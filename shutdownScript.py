import fme
import fmeobjects
import os
import csv
from arcgis.gis import GIS
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------
# 1. Configuration & Authentication
# ---------------------------------------------------------
# Authenticate with ArcGIS Online
AGO_URL = "https://ahs-vt.maps.arcgis.com/"
USERNAME = fme.macroValues['AGO_Username']
PASSWORD = fme.macroValues['AHS_ProductionPassword']

# Read directory where PDFs are saved to in the FME workspace
PDF_FOLDER = fme.macroValues['ShutdownScriptPDF_Folder']
AGO_FOLDER = "AHS_VDH_EnvHealth_HeatResilience"

# ---------------------------------------------------------
# 2. Upload Function
# ---------------------------------------------------------
def uploadToAGO(target_path, gis):
    logger = fmeobjects.FMELogFile()
    
    if not os.path.exists(target_path):
        logger.logMessageString(f"Shutdown Script Error: Path {target_path} does not exist.", fmeobjects.FME_ERROR)
        return
        
    filepaths = []
    
    if os.path.isfile(target_path) and target_path.endswith('.pdf'):
        filepaths.append(target_path)
    elif os.path.isdir(target_path):
        filepaths = [os.path.join(target_path, f) for f in os.listdir(target_path) if f.endswith('.pdf')]
    else:
        logger.logMessageString(f"Shutdown Script Error: Invalid path provided: {target_path}", fmeobjects.FME_ERROR)
        return
    
    if not filepaths:
        logger.logMessageString("Shutdown Script: No PDFs found to upload.", fmeobjects.FME_WARN)
        return

    logger.logMessageString("Shutdown Script: Fetching existing AGO items to optimize matching...", fmeobjects.FME_INFORM)
    
    existing_pdfs = gis.content.search(query='type:PDF', max_items=2000)
    pdf_map = {item.title: item for item in existing_pdfs}

    def process_pdf(filepath):
        if os.path.getsize(filepath) <= 200:
            return {"status": "skipped", "msg": f"Skipped (too small): {os.path.basename(filepath)}"}
            
        # ASSUMPTION: The PDF filename matches the TOWNNAMEMC attribute exactly.
        pdf_name = os.path.splitext(os.path.basename(filepath))[0]
        
        try:
            if pdf_name in pdf_map:
                item = pdf_map[pdf_name]
                item.update({}, filepath)
                msg_prefix = "PDF updated"
            else:
                item_props = {
                    "type": "PDF",
                    "title": pdf_name,
                    "description": "Heat resilience scorecards displaying data for specific towns."
                }
                item = gis.content.add(item_properties=item_props, data=filepath, folder=AGO_FOLDER)
                msg_prefix = "PDF added"
            
            # Share publicly to ensure the URL is accessible
            item.share(everyone=True)
            
            # Construct the direct URL to the PDF data using the item ID
            base_url = gis.url.rstrip('/')
            pdf_url = f"{base_url}/sharing/rest/content/items/{item.id}/data"
            
            return {
                "status": "success",
                "town": pdf_name, 
                "url": pdf_url, 
                "msg": f"{msg_prefix} & shared publicly: {pdf_name}"
            }
        except Exception as e:
            return {"status": "error", "msg": f"Error processing {pdf_name}: {str(e)}"}


    logger.logMessageString(f"Shutdown Script: Starting batch upload for {len(filepaths)} files...", fmeobjects.FME_INFORM)
    
    success_count = 0
    town_url_data = [] # List to store data for our final AGO Table
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_pdf, path) for path in filepaths]
        
        for future in as_completed(futures):
            result = future.result()
            logger.logMessageString(f"  - {result['msg']}", fmeobjects.FME_INFORM)
            
            if result["status"] == "success":
                success_count += 1
                # Append the town name and generated URL
                town_url_data.append({
                    "TOWNNAMEMC": result["town"], 
                    "PDF_URL": result["url"]
                })
                
    logger.logMessageString(f"Shutdown Script Complete: {success_count}/{len(filepaths)} PDFs successfully processed.", fmeobjects.FME_INFORM)

    # ---------------------------------------------------------
    # 3. Create Hosted Table in AGO
    # ---------------------------------------------------------
    if town_url_data:
        logger.logMessageString("Shutdown Script: Creating CSV and publishing to AGO...", fmeobjects.FME_INFORM)
        try:
            # Generate a local CSV first
            csv_filename = "Town_Heat_Resilience_URLs.csv"
            csv_path = os.path.join(os.path.dirname(target_path) if os.path.isfile(target_path) else target_path, csv_filename)
            
            with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["TOWNNAMEMC", "PDF_URL"])
                writer.writeheader()
                writer.writerows(town_url_data)
            
            # Check if this CSV already exists in AGO to overwrite it, avoiding duplicates
            existing_csvs = gis.content.search(f"title:{os.path.splitext(csv_filename)[0]} AND type:CSV")
            
            if existing_csvs:
                csv_item = existing_csvs[0]
                csv_item.update({}, csv_path)
                logger.logMessageString("Shutdown Script: Updated existing CSV mapping item.", fmeobjects.FME_INFORM)
                
                # NOTE: Overwriting an already published Hosted Feature Layer programmatically 
                # requires the arcgis.features.FeatureLayerCollection manager.
                # If this is a recurring run, you may want to implement `.manager.overwrite(csv_path)` here.
            else:
                csv_item_props = {
                    "title": os.path.splitext(csv_filename)[0],
                    "type": "CSV",
                    "description": "Mapping of Town Names to public Heat Resilience PDF URLs."
                }
                csv_item = gis.content.add(item_properties=csv_item_props, data=csv_path, folder=AGO_FOLDER)
                published_table = csv_item.publish()
                logger.logMessageString(f"Shutdown Script: Published new AGO Table. Item ID: {published_table.id}", fmeobjects.FME_INFORM)
                
        except Exception as e:
            logger.logMessageString(f"Shutdown Script Error publishing table: {str(e)}", fmeobjects.FME_ERROR)


# ---------------------------------------------------------
# 4. Execution
# ---------------------------------------------------------
try:
    logger = fmeobjects.FMELogFile()
    logger.logMessageString("Shutdown Script: Connecting to ArcGIS Online...", fmeobjects.FME_INFORM)
    
    gis_connection = GIS(AGO_URL, USERNAME, PASSWORD)
    uploadToAGO(PDF_FOLDER, gis_connection)
    
except Exception as e:
    logger.logMessageString(f"Shutdown Script Fatal Error: {str(e)}", fmeobjects.FME_ERROR)