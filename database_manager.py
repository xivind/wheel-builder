# All database CRUD operations are done with this method, other modules should never call db directly, always go through this module

from datetime import datetime
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

def get_hubs_by_ids(hub_ids):
    """Get multiple hubs by their IDs (batch fetch)."""
    if not hub_ids:
        return []
    return list(Hub.select().where(Hub.id.in_(hub_ids)))

def update_hub(hub_id, **kwargs):
    """Update a hub's fields."""
    query = Hub.update(**kwargs).where(Hub.id == hub_id)
    rows_updated = query.execute()
    logger.info(f"Updated hub {hub_id}: {rows_updated} rows")
    return rows_updated > 0

def delete_hub(hub_id):
    """Delete a hub."""
    try:
        hub = Hub.get_by_id(hub_id)
        hub.delete_instance()
        logger.info(f"Deleted hub: {hub_id}")
        return True
    except Hub.DoesNotExist:
        logger.warning(f"Cannot delete hub {hub_id}: does not exist")
        return False

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

def get_rims_by_ids(rim_ids):
    """Get multiple rims by their IDs (batch fetch)."""
    if not rim_ids:
        return []
    return list(Rim.select().where(Rim.id.in_(rim_ids)))

def update_rim(rim_id, **kwargs):
    """Update a rim's fields."""
    query = Rim.update(**kwargs).where(Rim.id == rim_id)
    rows_updated = query.execute()
    logger.info(f"Updated rim {rim_id}: {rows_updated} rows")
    return rows_updated > 0

def delete_rim(rim_id):
    """Delete a rim."""
    try:
        rim = Rim.get_by_id(rim_id)
        rim.delete_instance()
        logger.info(f"Deleted rim: {rim_id}")
        return True
    except Rim.DoesNotExist:
        logger.warning(f"Cannot delete rim {rim_id}: does not exist")
        return False

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
    """Get all spokes with their spoke types.

    Returns:
        list: All Spoke instances with spoke_type loaded
    """
    from database_model import SpokeType

    spokes = list(Spoke.select())

    # Eager load spoke types
    for spoke in spokes:
        try:
            spoke.spoke_type = SpokeType.get_by_id(spoke.spoke_type_id)
        except SpokeType.DoesNotExist:
            spoke.spoke_type = None
            logger.warning(f"Spoke {spoke.id} has invalid spoke_type_id")

    return spokes

def get_spoke_by_id(spoke_id):
    """Get spoke by ID with spoke type.

    Args:
        spoke_id: Spoke UUID

    Returns:
        Spoke instance or None
    """
    from database_model import SpokeType
    try:
        spoke = Spoke.get_by_id(spoke_id)
        # Eager load spoke type
        spoke.spoke_type = SpokeType.get_by_id(spoke.spoke_type_id)
        return spoke
    except (Spoke.DoesNotExist, SpokeType.DoesNotExist):
        return None

def update_spoke(spoke_id, **kwargs):
    """Update a spoke's fields."""
    query = Spoke.update(**kwargs).where(Spoke.id == spoke_id)
    rows_updated = query.execute()
    logger.info(f"Updated spoke {spoke_id}: {rows_updated} rows")
    return rows_updated > 0

def delete_spoke(spoke_id):
    """Delete a spoke."""
    try:
        spoke = Spoke.get_by_id(spoke_id)
        spoke.delete_instance()
        logger.info(f"Deleted spoke: {spoke_id}")
        return True
    except Spoke.DoesNotExist:
        logger.warning(f"Cannot delete spoke {spoke_id}: does not exist")
        return False

def get_builds_using_spoke(spoke_id):
    """Get all wheel builds using this spoke (left or right)."""
    return list(WheelBuild.select().where(
        (WheelBuild.spoke_left_id == spoke_id) | (WheelBuild.spoke_right_id == spoke_id)
    ))

def get_spoke_type_by_id(spoke_type_id):
    """Get spoke type by ID.

    Args:
        spoke_type_id: SpokeType UUID

    Returns:
        SpokeType instance or None
    """
    from database_model import SpokeType
    try:
        return SpokeType.get_by_id(spoke_type_id)
    except SpokeType.DoesNotExist:
        return None

def get_all_spoke_types():
    """Get all spoke types for selection.

    Returns:
        list: All SpokeType instances, ordered by name
    """
    from database_model import SpokeType
    return list(SpokeType.select().order_by(SpokeType.name))

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
    try:
        nipple = Nipple.get_by_id(nipple_id)
        nipple.delete_instance()
        logger.info(f"Deleted nipple: {nipple_id}")
        return True
    except Nipple.DoesNotExist:
        logger.warning(f"Cannot delete nipple {nipple_id}: does not exist")
        return False

def get_builds_using_nipple(nipple_id):
    """Get all wheel builds using this nipple."""
    return list(WheelBuild.select().where(WheelBuild.nipple_id == nipple_id))

# Wheel Build operations

def create_wheel_build(name, status='draft', hub_id=None, rim_id=None, spoke_left_id=None, spoke_right_id=None,
                       nipple_id=None, lacing_pattern=None, spoke_count=None,
                       actual_spoke_length_left=None, actual_spoke_length_right=None, comments=None):
    """Create a new wheel build."""
    build_id = generate_uuid()
    build = WheelBuild.create(
        id=build_id,
        name=name,
        status=status,
        hub_id=hub_id,
        rim_id=rim_id,
        spoke_left_id=spoke_left_id,
        spoke_right_id=spoke_right_id,
        nipple_id=nipple_id,
        lacing_pattern=lacing_pattern,
        spoke_count=spoke_count,
        actual_spoke_length_left=actual_spoke_length_left,
        actual_spoke_length_right=actual_spoke_length_right,
        comments=comments
    )
    logger.info(f"Created wheel build: {name} (ID: {build_id})")
    return build

def get_all_wheel_builds():
    """Get all wheel builds."""
    return list(WheelBuild.select().order_by(WheelBuild.updated_at.desc()))

def get_wheel_build_by_id(build_id):
    """Get a specific wheel build by ID."""
    try:
        return WheelBuild.get_by_id(build_id)
    except WheelBuild.DoesNotExist:
        return None

def update_wheel_build(build_id, **kwargs):
    """Update a wheel build's fields."""
    kwargs['updated_at'] = datetime.now()
    query = WheelBuild.update(**kwargs).where(WheelBuild.id == build_id)
    rows_updated = query.execute()
    logger.info(f"Updated wheel build {build_id}: {rows_updated} rows")
    return rows_updated > 0

def delete_wheel_build(build_id):
    """Delete a wheel build and associated tension sessions/readings."""
    # Delete tension readings first
    sessions = list(TensionSession.select().where(TensionSession.wheel_build_id == build_id))
    for session in sessions:
        TensionReading.delete().where(TensionReading.tension_session_id == session.id).execute()

    # Delete tension sessions
    TensionSession.delete().where(TensionSession.wheel_build_id == build_id).execute()

    # Delete wheel build
    build = WheelBuild.get_by_id(build_id)
    build.delete_instance()
    logger.info(f"Deleted wheel build: {build_id}")
    return True

# Tension Session operations

def create_tension_session(wheel_build_id, session_name, session_date, notes=None):
    """Create a new tension session for a wheel build."""
    session_id = generate_uuid()
    session = TensionSession.create(
        id=session_id,
        wheel_build_id=wheel_build_id,
        session_name=session_name,
        session_date=session_date,
        notes=notes
    )
    logger.info(f"Created tension session: {session_name} for build {wheel_build_id}")
    return session

def get_sessions_by_build(wheel_build_id):
    """Get all tension sessions for a wheel build."""
    return list(TensionSession.select()
                .where(TensionSession.wheel_build_id == wheel_build_id)
                .order_by(TensionSession.session_date.desc()))

def get_tension_session_by_id(session_id):
    """Get a specific tension session by ID."""
    try:
        return TensionSession.get_by_id(session_id)
    except TensionSession.DoesNotExist:
        return None

# Tension Reading operations

def create_tension_reading(tension_session_id, spoke_number, side, tm_reading,
                          estimated_tension_kgf, range_status, average_deviation_status):
    """Create a tension reading for a spoke."""
    reading_id = generate_uuid()
    reading = TensionReading.create(
        id=reading_id,
        tension_session_id=tension_session_id,
        spoke_number=spoke_number,
        side=side,
        tm_reading=tm_reading,
        estimated_tension_kgf=estimated_tension_kgf,
        range_status=range_status,
        average_deviation_status=average_deviation_status
    )
    return reading

def get_readings_by_session(tension_session_id):
    """Get all tension readings for a session."""
    return list(TensionReading.select()
                .where(TensionReading.tension_session_id == tension_session_id)
                .order_by(TensionReading.spoke_number))

def upsert_tension_reading(tension_session_id, spoke_number, side, tm_reading,
                          estimated_tension_kgf, range_status, average_deviation_status):
    """Create or update a single tension reading for a spoke.

    Args:
        tension_session_id: Session ID
        spoke_number: Spoke number (1-based)
        side: 'left' or 'right'
        tm_reading: Park Tool TM-1 reading
        estimated_tension_kgf: Calculated tension in kgf
        range_status: 'in_range', 'over', or 'under'
        average_deviation_status: 'in_range', 'over', or 'under'

    Returns:
        TensionReading: The created or updated reading
    """
    # Try to find existing reading
    try:
        reading = TensionReading.get(
            (TensionReading.tension_session_id == tension_session_id) &
            (TensionReading.spoke_number == spoke_number) &
            (TensionReading.side == side)
        )
        # Update existing reading
        reading.tm_reading = tm_reading
        reading.estimated_tension_kgf = estimated_tension_kgf
        reading.range_status = range_status
        reading.average_deviation_status = average_deviation_status
        reading.save()
        logger.debug(f"Updated reading for session {tension_session_id}, spoke {spoke_number} {side}")
        return reading
    except TensionReading.DoesNotExist:
        # Create new reading
        reading = create_tension_reading(
            tension_session_id=tension_session_id,
            spoke_number=spoke_number,
            side=side,
            tm_reading=tm_reading,
            estimated_tension_kgf=estimated_tension_kgf,
            range_status=range_status,
            average_deviation_status=average_deviation_status
        )
        logger.debug(f"Created reading for session {tension_session_id}, spoke {spoke_number} {side}")
        return reading

def delete_tension_reading(tension_session_id, spoke_number, side):
    """Delete a single tension reading.

    Args:
        tension_session_id: Session ID
        spoke_number: Spoke number
        side: 'left' or 'right'

    Returns:
        bool: True if deleted, False if not found
    """
    try:
        reading = TensionReading.get(
            (TensionReading.tension_session_id == tension_session_id) &
            (TensionReading.spoke_number == spoke_number) &
            (TensionReading.side == side)
        )
        reading.delete_instance()
        logger.debug(f"Deleted reading for session {tension_session_id}, spoke {spoke_number} {side}")
        return True
    except TensionReading.DoesNotExist:
        logger.debug(f"No reading found to delete for session {tension_session_id}, spoke {spoke_number} {side}")
        return False

def bulk_create_or_update_readings(tension_session_id, readings_data):
    """Bulk create or update tension readings.

    Args:
        tension_session_id: Session ID
        readings_data: List of dicts with reading data
    """
    # Delete existing readings for this session
    TensionReading.delete().where(TensionReading.tension_session_id == tension_session_id).execute()

    # Create new readings
    for data in readings_data:
        create_tension_reading(
            tension_session_id=tension_session_id,
            spoke_number=data['spoke_number'],
            side=data['side'],
            tm_reading=data['tm_reading'],
            estimated_tension_kgf=data['estimated_tension_kgf'],
            range_status=data['range_status'],
            average_deviation_status=data['average_deviation_status']
        )

    logger.info(f"Bulk updated {len(readings_data)} readings for session {tension_session_id}")
    return True