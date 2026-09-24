### test
import fme
from fme import BaseTransformer
import fmeobjects

class FeatureProcessor(BaseTransformer):
    def __init__(self):
        pass

    def has_support_for(self, support_type: int):
        return support_type == fmeobjects.FME_SUPPORT_FEATURE_TABLE_SHIM

    def input(self, feature: fmeobjects.FMEFeature):
        
        # Helper 1: Safely retrieve numerical values
        def get_val(attr_name):
            try:
                return float(feature.getAttribute(attr_name) or 0)
            except (ValueError, TypeError):
                return 0

        # Helper 2: Generate a single SVG block given a title and attribute prefix
        def build_svg_card(title, prefix):
            hst = get_val(f'{prefix}_historic')
            r1_245 = get_val(f'{prefix}_midCentury_ssp245')
            r1_585 = get_val(f'{prefix}_midCentury_ssp585')
            r2_245 = get_val(f'{prefix}_lateCentury_ssp245')
            r2_585 = get_val(f'{prefix}_lateCentury_ssp585')

            width = 300   
            # Increased padding slightly to ensure left-aligned historical labels don't clip
            pad = 32 
            max_val = max(hst, r1_245, r1_585, r2_245, r2_585) + 2
            
            if max_val == 0: 
                max_val = 1 

            scale = (width - (pad * 2)) / max_val

            x_hst = (hst * scale) + pad
            r1_x1 = (r1_245 * scale) + pad
            r1_x2 = (r1_585 * scale) + pad
            r2_x1 = (r2_245 * scale) + pad
            r2_x2 = (r2_585 * scale) + pad
            
            r1_max = max(r1_x1, r1_x2)
            r2_max = max(r2_x1, r2_x2)
            
            def fmt(val): 
                return f"{val:.1f}".rstrip('0').rstrip('.')

            # Staggered Y-coordinates implemented for text to prevent visual collisions.
            # Removed height="100%" to allow natural aspect-ratio scaling without clipping.
            return f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center;">
                <h4 style="margin: 0 0 15px 0; color: #005a84; font-size: 14px; text-align: center;">{title}</h4>
                <svg width="100%" viewBox="0 0 {width} 145" xmlns="http://www.w3.org/2000/svg" style="overflow: visible;">
                  <text x="0" y="15" font-family="sans-serif" font-size="11" font-weight="bold" fill="#64748b">Mid-Century</text>
                  
                  <line x1="{x_hst}" y1="45" x2="{r1_max}" y2="45" stroke="#f1f5f9" stroke-width="6" stroke-linecap="round" />
                  <line x1="{x_hst}" y1="45" x2="{r1_max}" y2="45" stroke="#cbd5e1" stroke-width="2" />
                  
                  <circle cx="{x_hst}" cy="45" r="5" fill="#94a3b8" /> 
                  <circle cx="{r1_x1}" cy="45" r="6" fill="#3b82f6" /> 
                  <circle cx="{r1_x2}" cy="45" r="6" fill="#ef4444" /> 
                  
                  <text x="{x_hst - 10}" y="48.5" font-family="sans-serif" font-size="10" text-anchor="end" fill="#64748b">{fmt(hst)}</text>
                  <text x="{r1_x1}" y="62" font-family="sans-serif" font-size="10" font-weight="bold" text-anchor="middle" fill="#3b82f6">{fmt(r1_245)}</text>
                  <text x="{r1_x2}" y="33" font-family="sans-serif" font-size="10" font-weight="bold" text-anchor="middle" fill="#ef4444">{fmt(r1_585)}</text>

                  <text x="0" y="88" font-family="sans-serif" font-size="11" font-weight="bold" fill="#64748b">Late-Century</text>
                  
                  <line x1="{x_hst}" y1="118" x2="{r2_max}" y2="118" stroke="#f1f5f9" stroke-width="6" stroke-linecap="round" />
                  <line x1="{x_hst}" y1="118" x2="{r2_max}" y2="118" stroke="#cbd5e1" stroke-width="2" />
                  
                  <circle cx="{x_hst}" cy="118" r="5" fill="#94a3b8" /> 
                  <circle cx="{r2_x1}" cy="118" r="6" fill="#3b82f6" /> 
                  <circle cx="{r2_x2}" cy="118" r="6" fill="#ef4444" /> 
                  
                  <text x="{x_hst - 10}" y="121.5" font-family="sans-serif" font-size="10" text-anchor="end" fill="#64748b">{fmt(hst)}</text>
                  <text x="{r2_x1}" y="135" font-family="sans-serif" font-size="10" font-weight="bold" text-anchor="middle" fill="#3b82f6">{fmt(r2_245)}</text>
                  <text x="{r2_x2}" y="106" font-family="sans-serif" font-size="10" font-weight="bold" text-anchor="middle" fill="#ef4444">{fmt(r2_585)}</text>
                </svg>
            </div>
            """

        # Define the 4 grids you want to generate (Title, Attribute Prefix)
        projections = [
            ("Days with High Above 90°F", "max90f"),
            ("Days with High Above 95°F", "max95f"),
            ("Days with High Above 100°F", "max100f"),
            ("Nights with Low Above 70°F", "min70f")
        ]

        # Loop through and generate the HTML for each chart
        all_charts_html = ""
        for title, prefix in projections:
            all_charts_html += build_svg_card(title, prefix)

        # Wrap all 4 charts in a responsive CSS grid container
        final_grid_html = f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; width: 100%;">
            {all_charts_html}
        </div>
        """

        # Set the combined grid string as the new attribute
        feature.setAttribute("DUMBBELL_CHART", final_grid_html)

        self.pyoutput(feature, output_tag="PYOUTPUT")

    def close(self):
        pass

    def process_group(self):
        pass

    def reject_feature(self, feature: fmeobjects.FMEFeature, code: str, message: str):
        feature.setAttribute("fme_rejection_code", code)
        feature.setAttribute("fme_rejection_message", message)
        self.pyoutput(feature, output_tag="<Rejected>")
