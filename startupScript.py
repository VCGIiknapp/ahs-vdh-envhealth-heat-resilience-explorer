import arcpy
import os
import fme


# Define your paths (consider using FME macro values here using fme.macroValues[])
APRX_PATH = fme.macroValues['StartupScript_AprxPath']
OUTPUT_FOLDER = fme.macroValues['StartupScript_OutputFolder']


def exportMapSeriesToPNG(APRX_PATH, OUTPUT_FOLDER):
    aprx = arcpy.mp.ArcGISProject(APRX_PATH)
    
    # Grab the layout containing the map series
    layout = aprx.listLayouts("TreeCanopy")[0]
    
    if layout.mapSeries is not None:
        ms = layout.mapSeries
        if ms.enabled:
            # Set up PNG export format
            # Pro tip: Keep resolution low (e.g., 96-150 DPI) to prevent massive Base64 strings
            pngExFormat = arcpy.mp.CreateExportFormat('PNG', os.path.join(OUTPUT_FOLDER, "TownMap.png"))
            pngExFormat.resolution = 300
            
            # Set up Map Series export options
            msExOpt = arcpy.mp.CreateExportOptions('MAPSERIES')
            msExOpt.setExportFileOptions('MULTIPLE_FILES_PAGE_NAME')
            msExOpt.setExportPages('ALL')
            
            # Execute export
            ms.export(pngExFormat, msExOpt)
            
exportMapSeriesToPNG(APRX_PATH, OUTPUT_FOLDER)