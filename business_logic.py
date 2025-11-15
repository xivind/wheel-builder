from database_manager import (
    get_hub_by_id, get_rim_by_id, get_spoke_by_id, get_nipple_by_id,
    get_builds_using_hub, get_builds_using_rim, get_builds_using_spoke, get_builds_using_nipple
)
from logger import logger
import math

def can_calculate_spoke_length(wheel_build):
    """Check if wheel build has all required data for spoke length calculation.

    Args:
        wheel_build: WheelBuild model instance

    Returns:
        tuple: (bool, list of missing field names)
    """
    missing = []

    if not wheel_build.hub_id:
        missing.append("hub")
    if not wheel_build.rim_id:
        missing.append("rim")
    if not wheel_build.spoke_id:
        missing.append("spoke")
    if not wheel_build.nipple_id:
        missing.append("nipple")
    if not wheel_build.lacing_pattern:
        missing.append("lacing pattern")
    if not wheel_build.spoke_count:
        missing.append("spoke count")

    return (len(missing) == 0, missing)

def check_component_locked(component_type, component_id):
    """Check if a component is used in any wheel builds.

    Args:
        component_type: 'hub', 'rim', 'spoke', or 'nipple'
        component_id: Component UUID

    Returns:
        dict: {'locked': bool, 'builds': list of build names}
    """
    if component_type == 'hub':
        builds = get_builds_using_hub(component_id)
    elif component_type == 'rim':
        builds = get_builds_using_rim(component_id)
    elif component_type == 'spoke':
        builds = get_builds_using_spoke(component_id)
    elif component_type == 'nipple':
        builds = get_builds_using_nipple(component_id)
    else:
        logger.error(f"Unknown component type: {component_type}")
        return {'locked': False, 'builds': []}

    build_names = [build.name for build in builds]
    is_locked = len(builds) > 0

    logger.info(f"Component {component_type}:{component_id} locked={is_locked}, used in {len(builds)} builds")

    return {
        'locked': is_locked,
        'builds': build_names
    }

def calculate_spoke_length(hub, rim, spoke, nipple, spoke_count, lacing_pattern, side):
    """Calculate recommended spoke length for one side of the wheel.

    NOTE: This is a placeholder. User will provide actual formulas.
    Based on standard spoke length formula from spokelengthcalculator.com

    Args:
        hub: Hub model instance
        rim: Rim model instance
        spoke: Spoke model instance (for gauge if needed)
        nipple: Nipple model instance (for nipple length)
        spoke_count: Number of spokes (integer)
        lacing_pattern: String like "radial", "1-cross", "2-cross", "3-cross", "4-cross"
        side: "left" or "right"

    Returns:
        float: Recommended spoke length in mm
    """
    # Get hub dimensions based on side
    if side == "left":
        flange_diameter = hub.left_flange_diameter
        flange_offset = hub.left_flange_offset
    else:
        flange_diameter = hub.right_flange_diameter
        flange_offset = hub.right_flange_offset

    # Parse crossing number from lacing pattern
    if lacing_pattern == "radial":
        crossing = 0
    else:
        # Extract number from "N-cross"
        crossing = int(lacing_pattern.split("-")[0])

    # Calculate spoke angle
    # For radial: angle = 0
    # For crossed: angle depends on crossing and spoke count
    spoke_angle = (2 * math.pi * crossing) / (spoke_count / 2)

    # Standard spoke length formula
    # L = sqrt(R^2 + H^2 - 2*R*H*cos(alpha)) - nipple_length
    # Where:
    # R = ERD/2 (rim radius)
    # H = sqrt((flange_radius)^2 + (center_to_flange)^2)
    # alpha = spoke angle

    rim_radius = rim.erd / 2
    flange_radius = flange_diameter / 2

    # Distance from wheel center to flange center
    center_to_flange = abs((hub.old / 2) - flange_offset)

    # Hypotenuse from wheel center to spoke hole in flange
    h_squared = (flange_radius ** 2) + (center_to_flange ** 2)

    # Calculate spoke length
    length_squared = (rim_radius ** 2) + h_squared - (2 * rim_radius * math.sqrt(h_squared) * math.cos(spoke_angle))
    spoke_length = math.sqrt(length_squared) - nipple.length

    logger.info(f"Calculated spoke length for {side} side: {spoke_length:.2f}mm")

    return round(spoke_length, 2)

def calculate_recommended_spoke_lengths(wheel_build):
    """Calculate recommended spoke lengths for both sides.

    Args:
        wheel_build: WheelBuild model instance

    Returns:
        dict: {'left': float, 'right': float} or None if can't calculate
    """
    can_calc, missing = can_calculate_spoke_length(wheel_build)
    if not can_calc:
        logger.warning(f"Cannot calculate spoke length, missing: {missing}")
        return None

    hub = get_hub_by_id(wheel_build.hub_id)
    rim = get_rim_by_id(wheel_build.rim_id)
    spoke = get_spoke_by_id(wheel_build.spoke_id)
    nipple = get_nipple_by_id(wheel_build.nipple_id)

    left_length = calculate_spoke_length(
        hub, rim, spoke, nipple,
        wheel_build.spoke_count,
        wheel_build.lacing_pattern,
        "left"
    )

    right_length = calculate_spoke_length(
        hub, rim, spoke, nipple,
        wheel_build.spoke_count,
        wheel_build.lacing_pattern,
        "right"
    )

    return {
        'left': left_length,
        'right': right_length
    }