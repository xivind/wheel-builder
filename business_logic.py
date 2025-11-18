from database_manager import (
    get_hub_by_id, get_rim_by_id, get_spoke_by_id, get_nipple_by_id,
    get_builds_using_hub, get_builds_using_rim, get_builds_using_spoke, get_builds_using_nipple
)
from logger import logger
import math
import statistics

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
    # Need at least one spoke selected (left or right)
    if not wheel_build.spoke_left_id and not wheel_build.spoke_right_id:
        missing.append("spoke (left or right)")
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
    spoke_left = get_spoke_by_id(wheel_build.spoke_left_id) if wheel_build.spoke_left_id else None
    spoke_right = get_spoke_by_id(wheel_build.spoke_right_id) if wheel_build.spoke_right_id else None
    nipple = get_nipple_by_id(wheel_build.nipple_id)

    # Use spoke_left for left calculation, or spoke_right as fallback
    left_spoke = spoke_left or spoke_right
    # Use spoke_right for right calculation, or spoke_left as fallback
    right_spoke = spoke_right or spoke_left

    left_length = calculate_spoke_length(
        hub, rim, left_spoke, nipple,
        wheel_build.spoke_count,
        wheel_build.lacing_pattern,
        "left"
    )

    right_length = calculate_spoke_length(
        hub, rim, right_spoke, nipple,
        wheel_build.spoke_count,
        wheel_build.lacing_pattern,
        "right"
    )

    return {
        'left': left_length,
        'right': right_length
    }

def calculate_tension_range(spoke, rim):
    """Calculate recommended min/max tension for a spoke/rim combination.

    NOTE: This is a placeholder. User will provide actual formulas.

    Args:
        spoke: Spoke model instance
        rim: Rim model instance

    Returns:
        dict: {
            'min_kgf': float,
            'max_kgf': float,
            'min_tm_reading': float,
            'max_tm_reading': float
        }
    """
    # Use spoke max_tension as the upper limit
    # Set min as 60% of max (common rule of thumb)
    max_tension = spoke.max_tension
    min_tension = max_tension * 0.6

    # Placeholder conversion to Park Tool TM-1 readings
    # Actual conversion depends on spoke gauge and type
    # This is simplified: divide kgf by a factor
    gauge_num = spoke.gauge  # gauge is now stored as numeric (mm)
    conversion_factor = 4.5 if gauge_num >= 2.0 else 5.0

    min_tm = min_tension / conversion_factor
    max_tm = max_tension / conversion_factor

    logger.info(f"Tension range: {min_tension:.1f}-{max_tension:.1f} kgf, TM: {min_tm:.1f}-{max_tm:.1f}")

    return {
        'min_kgf': round(min_tension, 1),
        'max_kgf': round(max_tension, 1),
        'min_tm_reading': round(min_tm, 1),
        'max_tm_reading': round(max_tm, 1)
    }

def analyze_tension_readings(readings, tension_range):
    """Analyze tension readings for a session.

    Args:
        readings: List of TensionReading model instances
        tension_range: Dict from calculate_tension_range

    Returns:
        dict: Analysis results by side
    """
    results = {
        'left': {'readings': [], 'average': 0, 'std_dev': 0, 'min': 0, 'max': 0},
        'right': {'readings': [], 'average': 0, 'std_dev': 0, 'min': 0, 'max': 0}
    }

    # Separate readings by side
    left_readings = [r for r in readings if r.side == 'left']
    right_readings = [r for r in readings if r.side == 'right']

    for side, side_readings in [('left', left_readings), ('right', right_readings)]:
        if not side_readings:
            continue

        tensions = [r.estimated_tension_kgf for r in side_readings]

        avg = statistics.mean(tensions)
        std_dev = statistics.stdev(tensions) if len(tensions) > 1 else 0
        min_tension = min(tensions)
        max_tension = max(tensions)

        # Calculate ±20% limits
        upper_limit = avg * 1.2
        lower_limit = avg * 0.8

        results[side] = {
            'readings': side_readings,
            'average': round(avg, 2),
            'std_dev': round(std_dev, 2),
            'min': round(min_tension, 2),
            'max': round(max_tension, 2),
            'upper_limit_20pct': round(upper_limit, 2),
            'lower_limit_20pct': round(lower_limit, 2)
        }

    return results

def determine_quality_status(analysis_results, tension_range):
    """Determine overall quality status of wheel.

    Args:
        analysis_results: Dict from analyze_tension_readings
        tension_range: Dict from calculate_tension_range

    Returns:
        dict: {
            'status': 'well_balanced' | 'needs_truing' | 'uneven_tension',
            'issues': list of issue descriptions
        }
    """
    issues = []

    for side in ['left', 'right']:
        readings = analysis_results[side]['readings']

        # Check if any readings outside recommended range
        out_of_range = [r for r in readings if r.range_status != 'in_range']
        if out_of_range:
            issues.append(f"{len(out_of_range)} spokes on {side} side outside recommended tension range")

        # Check if any readings outside ±20%
        out_of_tolerance = [r for r in readings if r.average_deviation_status != 'in_range']
        if out_of_tolerance:
            issues.append(f"{len(out_of_tolerance)} spokes on {side} side outside ±20% tolerance")

        # Check standard deviation
        if analysis_results[side]['std_dev'] > 10:
            issues.append(f"High tension variance on {side} side (σ={analysis_results[side]['std_dev']:.1f})")

    if not issues:
        status = 'well_balanced'
    elif any('outside ±20%' in issue for issue in issues):
        status = 'needs_truing'
    else:
        status = 'uneven_tension'

    return {
        'status': status,
        'issues': issues
    }

def tm_reading_to_kgf(tm_reading, spoke_gauge):
    """Convert Park Tool TM-1 reading to kgf tension.

    NOTE: This is a simplified conversion. Actual conversion depends on spoke gauge.
    Based on Park Tool TM-1 conversion charts.

    Args:
        tm_reading: Park Tool TM-1 reading (0-50 range)
        spoke_gauge: Spoke gauge in mm (e.g., 2.0, 1.8)

    Returns:
        float: Estimated tension in kgf
    """
    gauge_num = spoke_gauge  # gauge is now stored as numeric (mm)

    # Simplified conversion factor based on gauge
    # For 2.0mm spokes: multiply by ~10
    # For thinner spokes: multiply by less
    # For thicker spokes: multiply by more
    if gauge_num >= 2.3:
        conversion_factor = 12.0
    elif gauge_num >= 2.0:
        conversion_factor = 10.0
    elif gauge_num >= 1.8:
        conversion_factor = 8.5
    else:
        conversion_factor = 7.0

    kgf = tm_reading * conversion_factor

    logger.debug(f"TM reading {tm_reading} with gauge {spoke_gauge} mm = {kgf:.1f} kgf")

    return round(kgf, 1)