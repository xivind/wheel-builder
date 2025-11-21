# Spoke Type System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace formula-based tension meter conversion with table lookup system using Park Tool's complete calibration data for 36 spoke types.

**Architecture:** Add SpokeType and ConversionPoint tables, update Spoke table to reference spoke types, rewrite tm_reading_to_kgf to use linear interpolation, update UI to spoke type selection instead of manual entry.

**Tech Stack:** Python 3, Peewee ORM, SQLite, FastAPI, Jinja2 templates, HTMX

---

## Task 1: Update Database Schema

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/database_model.py`

**Step 1: Add SpokeType model class**

Add after the Rim class (after line 37):

```python
class SpokeType(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()  # e.g., "Steel Round 2.0mm"
    material = CharField()  # Steel, Aluminum, Titanium, Carbon
    shape = CharField()  # Round or Blade
    dimensions = CharField()  # "2.0mm" or "1.4 x 2.6mm"
    min_tm_reading = IntegerField()  # Lowest TM reading in conversion table
    max_tm_reading = IntegerField()  # Highest TM reading in conversion table
    min_tension_kgf = FloatField()  # Lowest kgf in conversion table
    max_tension_kgf = FloatField()  # Highest kgf in conversion table
```

**Step 2: Add ConversionPoint model class**

Add after the SpokeType class:

```python
class ConversionPoint(BaseModel):
    id = AutoField()  # Auto-incrementing primary key
    spoke_type_id = CharField()  # Foreign key to SpokeType
    tm_reading = IntegerField()  # Park Tool TM-1 reading (0-50)
    kgf = IntegerField()  # Corresponding tension in kgf

    class Meta:
        database = db
        indexes = (
            (('spoke_type_id', 'tm_reading'), True),  # Unique constraint
        )
```

**Step 3: Update Spoke model**

Replace the existing Spoke class (lines 39-44) with:

```python
class Spoke(BaseModel):
    id = CharField(primary_key=True)
    spoke_type_id = CharField()  # Foreign key to SpokeType, required
    length = FloatField()  # mm
```

**Step 4: Update initialize_database() function**

Update the create_tables call (line 93-96) to include new models:

```python
def initialize_database():
    """Create tables if they don't exist."""
    db.connect()
    db.create_tables([
        Hub, Rim, SpokeType, ConversionPoint, Spoke, Nipple,
        WheelBuild, TensionSession, TensionReading
    ], safe=True)
    db.close()
```

**Step 5: Commit schema changes**

```bash
git add database_model.py
git commit -m "feat: add SpokeType and ConversionPoint tables, update Spoke schema

- Add SpokeType table with material, shape, dimensions, tension range
- Add ConversionPoint table for TM→kgf lookup
- Update Spoke to reference spoke_type_id
- Remove material, gauge, max_tension from Spoke (now in SpokeType)"
```

---

## Task 2: Create Data Seeding Function

**Files:**
- Create: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/seed_spoke_types.py`

**Step 1: Write seed_spoke_types function**

Create new file with complete seeding logic:

```python
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
```

**Step 2: Test seeding manually**

```bash
cd /home/xivind/code/wheel-builder/.worktrees/spoke-type-system
rm -f /app/data/wheel_builder.db  # Fresh database
python3 seed_spoke_types.py
```

Expected output:
```
Seeded 36 spoke types
```

**Step 3: Verify seeding in database**

```bash
sqlite3 /app/data/wheel_builder.db "SELECT COUNT(*) FROM spoketype;"
sqlite3 /app/data/wheel_builder.db "SELECT COUNT(*) FROM conversionpoint;"
sqlite3 /app/data/wheel_builder.db "SELECT name, min_tm_reading, max_tm_reading FROM spoketype LIMIT 5;"
```

Expected: 36 spoke types, ~400 conversion points, sample data displayed

**Step 4: Integrate seeding into initialize_database**

Modify `database_model.py` initialize_database function:

```python
def initialize_database():
    """Create tables if they don't exist."""
    db.connect()
    db.create_tables([
        Hub, Rim, SpokeType, ConversionPoint, Spoke, Nipple,
        WheelBuild, TensionSession, TensionReading
    ], safe=True)

    # Seed spoke types if table is empty
    if SpokeType.select().count() == 0:
        from seed_spoke_types import seed_spoke_types
        seed_spoke_types()

    db.close()
```

**Step 5: Commit seeding function**

```bash
git add seed_spoke_types.py database_model.py
git commit -m "feat: add spoke type seeding from conversion table

- Parse 36 spoke types from conversion_table.txt
- Extract material, shape, dimensions from names
- Calculate min/max TM and kgf values
- Create SpokeType and ConversionPoint records
- Integrate seeding into initialize_database"
```

---

## Task 3: Update tm_reading_to_kgf Function

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/business_logic.py:313-352`

**Step 1: Replace tm_reading_to_kgf function**

Replace the entire function (lines 313-352) with new implementation:

```python
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
                f"Interpolated: TM {tm_reading} between {tm_low}→{kgf_low} and "
                f"{tm_high}→{kgf_high} = {kgf:.1f} kgf"
            )
            return {'kgf': round(kgf, 1), 'status': 'interpolated'}

    # Should never reach here if range checks worked
    logger.error(f"Failed to interpolate TM reading {tm_reading}")
    return {'kgf': None, 'status': 'below_table'}
```

**Step 2: Add helper function get_spoke_type_by_id**

Add to database_manager.py (if it doesn't exist there, add to business_logic.py):

```python
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
```

**Step 3: Commit tm_reading_to_kgf changes**

```bash
git add business_logic.py database_manager.py
git commit -m "feat: rewrite tm_reading_to_kgf to use table lookup

- Fetch ConversionPoint data for spoke type
- Check if reading is within table range
- Return exact match if found
- Linear interpolation between adjacent points
- No extrapolation for out-of-range readings
- Return status: exact, interpolated, below_table, above_table"
```

---

## Task 4: Update calculate_tension_range Function

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/business_logic.py:174-221`

**Step 1: Simplify calculate_tension_range**

Replace the function (lines 174-221) with:

```python
def calculate_tension_range(spoke, rim):
    """Calculate recommended min/max tension for a spoke/rim combination.

    Uses spoke type's calibration data directly from Park Tool conversion table.

    Args:
        spoke: Spoke model instance
        rim: Rim model instance

    Returns:
        dict: {
            'min_kgf': float,
            'max_kgf': float,
            'min_tm_reading': int,
            'max_tm_reading': int
        }
    """
    # Get spoke type
    spoke_type = get_spoke_type_by_id(spoke.spoke_type_id)

    if not spoke_type:
        logger.error(f"SpokeType {spoke.spoke_type_id} not found for spoke {spoke.id}")
        # Return safe defaults if spoke type not found
        return {
            'min_kgf': 50.0,
            'max_kgf': 120.0,
            'min_tm_reading': 15,
            'max_tm_reading': 25
        }

    logger.info(
        f"Tension range for {spoke_type.name}: "
        f"{spoke_type.min_tension_kgf}-{spoke_type.max_tension_kgf} kgf, "
        f"TM: {spoke_type.min_tm_reading}-{spoke_type.max_tm_reading}"
    )

    return {
        'min_kgf': spoke_type.min_tension_kgf,
        'max_kgf': spoke_type.max_tension_kgf,
        'min_tm_reading': spoke_type.min_tm_reading,
        'max_tm_reading': spoke_type.max_tm_reading
    }
```

**Step 2: Commit tension range changes**

```bash
git add business_logic.py
git commit -m "feat: simplify calculate_tension_range to use spoke type data

- Use spoke_type.min/max_tension_kgf directly
- Use spoke_type.min/max_tm_reading directly
- Remove 60% rule calculation
- Remove inverse formula calculations"
```

---

## Task 5: Update TensionReading Creation Logic

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/main.py` (find the route that creates tension readings)

**Step 1: Find the tension reading creation route**

Search for the route:

```bash
grep -n "TensionReading.create" /home/xivind/code/wheel-builder/.worktrees/spoke-type-system/main.py
```

**Step 2: Update tension reading creation**

Find the section where TensionReading.create is called and update to handle the new return format:

```python
# Get spoke from wheel build (via session)
wheel_build = get_wheel_build_by_id(session.wheel_build_id)
spoke = get_spoke_by_id(
    wheel_build.spoke_left_id if side == 'left' else wheel_build.spoke_right_id
)

# Convert TM reading to kgf
conversion_result = tm_reading_to_kgf(tm_reading, spoke.spoke_type_id)

# Handle conversion status
if conversion_result['status'] in ['below_table', 'above_table']:
    # Out of range - save NULL for kgf
    estimated_tension_kgf = None
    range_status = conversion_result['status']
    average_deviation_status = 'unknown'
else:
    # Valid conversion
    estimated_tension_kgf = conversion_result['kgf']

    # Calculate range status
    tension_range = calculate_tension_range(spoke, rim)
    if estimated_tension_kgf < tension_range['min_kgf']:
        range_status = 'under'
    elif estimated_tension_kgf > tension_range['max_kgf']:
        range_status = 'over'
    else:
        range_status = 'in_range'

    # average_deviation_status will be calculated later in analyze_tension_readings
    average_deviation_status = 'in_range'  # Temporary, updated after all readings

# Create reading
TensionReading.create(
    id=str(uuid.uuid4()),
    tension_session_id=session_id,
    spoke_number=spoke_number,
    side=side,
    tm_reading=tm_reading,
    estimated_tension_kgf=estimated_tension_kgf,
    range_status=range_status,
    average_deviation_status=average_deviation_status
)
```

**Step 3: Commit tension reading changes**

```bash
git add main.py
git commit -m "feat: update tension reading creation for new conversion format

- Handle dict return from tm_reading_to_kgf
- Set estimated_tension_kgf to NULL for out-of-range readings
- Set range_status to below_table or above_table
- Set average_deviation_status to unknown for unmeasurable readings"
```

---

## Task 6: Update analyze_tension_readings Function

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/business_logic.py:223-267`

**Step 1: Update analyze_tension_readings to filter NULL readings**

Modify the function (lines 223-267):

```python
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

        # Filter out NULL readings (out-of-table conversions)
        valid_readings = [
            r for r in side_readings
            if r.estimated_tension_kgf is not None
        ]

        if not valid_readings:
            # All readings are out of range
            results[side] = {
                'readings': side_readings,
                'average': 0,
                'std_dev': 0,
                'min': 0,
                'max': 0,
                'upper_limit_20pct': 0,
                'lower_limit_20pct': 0
            }
            continue

        tensions = [r.estimated_tension_kgf for r in valid_readings]

        avg = statistics.mean(tensions)
        std_dev = statistics.stdev(tensions) if len(tensions) > 1 else 0
        min_tension = min(tensions)
        max_tension = max(tensions)

        # Calculate ±20% limits
        upper_limit = avg * 1.2
        lower_limit = avg * 0.8

        results[side] = {
            'readings': side_readings,  # Include all readings for display
            'average': round(avg, 2),
            'std_dev': round(std_dev, 2),
            'min': round(min_tension, 2),
            'max': round(max_tension, 2),
            'upper_limit_20pct': round(upper_limit, 2),
            'lower_limit_20pct': round(lower_limit, 2)
        }

    return results
```

**Step 2: Commit analysis changes**

```bash
git add business_logic.py
git commit -m "feat: update analyze_tension_readings to skip NULL values

- Filter out readings where estimated_tension_kgf is NULL
- Calculate average only from valid readings
- Still return all readings for display purposes
- Handle case where all readings are out of range"
```

---

## Task 7: Update Spoke API Routes

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/main.py` (spoke CRUD routes)
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/database_manager.py`

**Step 1: Add get_all_spoke_types to database_manager.py**

```python
def get_all_spoke_types():
    """Get all spoke types for selection.

    Returns:
        list: All SpokeType instances, ordered by name
    """
    from database_model import SpokeType
    return list(SpokeType.select().order_by(SpokeType.name))
```

**Step 2: Update spoke form route (GET /config/spoke/form)**

Find and update the route:

```python
@app.get("/config/spoke/form")
async def get_spoke_form(request: Request, spoke_id: str = None):
    """Show spoke creation/edit form."""
    spoke = None
    locked = False
    used_by_builds = []
    spoke_types = get_all_spoke_types()  # NEW: Load all spoke types

    if spoke_id:
        spoke = get_spoke_by_id(spoke_id)
        if spoke:
            lock_status = check_component_locked('spoke', spoke_id)
            locked = lock_status['locked']
            if locked:
                used_by_builds = get_builds_using_spoke(spoke_id)

    return templates.TemplateResponse(
        "partials/spoke_form.html",
        {
            "request": request,
            "spoke": spoke,
            "locked": locked,
            "used_by_builds": used_by_builds,
            "spoke_types": spoke_types  # NEW: Pass to template
        }
    )
```

**Step 3: Update spoke create route (POST /config/spoke/create)**

Find and update the route:

```python
@app.post("/config/spoke/create")
async def create_spoke(
    request: Request,
    spoke_type_id: str = Form(...),
    length: float = Form(...)
):
    """Create new spoke."""
    import uuid
    from database_model import Spoke

    # Validate spoke type exists
    spoke_type = get_spoke_type_by_id(spoke_type_id)
    if not spoke_type:
        logger.error(f"Invalid spoke_type_id: {spoke_type_id}")
        # Return error response
        return templates.TemplateResponse(
            "partials/spoke_form.html",
            {
                "request": request,
                "error": "Invalid spoke type selected",
                "spoke_types": get_all_spoke_types()
            },
            status_code=400
        )

    # Validate length
    if length <= 0:
        return templates.TemplateResponse(
            "partials/spoke_form.html",
            {
                "request": request,
                "error": "Length must be greater than 0",
                "spoke_types": get_all_spoke_types()
            },
            status_code=400
        )

    # Create spoke
    spoke = Spoke.create(
        id=str(uuid.uuid4()),
        spoke_type_id=spoke_type_id,
        length=length
    )

    logger.info(f"Created spoke: {spoke.id} (type: {spoke_type.name}, length: {length}mm)")

    # Return updated config page or success response
    return RedirectResponse(url="/config", status_code=303)
```

**Step 4: Update spoke update route (POST /config/spoke/<id>/update)**

Find and update the route:

```python
@app.post("/config/spoke/{spoke_id}/update")
async def update_spoke(
    request: Request,
    spoke_id: str,
    length: float = Form(...)
):
    """Update existing spoke (only length can be changed)."""
    spoke = get_spoke_by_id(spoke_id)
    if not spoke:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Spoke not found"},
            status_code=404
        )

    # Check if locked
    lock_status = check_component_locked('spoke', spoke_id)
    if lock_status['locked']:
        return templates.TemplateResponse(
            "partials/spoke_form.html",
            {
                "request": request,
                "spoke": spoke,
                "locked": True,
                "used_by_builds": get_builds_using_spoke(spoke_id),
                "spoke_types": get_all_spoke_types(),
                "error": "Cannot edit spoke - it is being used in wheel builds"
            },
            status_code=403
        )

    # Validate length
    if length <= 0:
        return templates.TemplateResponse(
            "partials/spoke_form.html",
            {
                "request": request,
                "spoke": spoke,
                "spoke_types": get_all_spoke_types(),
                "error": "Length must be greater than 0"
            },
            status_code=400
        )

    # Update only length (spoke_type_id cannot be changed)
    spoke.length = length
    spoke.save()

    logger.info(f"Updated spoke {spoke_id}: length={length}mm")

    return RedirectResponse(url="/config", status_code=303)
```

**Step 5: Commit spoke route changes**

```bash
git add main.py database_manager.py
git commit -m "feat: update spoke API routes for type selection

- Add get_all_spoke_types helper
- Load spoke types in form route
- Update create to accept spoke_type_id + length
- Update edit to only allow length changes
- Validate spoke_type_id exists
- spoke_type_id locked once spoke is used in builds"
```

---

## Task 8: Update Spoke Form Template

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/templates/partials/spoke_form.html`

**Step 1: Replace spoke form with type selection UI**

Replace the entire form body (lines 11-56) with:

```html
<form method="POST" action="{% if spoke %}/config/spoke/{{ spoke.id }}/update{% else %}/config/spoke/create{% endif %}">
    <div class="modal-body">
        {% if locked %}
        <div class="alert alert-warning">
            <i class="bi bi-exclamation-triangle"></i>
            <strong>This component is locked.</strong>
            It is being used by the following builds and cannot be edited:
            <ul class="mb-0 mt-2">
                {% for build in used_by_builds %}
                <li><a href="/build/{{ build.id }}">{{ build.name }}</a></li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        {% if error %}
        <div class="alert alert-danger">
            <i class="bi bi-exclamation-circle"></i>
            {{ error }}
        </div>
        {% endif %}

        {% if spoke %}
        {# Edit mode - show spoke type as readonly #}
        <div class="mb-3">
            <label class="form-label">Spoke Type</label>
            <div class="card bg-light">
                <div class="card-body">
                    <h6 class="card-title mb-2">{{ spoke.spoke_type.name }}</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">Material:</small>
                            <div>{{ spoke.spoke_type.material }}</div>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted">Dimensions:</small>
                            <div>{{ spoke.spoke_type.dimensions }}</div>
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">Tension Range:</small>
                        <div>{{ spoke.spoke_type.min_tm_reading }} ({{ spoke.spoke_type.min_tension_kgf }} kgf) - {{ spoke.spoke_type.max_tm_reading }} ({{ spoke.spoke_type.max_tension_kgf }} kgf)</div>
                    </div>
                </div>
            </div>
            <input type="hidden" name="spoke_type_id" value="{{ spoke.spoke_type_id }}">
        </div>

        {% else %}
        {# Create mode - allow spoke type selection #}
        <div class="mb-3">
            <label for="spoke_type_id" class="form-label">Spoke Type <span class="text-danger">*</span></label>
            <select class="form-select" id="spoke_type_id" name="spoke_type_id" required onchange="updateSpokeTypeInfo(this)">
                <option value="">Select spoke type...</option>
                {% for spoke_type in spoke_types %}
                <option value="{{ spoke_type.id }}"
                        data-material="{{ spoke_type.material }}"
                        data-dimensions="{{ spoke_type.dimensions }}"
                        data-min-tm="{{ spoke_type.min_tm_reading }}"
                        data-max-tm="{{ spoke_type.max_tm_reading }}"
                        data-min-kgf="{{ spoke_type.min_tension_kgf }}"
                        data-max-kgf="{{ spoke_type.max_tension_kgf }}">
                    {{ spoke_type.name }}
                </option>
                {% endfor %}
            </select>
        </div>

        <div id="spoke-type-info" class="card bg-light mb-3" style="display: none;">
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <small class="text-muted">Material:</small>
                        <div id="info-material">-</div>
                    </div>
                    <div class="col-md-6">
                        <small class="text-muted">Dimensions:</small>
                        <div id="info-dimensions">-</div>
                    </div>
                </div>
                <div class="mt-2">
                    <small class="text-muted">Tension Range:</small>
                    <div id="info-range">-</div>
                </div>
            </div>
        </div>
        {% endif %}

        <div class="mb-3">
            <label for="length" class="form-label">Length (mm) <span class="text-danger">*</span></label>
            <input type="number" step="0.1" min="0.1" class="form-control" id="length" name="length"
                   value="{% if spoke %}{{ spoke.length }}{% endif %}"
                   placeholder="260" {% if locked %}disabled{% else %}required{% endif %}>
        </div>

        <p class="text-muted small mt-3">
            <i class="bi bi-info-circle"></i>
            {% if spoke %}Only length can be edited.{% else %}All fields are required{% endif %}
        </p>
    </div>
    <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        {% if not locked %}
        <button type="submit" class="btn btn-primary">
            <i class="bi bi-check-lg"></i> {% if spoke %}Update{% else %}Create{% endif %} Spoke
        </button>
        {% endif %}
    </div>
</form>

<script>
function updateSpokeTypeInfo(select) {
    const option = select.selectedOptions[0];
    const infoDiv = document.getElementById('spoke-type-info');

    if (!option.value) {
        infoDiv.style.display = 'none';
        return;
    }

    document.getElementById('info-material').textContent = option.dataset.material;
    document.getElementById('info-dimensions').textContent = option.dataset.dimensions;
    document.getElementById('info-range').textContent =
        `${option.dataset.minTm} (${option.dataset.minKgf} kgf) - ${option.dataset.maxTm} (${option.dataset.maxKgf} kgf)`;

    infoDiv.style.display = 'block';
}
</script>
```

**Step 2: Commit template changes**

```bash
git add templates/partials/spoke_form.html
git commit -m "feat: update spoke form for type selection UI

- Show dropdown of 36 spoke types in create mode
- Display spoke type details when selected (material, dimensions, range)
- Show readonly spoke type info in edit mode
- Only allow length editing
- Add JavaScript to show/hide type info on selection"
```

---

## Task 9: Update Spoke Display in Config Page

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/templates/config.html` (or wherever spokes are listed)

**Step 1: Update spoke list display**

Find the spoke listing section and update to show spoke type + length:

```html
{% for spoke in spokes %}
<tr>
    <td>{{ spoke.spoke_type.name }} @ {{ spoke.length }}mm</td>
    <td>
        <span class="badge bg-secondary">{{ spoke.spoke_type.material }}</span>
        <span class="badge bg-info">{{ spoke.spoke_type.dimensions }}</span>
    </td>
    <td>{{ spoke.spoke_type.min_tension_kgf }} - {{ spoke.spoke_type.max_tension_kgf }} kgf</td>
    <td>
        <button class="btn btn-sm btn-primary" onclick="editSpoke('{{ spoke.id }}')">
            <i class="bi bi-pencil"></i> Edit
        </button>
        <button class="btn btn-sm btn-danger" onclick="deleteSpoke('{{ spoke.id }}')">
            <i class="bi bi-trash"></i> Delete
        </button>
    </td>
</tr>
{% endfor %}
```

**Step 2: Commit config page changes**

```bash
git add templates/config.html
git commit -m "feat: update spoke display to show type + length

- Display as 'Spoke Type @ Length'
- Show material and dimensions as badges
- Display tension range from spoke type"
```

---

## Task 10: Update Tension Reading Display with New Badges

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/templates/partials/tension_reading_response.html`

**Step 1: Update tension reading row template**

Find the template that displays tension reading rows and update badge logic:

```html
<tr>
    <td>{{ reading.spoke_number }}</td>
    <td>{{ reading.side|upper }}</td>
    <td>{{ reading.tm_reading }}</td>
    <td>
        {% if reading.estimated_tension_kgf is none %}
        -
        {% else %}
        {{ reading.estimated_tension_kgf }} kgf
        {% endif %}
    </td>
    <td>
        {% if reading.range_status == 'in_range' %}
        <span class="badge bg-success">IN RANGE</span>
        {% elif reading.range_status == 'over' %}
        <span class="badge bg-danger">OVER</span>
        {% elif reading.range_status == 'under' %}
        <span class="badge bg-warning">UNDER</span>
        {% elif reading.range_status == 'below_table' %}
        <span class="badge bg-danger">BELOW RANGE</span>
        {% elif reading.range_status == 'above_table' %}
        <span class="badge bg-danger">ABOVE RANGE</span>
        {% endif %}
    </td>
    <td>
        {% if reading.average_deviation_status == 'unknown' %}
        <span class="badge bg-secondary">UNKNOWN</span>
        {% elif reading.average_deviation_status == 'in_range' %}
        <span class="badge bg-success">IN RANGE</span>
        {% elif reading.average_deviation_status == 'over' %}
        <span class="badge bg-danger">OVER</span>
        {% elif reading.average_deviation_status == 'under' %}
        <span class="badge bg-warning">UNDER</span>
        {% endif %}
    </td>
</tr>
```

**Step 2: Commit tension display changes**

```bash
git add templates/partials/tension_reading_response.html
git commit -m "feat: add badges for out-of-range tension readings

- Show '-' for tension when kgf is NULL
- Add BELOW RANGE badge (red) for below_table status
- Add ABOVE RANGE badge (red) for above_table status
- Add UNKNOWN badge (grey) for unmeasurable deviation"
```

---

## Task 11: Update Database Manager Helpers

**Files:**
- Modify: `/home/xivind/code/wheel-builder/.worktrees/spoke-type-system/database_manager.py`

**Step 1: Update get_spoke_by_id to include spoke_type**

Find get_spoke_by_id and ensure it fetches the related spoke_type:

```python
def get_spoke_by_id(spoke_id):
    """Get spoke by ID with spoke type.

    Args:
        spoke_id: Spoke UUID

    Returns:
        Spoke instance or None
    """
    from database_model import Spoke, SpokeType
    try:
        spoke = Spoke.get_by_id(spoke_id)
        # Eager load spoke type
        spoke.spoke_type = SpokeType.get_by_id(spoke.spoke_type_id)
        return spoke
    except (Spoke.DoesNotExist, SpokeType.DoesNotExist):
        return None
```

**Step 2: Update get_all_spokes to include spoke_types**

```python
def get_all_spokes():
    """Get all spokes with their spoke types.

    Returns:
        list: All Spoke instances with spoke_type loaded
    """
    from database_model import Spoke, SpokeType

    spokes = list(Spoke.select())

    # Eager load spoke types
    for spoke in spokes:
        try:
            spoke.spoke_type = SpokeType.get_by_id(spoke.spoke_type_id)
        except SpokeType.DoesNotExist:
            spoke.spoke_type = None
            logger.warning(f"Spoke {spoke.id} has invalid spoke_type_id")

    return spokes
```

**Step 3: Commit database manager changes**

```bash
git add database_manager.py
git commit -m "feat: eager load spoke types in database helpers

- Update get_spoke_by_id to load spoke_type
- Update get_all_spokes to load spoke_types
- Handle missing spoke types gracefully"
```

---

## Task 12: Testing and Verification

**Files:**
- None (manual testing)

**Step 1: Fresh database setup**

```bash
cd /home/xivind/code/wheel-builder/.worktrees/spoke-type-system
rm -f /app/data/wheel_builder.db
python3 -c "from database_model import initialize_database; initialize_database()"
```

Expected: Database created, 36 spoke types seeded

**Step 2: Verify spoke types in database**

```bash
sqlite3 /app/data/wheel_builder.db "SELECT COUNT(*) FROM spoketype;"
sqlite3 /app/data/wheel_builder.db "SELECT name, material, min_tm_reading, max_tm_reading FROM spoketype LIMIT 5;"
```

Expected: 36 spoke types, sample data shown

**Step 3: Start application and test spoke creation**

```bash
python3 main.py
```

- Navigate to /config
- Click "Add Spoke"
- Select "Steel Round 2.0mm" from dropdown
- Verify type info appears (material: Steel, range: 17-28)
- Enter length: 260
- Submit
- Verify spoke appears as "Steel Round 2.0mm @ 260mm"

**Step 4: Test tension reading with valid TM value**

- Create a wheel build with the spoke
- Create tension session
- Enter TM reading: 24 (within range for Steel Round 2.0mm)
- Verify kgf value is calculated and displayed
- Verify badges show correctly

**Step 5: Test tension reading with below-range TM value**

- Enter TM reading: 10 (below min of 17 for Steel Round 2.0mm)
- Verify tension column shows "-"
- Verify range badge shows "BELOW RANGE" (red)
- Verify deviation badge shows "UNKNOWN" (grey)

**Step 6: Test tension reading with above-range TM value**

- Enter TM reading: 35 (above max of 28 for Steel Round 2.0mm)
- Verify tension column shows "-"
- Verify range badge shows "ABOVE RANGE" (red)
- Verify deviation badge shows "UNKNOWN" (grey)

**Step 7: Test average calculation excludes NULL**

- Create 4 readings: 120 kgf, NULL (below), 125 kgf, 118 kgf
- Verify average = (120+125+118)/3 = 121 kgf
- Verify valid readings show ±20% status
- Verify NULL reading shows "UNKNOWN"

**Step 8: Final commit**

```bash
git add -A
git commit -m "test: verify spoke type system implementation

Manual testing confirms:
- 36 spoke types seeded correctly
- Spoke selection UI works
- TM→kgf conversion accurate
- Out-of-range readings handled properly
- Badges display correctly
- Average calculation excludes NULL values"
```

---

## Completion Checklist

- [ ] SpokeType and ConversionPoint tables created
- [ ] Spoke table updated with spoke_type_id
- [ ] 36 spoke types seeded from conversion_table.txt
- [ ] tm_reading_to_kgf uses table lookup + linear interpolation
- [ ] calculate_tension_range uses spoke type data directly
- [ ] TensionReading creation handles out-of-range readings
- [ ] analyze_tension_readings skips NULL values
- [ ] Spoke API routes updated for type selection
- [ ] Spoke form shows type selection dropdown
- [ ] Config page displays "Type @ Length" format
- [ ] Tension reading display shows new badges
- [ ] Database helpers eager load spoke types
- [ ] Manual testing completed and verified

---

## Next Steps After Implementation

1. **Delete old database** - `rm /app/data/wheel_builder.db` (confirmed not in production)
2. **Restart with fresh database** - Let seeding populate 36 spoke types
3. **Update any existing seed_data.py** - Remove old spoke seeding if it exists
4. **Consider adding spoke type search/filter** - If 36 types becomes unwieldy in dropdown
5. **Monitor performance** - Add caching to ConversionPoint lookups if needed

## References

- Design doc: `docs/plans/2025-11-21-spoke-type-system-design.md`
- Conversion data: `conversion_table.txt`
- TDD workflow: @superpowers:test-driven-development
- Code review: @superpowers:requesting-code-review
