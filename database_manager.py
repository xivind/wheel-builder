# All database CRUD operations are done with this method, other modules should never call db directly, always go through this module

from database_model import Hub, Rim, Spoke, Nipple, WheelBuild, TensionSession, TensionReading
from utils import generate_uuid
from logger import logger

# Hub operations

def create_hub(make, model, hub_type, old, left_flange_diameter, right_flange_diameter,
               left_flange_offset, right_flange_offset, spoke_hole_diameter):
    """Create a new hub in the database."""
    hub_id = generate_uuid()
    hub = Hub.create(
        id=hub_id,
        make=make,
        model=model,
        type=hub_type,
        old=old,
        left_flange_diameter=left_flange_diameter,
        right_flange_diameter=right_flange_diameter,
        left_flange_offset=left_flange_offset,
        right_flange_offset=right_flange_offset,
        spoke_hole_diameter=spoke_hole_diameter
    )
    logger.info(f"Created hub: {make} {model} (ID: {hub_id})")
    return hub

def get_all_hubs():
    """Get all hubs from database."""
    return list(Hub.select())

def get_hub_by_id(hub_id):
    """Get a specific hub by ID."""
    try:
        return Hub.get_by_id(hub_id)
    except Hub.DoesNotExist:
        return None

def update_hub(hub_id, **kwargs):
    """Update a hub's fields."""
    query = Hub.update(**kwargs).where(Hub.id == hub_id)
    rows_updated = query.execute()
    logger.info(f"Updated hub {hub_id}: {rows_updated} rows")
    return rows_updated > 0

def delete_hub(hub_id):
    """Delete a hub."""
    hub = Hub.get_by_id(hub_id)
    hub.delete_instance()
    logger.info(f"Deleted hub: {hub_id}")
    return True

def get_builds_using_hub(hub_id):
    """Get all wheel builds using this hub."""
    return list(WheelBuild.select().where(WheelBuild.hub_id == hub_id))

# Rim operations

def create_rim(make, model, rim_type, erd, osb, inner_width, outer_width, holes, material):
    """Create a new rim in the database."""
    rim_id = generate_uuid()
    rim = Rim.create(
        id=rim_id,
        make=make,
        model=model,
        type=rim_type,
        erd=erd,
        osb=osb,
        inner_width=inner_width,
        outer_width=outer_width,
        holes=holes,
        material=material
    )
    logger.info(f"Created rim: {make} {model} (ID: {rim_id})")
    return rim

def get_all_rims():
    """Get all rims from database."""
    return list(Rim.select())

def get_rim_by_id(rim_id):
    """Get a specific rim by ID."""
    try:
        return Rim.get_by_id(rim_id)
    except Rim.DoesNotExist:
        return None

def update_rim(rim_id, **kwargs):
    """Update a rim's fields."""
    query = Rim.update(**kwargs).where(Rim.id == rim_id)
    rows_updated = query.execute()
    logger.info(f"Updated rim {rim_id}: {rows_updated} rows")
    return rows_updated > 0

def delete_rim(rim_id):
    """Delete a rim."""
    rim = Rim.get_by_id(rim_id)
    rim.delete_instance()
    logger.info(f"Deleted rim: {rim_id}")
    return True

def get_builds_using_rim(rim_id):
    """Get all wheel builds using this rim."""
    return list(WheelBuild.select().where(WheelBuild.rim_id == rim_id))

# Spoke operations

def create_spoke(material, gauge, max_tension, length):
    """Create a new spoke type in the database."""
    spoke_id = generate_uuid()
    spoke = Spoke.create(
        id=spoke_id,
        material=material,
        gauge=gauge,
        max_tension=max_tension,
        length=length
    )
    logger.info(f"Created spoke: {material} {gauge} (ID: {spoke_id})")
    return spoke

def get_all_spokes():
    """Get all spokes from database."""
    return list(Spoke.select())

def get_spoke_by_id(spoke_id):
    """Get a specific spoke by ID."""
    try:
        return Spoke.get_by_id(spoke_id)
    except Spoke.DoesNotExist:
        return None

def update_spoke(spoke_id, **kwargs):
    """Update a spoke's fields."""
    query = Spoke.update(**kwargs).where(Spoke.id == spoke_id)
    rows_updated = query.execute()
    logger.info(f"Updated spoke {spoke_id}: {rows_updated} rows")
    return rows_updated > 0

def delete_spoke(spoke_id):
    """Delete a spoke."""
    spoke = Spoke.get_by_id(spoke_id)
    spoke.delete_instance()
    logger.info(f"Deleted spoke: {spoke_id}")
    return True

def get_builds_using_spoke(spoke_id):
    """Get all wheel builds using this spoke."""
    return list(WheelBuild.select().where(WheelBuild.spoke_id == spoke_id))

# Nipple operations

def create_nipple(material, diameter, length, color):
    """Create a new nipple type in the database."""
    nipple_id = generate_uuid()
    nipple = Nipple.create(
        id=nipple_id,
        material=material,
        diameter=diameter,
        length=length,
        color=color
    )
    logger.info(f"Created nipple: {material} {diameter}mm (ID: {nipple_id})")
    return nipple

def get_all_nipples():
    """Get all nipples from database."""
    return list(Nipple.select())

def get_nipple_by_id(nipple_id):
    """Get a specific nipple by ID."""
    try:
        return Nipple.get_by_id(nipple_id)
    except Nipple.DoesNotExist:
        return None

def update_nipple(nipple_id, **kwargs):
    """Update a nipple's fields."""
    query = Nipple.update(**kwargs).where(Nipple.id == nipple_id)
    rows_updated = query.execute()
    logger.info(f"Updated nipple {nipple_id}: {rows_updated} rows")
    return rows_updated > 0

def delete_nipple(nipple_id):
    """Delete a nipple."""
    nipple = Nipple.get_by_id(nipple_id)
    nipple.delete_instance()
    logger.info(f"Deleted nipple: {nipple_id}")
    return True

def get_builds_using_nipple(nipple_id):
    """Get all wheel builds using this nipple."""
    return list(WheelBuild.select().where(WheelBuild.nipple_id == nipple_id))