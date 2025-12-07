from database_model import initialize_database, db
from database_manager import (
    create_hub, create_rim, create_nipple,
    get_all_hubs, get_all_rims, get_all_spokes, get_all_nipples
)
import logging

logger = logging.getLogger(__name__)

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
         "left_flange_diameter": 92.6, "right_flange_diameter": 92.6,
         "left_flange_offset": 25.5, "right_flange_offset": 31.8, "spoke_hole_diameter": 2.9,
         "number_of_spokes": 36},
         {"make": "Shimano", "model": "Alfine SG-S700", "hub_type": "rear", "old": 135,
         "left_flange_diameter": 92.6, "right_flange_diameter": 92.6,
         "left_flange_offset": 25.5, "right_flange_offset": 31.8, "spoke_hole_diameter": 2.9,
         "number_of_spokes": 32},
         {"make": "Shimano", "model": "DH-UR708-3D", "hub_type": "front", "old": 100,
         "left_flange_diameter": 61, "right_flange_diameter": 61,
         "left_flange_offset": 29.5, "right_flange_offset": 22.5, "spoke_hole_diameter": 2.0,
         "number_of_spokes": 36},
         {"make": "Shimano", "model": "DH-UR708-3D", "hub_type": "front", "old": 100,
         "left_flange_diameter": 61, "right_flange_diameter": 61,
         "left_flange_offset": 29.5, "right_flange_offset": 22.5, "spoke_hole_diameter": 2.0,
         "number_of_spokes": 32},
         {"make": "Shimano", "model": "XT FH-M756A", "hub_type": "rear", "old": 135,
         "left_flange_diameter": 61, "right_flange_diameter": 61,
         "left_flange_offset": 34, "right_flange_offset": 23.4, "spoke_hole_diameter": 2.6,
         "number_of_spokes": 36},
         {"make": "Shimano", "model": "XT FH-M756A", "hub_type": "rear", "old": 135,
         "left_flange_diameter": 61, "right_flange_diameter": 61,
         "left_flange_offset": 34, "right_flange_offset": 23.4, "spoke_hole_diameter": 2.6,
         "number_of_spokes": 32},
         {"make": "Hope", "model": "Pro 4 Boost", "hub_type": "front", "old": 110,
         "left_flange_diameter": 57, "right_flange_diameter": 57,
         "left_flange_offset": 30, "right_flange_offset": 22, "spoke_hole_diameter": 2.6,
         "number_of_spokes": 32},
         {"make": "Shimano", "model": "Deore HB-M6000", "hub_type": "front", "old": 100,
         "left_flange_diameter": 44, "right_flange_diameter": 44,
         "left_flange_offset": 24.5, "right_flange_offset": 35.7, "spoke_hole_diameter": 2.6,
         "number_of_spokes": 36},
         {"make": "Shimano", "model": "Deore HB-M6000", "hub_type": "front", "old": 100,
         "left_flange_diameter": 44, "right_flange_diameter": 44,
         "left_flange_offset": 24.5, "right_flange_offset": 35.7, "spoke_hole_diameter": 2.6,
         "number_of_spokes": 32},
    ]

    for hub_data in hubs_data:
        create_hub(**hub_data)

    # Seed Rims
    rims_data = [
        {"make": "DT Swiss", "model": "535", "rim_type": "symmetric", "erd": 600,
         "osb": 0, "inner_width": 19, "outer_width": 24, "holes": 36, "material": "aluminum"},
         {"make": "DT Swiss", "model": "535", "rim_type": "symmetric", "erd": 600,
         "osb": 0, "inner_width": 19, "outer_width": 24, "holes": 32, "material": "aluminum"},
         {"make": "Mavic", "model": "A719", "rim_type": "symmetric", "erd": 604,
         "osb": 0, "inner_width": 19, "outer_width": 24.5, "holes": 36, "material": "aluminum"},
         {"make": "Mavic", "model": "A719", "rim_type": "symmetric", "erd": 604,
         "osb": 0, "inner_width": 19, "outer_width": 24.5, "holes": 32, "material": "aluminum"},
         {"make": "Ryde", "model": "Andra 30", "rim_type": "symmetric", "erd": 605.4,
         "osb": 0, "inner_width": 19, "outer_width": 25, "holes": 36, "material": "aluminum"},
         {"make": "Mavic", "model": "XM 1030", "rim_type": "symmetric", "erd": 598,
         "osb": 0, "inner_width": 30, "outer_width": 34.5, "holes": 32, "material": "aluminum"},
    ]

    for rim_data in rims_data:
        create_rim(**rim_data)

    # Seed Spokes - using spoke type system
    # Get some spoke types to use for seeding
    from database_manager import get_all_spoke_types
    from database_model import Spoke
    import uuid

    spoke_types = get_all_spoke_types()
    if not spoke_types:
        logger.warning("No spoke types found - run seed_spoke_types.py first")
        return

    # Find specific spoke types by name
    steel_round_2mm = next((st for st in spoke_types if st.name == "Steel Round 2.0mm"), None)
    if not steel_round_2mm:
        logger.warning("Steel Round 2.0mm spoke type not found - skipping sample spokes with this type")

    steel_round_18mm = next((st for st in spoke_types if st.name == "Steel Round 1.8mm"), None)
    if not steel_round_18mm:
        logger.warning("Steel Round 1.8mm spoke type not found - skipping sample spokes with this type")

    titanium_round_2mm = next((st for st in spoke_types if st.name == "Titanium Round 2.0mm"), None)
    if not titanium_round_2mm:
        logger.warning("Titanium Round 2.0mm spoke type not found - skipping sample spokes with this type")

    # Create sample spokes using spoke types
    spokes_data = [
        {"spoke_type_id": steel_round_2mm.id, "length": 286} if steel_round_2mm else None,
        {"spoke_type_id": steel_round_2mm.id, "length": 285} if steel_round_2mm else None,
        {"spoke_type_id": steel_round_18mm.id, "length": 286} if steel_round_18mm else None,
        {"spoke_type_id": steel_round_18mm.id, "length": 285} if steel_round_18mm else None,
    ]

    # Filter out None entries and create spokes
    total_possible_spokes = len(spokes_data)
    spokes_to_create = [s for s in spokes_data if s]
    for spoke_data in spokes_to_create:
        Spoke.create(id=str(uuid.uuid4()), **spoke_data)

    logger.info(f"Created {len(spokes_to_create)} of {total_possible_spokes} sample spokes")

    # Seed Nipples
    nipples_data = [
        {"material": "Brass", "diameter": 2.0, "length": 12, "color": "silver"},
        {"material": "Brass", "diameter": 2.0, "length": 14, "color": "silver"},
        {"material": "Aluminum", "diameter": 2.0, "length": 12, "color": "anodized black"},
        {"material": "Aluminum", "diameter": 2.0, "length": 12, "color": "anodized red"},
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