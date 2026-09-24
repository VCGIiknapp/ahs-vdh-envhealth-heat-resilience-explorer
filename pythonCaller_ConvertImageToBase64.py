import fme
import fmeobjects
import base64

class FeatureProcessor(object):
    def __init__(self):
        pass

    def input(self, feature):
        # Get the file path from the Directory reader
        filepath = feature.getAttribute('path_windows')
        
        if filepath and filepath.endswith('.png'):
            try:
                with open(filepath, "rb") as image_file:
                    # Read bytes, encode to base64, and decode to utf-8 string
                    b64_string = base64.b64encode(image_file.read()).decode('utf-8')
                    # Set the new attribute for the HTML template
                    feature.setAttribute('MAP_BASE64_STRING', b64_string)
            except Exception as e:
                fmeobjects.FMELogFile().logMessageString(f"Error encoding {filepath}: {str(e)}", fmeobjects.FME_ERROR)
        
        # Send the feature out of the PythonCaller
        self.pyoutput(feature)

    def close(self):
        pass