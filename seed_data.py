from database_model import initialize_database, db
from database_manager import (
    create_hub, create_rim, create_spoke, create_nipple,
    get_all_hubs, get_all_rims, get_all_spokes, get_all_nipples
)
from logger import logger

def seed_components():
    """Populate database with sample components."""

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

    # Seed Spokes
    spokes_data = [
        {"material": "Steel", "gauge": 2.0, "max_tension": 120, "length": 282},
        {"material": "Steel", "gauge": 2.0, "max_tension": 120, "length": 286},
        {"material": "Stainless Steel", "gauge": 1.8, "max_tension": 130, "length": 282},  # 2.0/1.8/2.0 butted - use thinnest
        {"material": "Steel", "gauge": 1.8, "max_tension": 100, "length": 282},
        {"material": "Titanium", "gauge": 2.0, "max_tension": 140, "length": 282},
    ]

    for spoke_data in spokes_data:
        create_spoke(**spoke_data)

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
                f"{len(spokes_data)} spokes, {len(nipples_data)} nipples")

if __name__ == "__main__":
    initialize_database()
    db.connect()
    seed_components()
    db.close()
    print("Database seeded successfully")