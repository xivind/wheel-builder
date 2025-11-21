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

    # Convert kgf to Park Tool TM-1 readings using inverse of exponential formula
    # Formula: reading = ln((kgf - a) / b) / c
    gauge_num = spoke.gauge  # gauge is now stored as numeric (mm)

    # Get coefficients for this gauge (same as tm_reading_to_kgf)
    if gauge_num >= 2.3:
        a, b, c = 18.0, 4.5, 0.128
    elif gauge_num >= 2.0:
        a, b, c = 16.126, 3.8987, 0.13127
    elif gauge_num >= 1.8:
        a, b, c = 14.0, 3.3, 0.135
    else:
        a, b, c = 12.0, 2.8, 0.138

    # Inverse formula: reading = ln((kgf - a) / b) / c
    min_tm = math.log((min_tension - a) / b) / c if min_tension > a else 0
    max_tm = math.log((max_tension - a) / b) / c if max_tension > a else 0

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

def tm_reading_to_kgf(tm_reading, spoke_type_id):
    """Convert Park Tool TM-1 reading to kgf tension using table lookup.

    Uses ConversionPoint table for accurate conversion based on spoke type.
    Linear interpolation for readings between table values.
    No extrapolation - returns None for out-of-range readings.

    Args:
        tm_reading: Park Tool TM-1 reading (0-50 range)
        spoke_type_id: UUID of SpokeType

    Returns:
        dict: {
            'kgf': float or None,
            'status': 'exact' | 'interpolated' | 'below_table' | 'above_table'
        }
    """
    from database_model import ConversionPoint, SpokeType
    from database_manager import get_spoke_type_by_id

    # Get spoke type for range info
    spoke_type = get_spoke_type_by_id(spoke_type_id)
    if not spoke_type:
        logger.error(f"SpokeType {spoke_type_id} not found")
        return {'kgf': None, 'status': 'below_table'}

    # Check if reading is out of range
    if tm_reading < spoke_type.min_tm_reading:
        logger.warning(
            f"TM reading {tm_reading} below table range for {spoke_type.name} "
            f"(min: {spoke_type.min_tm_reading})"
        )
        return {'kgf': None, 'status': 'below_table'}

    if tm_reading > spoke_type.max_tm_reading:
        logger.warning(
            f"TM reading {tm_reading} above table range for {spoke_type.name} "
            f"(max: {spoke_type.max_tm_reading})"
        )
        return {'kgf': None, 'status': 'above_table'}

    # Fetch conversion points for this spoke type, ordered by tm_reading
    conversion_points = list(
        ConversionPoint
        .select()
        .where(ConversionPoint.spoke_type_id == spoke_type_id)
        .order_by(ConversionPoint.tm_reading)
    )

    if not conversion_points:
        logger.error(f"No conversion points found for spoke type {spoke_type_id}")
        return {'kgf': None, 'status': 'below_table'}

    # Check for exact match
    for point in conversion_points:
        if point.tm_reading == tm_reading:
            logger.debug(f"Exact match: TM {tm_reading} = {point.kgf} kgf")
            return {'kgf': float(point.kgf), 'status': 'exact'}

    # Find adjacent points for interpolation
    for i in range(len(conversion_points) - 1):
        tm_low = conversion_points[i].tm_reading
        tm_high = conversion_points[i + 1].tm_reading

        if tm_low <= tm_reading <= tm_high:
            kgf_low = conversion_points[i].kgf
            kgf_high = conversion_points[i + 1].kgf

            # Linear interpolation
            ratio = (tm_reading - tm_low) / (tm_high - tm_low)
            kgf = kgf_low + ratio * (kgf_high - kgf_low)

            logger.debug(
                f"Interpolated: TM {tm_reading} between {tm_low}->{kgf_low} and "
                f"{tm_high}->{kgf_high} = {kgf:.1f} kgf"
            )
            return {'kgf': round(kgf, 1), 'status': 'interpolated'}

    # Should never reach here if range checks worked
    logger.error(f"Failed to interpolate TM reading {tm_reading}")
    return {'kgf': None, 'status': 'below_table'}