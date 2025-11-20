from database_model import initialize_database, db
from database_manager import (
    create_hub, create_rim, create_spoke, create_nipple,
    get_all_hubs, get_all_rims, get_all_spokes, get_all_nipples
)
from logger import logger

# ==============================================================================
# PARK TOOL TM-1 CONVERSION TABLES
# Complete official conversion data for all spoke types
# Format: {tm_reading: kgf_tension}
# ==============================================================================

TM1_CONVERSION_TABLE = {
    # ==============================================================================
    # SECTION 1: STEEL ROUND SPOKES
    # ==============================================================================
    "Steel Round 2.6mm": {
        20: 53, 21: 58, 22: 63, 23: 70, 24: 77, 25: 85, 26: 94, 27: 105,
        28: 117, 29: 131, 30: 148, 31: 166
    },
    "Steel Round 2.55mm": {
        15: 54, 16: 59, 17: 66, 18: 73, 19: 82, 20: 92, 21: 104, 22: 117,
        23: 133, 24: 151, 25: 172
    },
    "Steel Round 2.3mm": {
        15: 54, 16: 59, 17: 66, 18: 73, 19: 82, 20: 92, 21: 104, 22: 117,
        23: 133, 24: 151, 25: 172
    },
    "Steel Round 2.0mm": {
        16: 53, 17: 58, 18: 63, 19: 70, 20: 77, 21: 85, 22: 94, 23: 105,
        24: 117, 25: 131, 26: 148, 27: 167
    },
    "Steel Round 1.8mm": {
        19: 53, 20: 58, 21: 64, 22: 71, 23: 78, 24: 86, 25: 95, 26: 105,
        27: 115, 28: 126, 29: 138, 30: 151, 31: 165
    },
    "Steel Round 1.7mm": {
        21: 51, 22: 56, 23: 61, 24: 67, 25: 73, 26: 81, 27: 89, 28: 99,
        29: 110, 30: 122, 31: 137, 32: 154, 33: 174
    },
    "Steel Round 1.6mm": {
        24: 54, 25: 58, 26: 64, 27: 70, 28: 76, 29: 84, 30: 93, 31: 103,
        32: 114, 33: 128, 34: 143, 35: 160
    },
    "Steel Round 1.5mm": {
        26: 52, 27: 56, 28: 61, 29: 66, 30: 73, 31: 80, 32: 88, 33: 97,
        34: 107, 35: 119, 36: 133, 37: 148, 38: 166
    },
    "Steel Round 1.4mm": {
        28: 52, 29: 56, 30: 61, 31: 66, 32: 72, 33: 79, 34: 88, 35: 97,
        36: 107, 37: 119, 38: 133, 39: 148, 40: 166, 41: 172
    },

    # ==============================================================================
    # SECTION 2: STEEL BLADE SPOKES
    # ==============================================================================
    "Steel Blade 0.8 x 2.0mm": {
        16: 118, 17: 131, 18: 146, 19: 163
    },
    "Steel Blade 0.9 x 2.2mm": {
        5: 52, 6: 56, 7: 60, 8: 65, 9: 71, 10: 78, 11: 85, 12: 93,
        13: 103, 14: 114, 15: 126, 16: 141, 17: 157, 18: 176
    },
    "Steel Blade 0.9 x 3.6mm": {
        10: 58, 11: 68, 12: 81, 13: 98, 14: 108, 15: 119, 16: 133, 17: 148, 18: 165
    },
    "Steel Blade 1.0 x 2.0-2.2mm": {
        10: 53, 11: 57, 12: 62, 13: 68, 14: 74, 15: 81, 16: 89, 17: 98,
        18: 108, 19: 119, 20: 131, 21: 145, 22: 160
    },
    "Steel Blade 1.0 x 2.5-2.7mm": {
        9: 51, 10: 56, 11: 61, 12: 66, 13: 71, 14: 78, 15: 85, 16: 92,
        17: 103, 18: 115, 19: 130, 20: 146, 21: 165
    },
    "Steel Blade 1.0 x 3.2mm": {
        6: 53, 7: 57, 8: 62, 9: 67, 10: 73, 11: 80, 12: 88, 13: 97,
        14: 107, 15: 119, 16: 132, 17: 148, 18: 165
    },
    "Steel Blade 1.1 x 1.9-2.0mm": {
        8: 54, 9: 59, 10: 65, 11: 71, 12: 78, 13: 86, 14: 94, 15: 104,
        16: 115, 17: 128, 18: 143, 19: 160, 20: 180
    },
    "Steel Blade 1.1 x 3.0-3.6mm": {
        8: 51, 9: 55, 10: 59, 11: 65, 12: 71, 13: 77, 14: 85, 15: 94,
        16: 103, 17: 115, 18: 128, 19: 142, 20: 160, 21: 179
    },
    "Steel Blade 1.2 x 2.6mm": {
        8: 51, 9: 55, 10: 59, 11: 65, 12: 71, 13: 77, 14: 85, 15: 94,
        16: 104, 17: 115, 18: 128, 19: 142, 20: 160, 21: 179
    },
    "Steel Blade 1.2 x 1.9mm": {
        8: 53, 9: 58, 10: 63, 11: 68, 12: 74, 13: 82, 14: 90, 15: 99,
        16: 110, 17: 122, 18: 136, 19: 152, 20: 170
    },
    "Steel Blade 1.3 x 2.1mm": {
        8: 51, 9: 55, 10: 60, 11: 66, 12: 72, 13: 79, 14: 86, 15: 95,
        16: 106, 17: 117, 18: 131, 19: 146, 20: 164
    },
    "Steel Blade 1.3 x 2.2-2.5mm": {
        10: 53, 11: 57, 12: 62, 13: 68, 14: 74, 15: 82, 16: 90, 17: 100,
        18: 111, 19: 124, 20: 138, 21: 155, 22: 175
    },
    "Steel Blade 1.3 x 2.7mm": {
        11: 51, 12: 56, 13: 61, 14: 66, 15: 73, 16: 80, 17: 89, 18: 98,
        19: 109, 20: 122, 21: 137, 22: 153, 23: 173
    },
    "Steel Blade 1.4 x 2.3mm": {
        13: 53, 14: 58, 15: 63, 16: 69, 17: 76, 18: 84, 19: 93, 20: 103,
        21: 115, 22: 129, 23: 144, 24: 163
    },
    "Steel Blade 1.4 x 2.6mm": {
        12: 53, 13: 58, 14: 63, 15: 69, 16: 76, 17: 83, 18: 92, 19: 102,
        20: 114, 21: 127, 22: 142, 23: 160
    },
    "Steel Blade 1.4 x 2.9mm": {
        11: 53, 12: 58, 13: 63, 14: 69, 15: 76, 16: 83, 17: 92, 18: 102,
        19: 114, 20: 127, 21: 142, 22: 151, 23: 170
    },
    "Steel Blade 1.5 x 2.4-2.6mm": {
        14: 54, 15: 59, 16: 65, 17: 71, 18: 78, 19: 86, 20: 96, 21: 107,
        22: 120, 23: 134, 24: 151, 25: 170, 26: 176
    },
    "Steel Blade 1.7 x 2.3mm": {
        14: 54, 15: 59, 16: 65, 17: 72, 18: 79, 19: 88, 20: 98, 21: 109,
        22: 123, 23: 138, 24: 156, 25: 176
    },

    # ==============================================================================
    # SECTION 3: ALUMINUM SPOKES
    # ==============================================================================
    "Aluminum Round 3.3mm": {
        13: 51, 14: 58, 15: 65, 16: 74, 17: 83, 18: 95, 19: 108, 20: 123,
        21: 141, 22: 162
    },
    "Aluminum Round 2.8mm": {
        13: 50, 14: 57, 15: 64, 16: 73, 17: 82, 18: 94, 19: 107, 20: 122,
        21: 140, 22: 160, 23: 175
    },
    "Aluminum Round 2.54mm": {
        13: 55, 14: 61, 15: 68, 16: 77, 17: 86, 18: 96, 19: 108, 20: 121,
        21: 137, 22: 154, 23: 175
    },
    "Aluminum Round 2.28mm": {
        12: 52, 13: 58, 14: 65, 15: 72, 16: 81, 17: 91, 18: 103, 19: 116,
        20: 130, 21: 147, 22: 166
    },
    "Aluminum Blade 1.5 x 3.9mm": {
        6: 52, 7: 58, 8: 65, 9: 72, 10: 81, 11: 91, 12: 103, 13: 116,
        14: 130, 15: 147, 16: 166
    },
    "Aluminum Blade 1.8 x 5.3mm": {
        13: 51, 14: 56, 15: 61, 16: 68, 17: 75, 18: 83, 19: 92, 20: 103,
        21: 115, 22: 130, 23: 146, 24: 165
    },
    "Aluminum Blade 2.1 x 4.3mm": {
        17: 56, 18: 63, 19: 71, 20: 81, 21: 92, 22: 104, 23: 118, 24: 134,
        25: 153, 26: 174
    },

    # ==============================================================================
    # SECTION 4: TITANIUM & SPECIALTY
    # ==============================================================================
    "TL Round 2.0mm": {
        12: 53, 13: 57, 14: 62, 15: 67, 16: 72, 17: 79, 18: 86, 19: 95,
        20: 105, 21: 116, 22: 129, 23: 143, 24: 160
    },
    "Titanium Blade 1.4 x 2.6mm": {
        13: 53, 14: 57, 15: 62, 16: 67, 17: 72, 18: 79, 19: 86, 20: 95,
        21: 105, 22: 116, 23: 129, 24: 143, 25: 160
    },
    "Mavic R2R Carbon Blade": {
        5: 59, 6: 63, 7: 67, 8: 72, 9: 77, 10: 82, 11: 89, 12: 96, 13: 105,
        14: 119, 15: 125, 16: 137, 17: 151
    },
    "SPO Spinergy Round 2.6mm": {
        10: 51, 11: 54, 12: 57, 13: 61, 14: 64, 15: 68, 16: 73, 17: 77,
        18: 83, 19: 88, 20: 95, 21: 102, 22: 109, 23: 118, 24: 127, 25: 137,
        26: 148, 27: 160, 28: 174
    }
}


def create_spoke_templates():
    """Create 38 Park Tool spoke type templates with conversion data.

    These templates are read-only reference data that users select from when
    creating actual spokes for their wheel builds.
    """

    templates = []

    # Helper to extract material, shape, and dimensions from Park Tool designation
    def parse_spoke_type(designation):
        """Parse Park Tool designation into structured data."""
        parts = designation.split()
        material_raw = parts[0]  # "Steel", "Aluminum", "Titanium", etc.
        shape = parts[1] if len(parts) > 1 else "Round"  # "Round", "Blade"

        # Extract dimensions from the designation
        if "Round" in designation:
            # Extract diameter (e.g., "2.0mm" from "Steel Round 2.0mm")
            dim_str = designation.split()[-1].replace("mm", "")
            gauge = float(dim_str)
            width = None
            thickness = None
        elif "Blade" in designation:
            # Extract width x thickness (e.g., "1.4 x 2.6mm" from "Steel Blade 1.4 x 2.6mm")
            dim_part = designation.split("Blade")[1].strip().replace("mm", "")
            if "x" in dim_part:
                dims = dim_part.split("x")
                thickness = float(dims[0].strip().split("-")[0])  # Handle ranges like "2.0-2.2"
                width = float(dims[1].strip().split("-")[0])
                gauge = thickness  # Use thickness as gauge for blade spokes
            else:
                gauge = 2.0
                width = None
                thickness = None
        else:
            gauge = 2.0
            width = None
            thickness = None

        # Normalize material names
        material_map = {
            "Steel": "steel",
            "Aluminum": "aluminum",
            "Titanium": "titanium",
            "TL": "titanium",  # TL = Titanium alloy
            "Mavic": "carbon",  # Mavic R2R is carbon
            "SPO": "steel"  # Spinergy specialty steel
        }
        material = material_map.get(material_raw, "steel")

        return {
            "material": material,
            "shape": shape.lower(),
            "gauge": gauge,
            "width": width,
            "thickness": thickness
        }

    # Build template data for each spoke type
    for designation, conversion_table in TM1_CONVERSION_TABLE.items():
        parsed = parse_spoke_type(designation)

        # Calculate min/max tension from conversion table
        kgf_values = list(conversion_table.values())
        min_tension = min(kgf_values)
        max_tension = max(kgf_values)

        template = {
            "name": designation,  # Use Park Tool designation as name
            "is_template": True,
            "template_id": None,  # Templates don't have a parent template
            "park_tool_designation": designation,
            "material": parsed["material"],
            "shape": parsed["shape"],
            "gauge": parsed["gauge"],
            "width": parsed["width"],
            "thickness": parsed["thickness"],
            "min_tension": min_tension,
            "max_tension": max_tension,
            "conversion_table": conversion_table,
            "length": None  # Templates don't have a specific length
        }

        templates.append(template)

    return templates


def seed_components():
    """Populate database with sample components and spoke templates."""

    # Check if already seeded
    if len(get_all_hubs()) > 0:
        logger.info("Database already seeded, skipping")
        return

    logger.info("Seeding component library...")

    # Seed Hubs
    hubs_data = [
        {"make": "Shimano", "model": "Alfine SG-S700", "hub_type": "rear", "old": 135,
         "left_flange_diameter": 93, "right_flange_diameter": 93,
         "left_flange_offset": 38, "right_flange_offset": 43.5, "spoke_hole_diameter": 2.9},
        {"make": "DT Swiss", "model": "350", "hub_type": "front", "old": 100,
         "left_flange_diameter": 58, "right_flange_diameter": 58,
         "left_flange_offset": 32, "right_flange_offset": 32, "spoke_hole_diameter": 2.6},
        {"make": "Hope", "model": "Pro 4", "hub_type": "front", "old": 100,
         "left_flange_diameter": 56, "right_flange_diameter": 56,
         "left_flange_offset": 30, "right_flange_offset": 30, "spoke_hole_diameter": 2.5},
        {"make": "Shimano", "model": "Ultegra", "hub_type": "rear", "old": 130,
         "left_flange_diameter": 46, "right_flange_diameter": 58,
         "left_flange_offset": 35, "right_flange_offset": 40.5, "spoke_hole_diameter": 2.5},
        {"make": "Phil Wood", "model": "Track", "hub_type": "rear", "old": 120,
         "left_flange_diameter": 52, "right_flange_diameter": 52,
         "left_flange_offset": 28, "right_flange_offset": 28, "spoke_hole_diameter": 2.6},
    ]

    for hub_data in hubs_data:
        create_hub(**hub_data)

    # Seed Rims
    rims_data = [
        {"make": "Ryde", "model": "Andra 30", "rim_type": "symmetric", "erd": 605.4,
         "osb": 0, "inner_width": 20, "outer_width": 30, "holes": 36, "material": "aluminum"},
        {"make": "Mavic", "model": "Open Pro", "rim_type": "symmetric", "erd": 610,
         "osb": 0, "inner_width": 17, "outer_width": 23, "holes": 32, "material": "aluminum"},
        {"make": "DT Swiss", "model": "XM 481", "rim_type": "symmetric", "erd": 597,
         "osb": 0, "inner_width": 25, "outer_width": 30, "holes": 32, "material": "aluminum"},
        {"make": "Stan's", "model": "Grail", "rim_type": "symmetric", "erd": 589,
         "osb": 0, "inner_width": 21, "outer_width": 30, "holes": 28, "material": "aluminum"},
        {"make": "H+Son", "model": "Archetype", "rim_type": "symmetric", "erd": 602,
         "osb": 0, "inner_width": 17, "outer_width": 23, "holes": 32, "material": "aluminum"},
    ]

    for rim_data in rims_data:
        create_rim(**rim_data)

    # Seed Spoke Templates (38 Park Tool spoke types)
    spoke_templates = create_spoke_templates()
    for template_data in spoke_templates:
        create_spoke(**template_data)

    # Seed Nipples
    nipples_data = [
        {"material": "Brass", "diameter": 2.0, "length": 12, "color": "silver"},
        {"material": "Aluminum", "diameter": 2.0, "length": 12, "color": "black"},
        {"material": "Brass", "diameter": 2.0, "length": 14, "color": "silver"},
        {"material": "Aluminum", "diameter": 2.0, "length": 12, "color": "red"},
    ]

    for nipple_data in nipples_data:
        create_nipple(**nipple_data)

    logger.info(f"Seeded: {len(hubs_data)} hubs, {len(rims_data)} rims, "
                f"{len(spoke_templates)} spoke templates, {len(nipples_data)} nipples")

if __name__ == "__main__":
    initialize_database()
    db.connect()
    seed_components()
    db.close()
    print("Database seeded successfully")
