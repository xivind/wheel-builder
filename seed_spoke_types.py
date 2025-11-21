import json
import uuid
from database_model import db, SpokeType, ConversionPoint
from logger import logger

def parse_spoke_type_metadata(name):
    """Parse material, shape, and dimensions from spoke type name.

    Args:
        name: Spoke type name (e.g., "Steel Round 2.0mm")

    Returns:
        dict: {'material': str, 'shape': str, 'dimensions': str}
    """
    # Determine material
    if name.startswith("Steel"):
        material = "Steel"
    elif name.startswith("Aluminum"):
        material = "Aluminum"
    elif name.startswith("Titanium"):
        material = "Titanium"
    elif "carbon" in name.lower():
        material = "Carbon"
    else:
        # Default for special cases like "Mavic R2R", "SPO Spinnergy"
        if "Mavic" in name and "carbon" in name.lower():
            material = "Carbon"
        elif "SPO" in name or "Spinnergy" in name:
            material = "Steel"  # Default assumption
        else:
            material = "Unknown"

    # Determine shape
    if "Round" in name:
        shape = "Round"
    elif "Blade" in name or "blade" in name:
        shape = "Blade"
    else:
        shape = "Unknown"

    # Extract dimensions (everything after material and shape)
    # Examples: "2.0mm", "1.4 x 2.6mm", "0.8 x 2.0mm"
    parts = name.split()
    dimensions = " ".join(parts[-1:])  # Last part usually contains dimensions
    if not dimensions or len(dimensions) > 20:
        # Try to find pattern like "2.0mm" or "1.4 x 2.6mm"
        import re
        match = re.search(r'(\d+\.?\d*\s*x?\s*\d*\.?\d*mm)', name)
        if match:
            dimensions = match.group(1)
        else:
            dimensions = name  # Fallback to full name

    return {
        'material': material,
        'shape': shape,
        'dimensions': dimensions
    }

def seed_spoke_types():
    """Seed SpokeType and ConversionPoint tables from conversion_table.txt.

    Returns:
        int: Number of spoke types seeded
    """
    # Check if already seeded
    if SpokeType.select().count() > 0:
        logger.info("SpokeType table already populated, skipping seed")
        return 0

    logger.info("Seeding spoke types from conversion_table.txt")

    # Load conversion table
    with open('conversion_table.txt', 'r') as f:
        conversion_data = json.load(f)

    spoke_types_created = 0
    conversion_points_created = 0

    db.connect(reuse_if_open=True)

    for spoke_name, conversions in conversion_data.items():
        # Parse metadata from name
        metadata = parse_spoke_type_metadata(spoke_name)

        # Get min/max TM readings and kgf values
        tm_readings = [int(tm) for tm in conversions.keys()]
        kgf_values = list(conversions.values())

        min_tm = min(tm_readings)
        max_tm = max(tm_readings)
        min_kgf = conversions[str(min_tm)]
        max_kgf = conversions[str(max_tm)]

        # Create SpokeType record
        spoke_type_id = str(uuid.uuid4())
        SpokeType.create(
            id=spoke_type_id,
            name=spoke_name,
            material=metadata['material'],
            shape=metadata['shape'],
            dimensions=metadata['dimensions'],
            min_tm_reading=min_tm,
            max_tm_reading=max_tm,
            min_tension_kgf=min_kgf,
            max_tension_kgf=max_kgf
        )
        spoke_types_created += 1

        # Create ConversionPoint records
        for tm_str, kgf in conversions.items():
            ConversionPoint.create(
                spoke_type_id=spoke_type_id,
                tm_reading=int(tm_str),
                kgf=kgf
            )
            conversion_points_created += 1

        logger.info(f"Seeded spoke type: {spoke_name} ({len(conversions)} conversion points)")

    db.close()

    logger.info(f"Seeding complete: {spoke_types_created} spoke types, {conversion_points_created} conversion points")
    return spoke_types_created

if __name__ == "__main__":
    # For testing
    from database_model import initialize_database
    initialize_database()
    count = seed_spoke_types()
    print(f"Seeded {count} spoke types")
