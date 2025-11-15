# Wheel Builder Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a self-hosted FastAPI web application to help bicycle wheel builders manage components, calculate spoke lengths, track tension measurements, and visualize build quality.

**Architecture:** Three-layer architecture with main.py (routing), business_logic.py (calculations/orchestration), database_manager.py (CRUD). Frontend uses Jinja2 templates with HTMX for dynamic updates, Bootstrap for styling, Chart.js for visualizations.

**Tech Stack:** FastAPI, SQLite, PeeWee ORM, Jinja2, HTMX, Bootstrap 5, TomSelect, Tempus Dominus, Chart.js, Docker

---

## Task 1: Project Dependencies

**Files:**
- Modify: `requirements.txt`
- Create: `.python-version`
- Create: `Dockerfile`
- Create: `.dockerignore`

**Step 1: Write requirements.txt**

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
peewee==3.17.0
jinja2==3.1.2
python-multipart==0.0.6
```

**Step 2: Create .python-version**

```
3.11
```

**Step 3: Create basic Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
```

**Step 4: Create .dockerignore**

```
__pycache__/
*.py[cod]
*$py.class
.git/
.gitignore
.worktrees/
*.md
.env
*.db
data/
```

**Step 5: Commit**

```bash
git add requirements.txt .python-version Dockerfile .dockerignore
git commit -m "build: add project dependencies and Docker configuration

- FastAPI, Uvicorn, PeeWee, Jinja2
- Python 3.11
- Dockerfile exposing port 8004
- Dockerignore to exclude dev files"
```

---

## Task 2: Utility Functions

**Files:**
- Modify: `utils.py`

**Step 1: Implement UUID generator**

```python
import uuid

def generate_uuid():
    """Generate a UUID string for database records.

    Returns:
        str: UUID4 as string
    """
    return str(uuid.uuid4())
```

**Step 2: Verify in Python REPL**

```bash
python3 -c "from utils import generate_uuid; print(generate_uuid())"
```

Expected: UUID string like `"550e8400-e29b-41d4-a716-446655440000"`

**Step 3: Commit**

```bash
git add utils.py
git commit -m "feat: add UUID generation utility

Helper function to generate UUIDs for all database records"
```

---

## Task 3: Logger Configuration

**Files:**
- Modify: `logger.py`

**Step 1: Implement logging configuration**

```python
import logging
import sys

def setup_logger():
    """Configure unified logging for FastAPI and Python modules.

    Logs to stdout/stderr for Docker container visibility.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()
```

**Step 2: Test logger**

```bash
python3 -c "from logger import logger; logger.info('Test message')"
```

Expected: Log output with timestamp and message

**Step 3: Commit**

```bash
git add logger.py
git commit -m "feat: add logging configuration

Unified logging to stdout for Docker container visibility"
```

---

## Task 4: Database Models

**Files:**
- Modify: `database_model.py`

**Step 1: Write database models with PeeWee**

```python
from peewee import *
import os

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', '/app/data/wheel_builder.db')
db = SqliteDatabase(DATABASE_PATH)

class BaseModel(Model):
    """Base model with common configuration."""
    class Meta:
        database = db

# Component Library Models

class Hub(BaseModel):
    id = CharField(primary_key=True)
    make = CharField()
    model = CharField()
    type = CharField()  # front or rear
    old = FloatField()  # over locknut distance
    left_flange_diameter = FloatField()
    right_flange_diameter = FloatField()
    left_flange_offset = FloatField()
    right_flange_offset = FloatField()
    spoke_hole_diameter = FloatField()

class Rim(BaseModel):
    id = CharField(primary_key=True)
    make = CharField()
    model = CharField()
    type = CharField()  # symmetric or asymmetric
    erd = FloatField()  # effective rim diameter
    osb = FloatField()  # offset spoke bed
    inner_width = FloatField()
    outer_width = FloatField()
    holes = IntegerField()
    material = CharField()

class Spoke(BaseModel):
    id = CharField(primary_key=True)
    material = CharField()
    gauge = CharField()
    max_tension = FloatField()  # kgf
    length = FloatField()  # mm

class Nipple(BaseModel):
    id = CharField(primary_key=True)
    material = CharField()
    diameter = FloatField()  # mm
    length = FloatField()  # mm
    color = CharField()

# Wheel Build Models

class WheelBuild(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()
    status = CharField(default='draft')  # draft, in_progress, completed
    hub_id = CharField(null=True)
    rim_id = CharField(null=True)
    spoke_id = CharField(null=True)
    nipple_id = CharField(null=True)
    lacing_pattern = CharField(null=True)
    spoke_count = IntegerField(null=True)
    actual_spoke_length_left = FloatField(null=True)
    actual_spoke_length_right = FloatField(null=True)
    comments = TextField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class TensionSession(BaseModel):
    id = CharField(primary_key=True)
    wheel_build_id = CharField()
    session_name = CharField()
    session_date = DateTimeField()
    notes = TextField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class TensionReading(BaseModel):
    id = CharField(primary_key=True)
    tension_session_id = CharField()
    spoke_number = IntegerField()
    side = CharField()  # left or right
    tm_reading = FloatField()  # Park Tool TM-1 reading
    estimated_tension_kgf = FloatField()
    range_status = CharField()  # in_range, over, under
    average_deviation_status = CharField()  # in_range, over, under

def initialize_database():
    """Create tables if they don't exist."""
    db.connect()
    db.create_tables([
        Hub, Rim, Spoke, Nipple,
        WheelBuild, TensionSession, TensionReading
    ], safe=True)
    db.close()
```

**Step 2: Test database initialization**

```bash
python3 -c "from database_model import initialize_database; initialize_database(); print('Database initialized')"
```

Expected: Database file created, no errors

**Step 3: Commit**

```bash
git add database_model.py
git commit -m "feat: add database models with PeeWee ORM

Models for:
- Component library (Hub, Rim, Spoke, Nipple)
- Wheel builds (WheelBuild, TensionSession, TensionReading)
- All IDs are UUIDs (not auto-generated)
- Database initialization function"
```

---

## Task 5: Database Manager - Component CRUD

**Files:**
- Modify: `database_manager.py`

**Step 1: Implement component CRUD operations**

```python
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
```

**Step 2: Test component creation**

```bash
python3 -c "
from database_model import initialize_database, db
from database_manager import create_hub, get_all_hubs
initialize_database()
db.connect()
hub = create_hub('Test', 'Model', 'front', 100, 58, 58, 32, 32, 2.6)
hubs = get_all_hubs()
print(f'Created hub, total hubs: {len(hubs)}')
db.close()
"
```

Expected: "Created hub, total hubs: 1"

**Step 3: Commit**

```bash
git add database_manager.py
git commit -m "feat: add component CRUD operations in database_manager

Operations for Hub, Rim, Spoke, Nipple:
- create, get_all, get_by_id, update, delete
- get_builds_using_X for component locking checks"
```

---

## Task 6: Database Manager - Wheel Build CRUD

**Files:**
- Modify: `database_manager.py`

**Step 1: Add wheel build operations**

```python
# Add to database_manager.py after nipple operations

from datetime import datetime

# Wheel Build operations

def create_wheel_build(name, status='draft', hub_id=None, rim_id=None, spoke_id=None,
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
        spoke_id=spoke_id,
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
```

**Step 2: Test wheel build creation**

```bash
python3 -c "
from database_model import initialize_database, db
from database_manager import create_wheel_build, get_all_wheel_builds
initialize_database()
db.connect()
build = create_wheel_build('Test Build')
builds = get_all_wheel_builds()
print(f'Created build, total builds: {len(builds)}')
db.close()
"
```

Expected: "Created build, total builds: 1"

**Step 3: Commit**

```bash
git add database_manager.py
git commit -m "feat: add wheel build and tension session CRUD

Operations for:
- WheelBuild: create, get_all, get_by_id, update, delete
- TensionSession: create, get_by_build, get_by_id
- TensionReading: create, get_by_session, bulk_create_or_update"
```

---

## Task 7: Seed Data

**Files:**
- Modify: `seed_data.py`

**Step 1: Implement seed data population**

```python
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
        {"material": "Steel", "gauge": "2.0 mm", "max_tension": 120, "length": 282},
        {"material": "Steel", "gauge": "2.0 mm", "max_tension": 120, "length": 286},
        {"material": "Stainless Steel", "gauge": "2.0/1.8/2.0 mm", "max_tension": 130, "length": 282},
        {"material": "Steel", "gauge": "1.8 mm", "max_tension": 100, "length": 282},
        {"material": "Titanium", "gauge": "2.0 mm", "max_tension": 140, "length": 282},
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
```

**Step 2: Run seed script**

```bash
python3 seed_data.py
```

Expected: "Database seeded successfully"

**Step 3: Verify seed data**

```bash
python3 -c "
from database_model import db
from database_manager import get_all_hubs, get_all_rims
db.connect()
print(f'Hubs: {len(get_all_hubs())}, Rims: {len(get_all_rims())}')
db.close()
"
```

Expected: "Hubs: 5, Rims: 5"

**Step 4: Commit**

```bash
git add seed_data.py
git commit -m "feat: add seed data for component library

Populates database with sample:
- 5 hubs (Shimano, DT Swiss, Hope, Phil Wood)
- 5 rims (Ryde, Mavic, DT Swiss, Stan's, H+Son)
- 5 spoke types (various gauges and materials)
- 4 nipple types (brass/aluminum, various sizes)"
```

---

## Task 8: Business Logic - Validation

**Files:**
- Modify: `business_logic.py`

**Step 1: Implement validation functions**

```python
from database_manager import (
    get_hub_by_id, get_rim_by_id, get_spoke_by_id, get_nipple_by_id,
    get_builds_using_hub, get_builds_using_rim, get_builds_using_spoke, get_builds_using_nipple
)
from logger import logger

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
```

**Step 2: Test validation**

```bash
python3 -c "
from database_model import initialize_database, db, WheelBuild
from business_logic import can_calculate_spoke_length
from utils import generate_uuid

initialize_database()
db.connect()

# Create incomplete build
build = WheelBuild.create(id=generate_uuid(), name='Test', status='draft')
can_calc, missing = can_calculate_spoke_length(build)
print(f'Can calculate: {can_calc}, Missing: {missing}')

db.close()
"
```

Expected: "Can calculate: False, Missing: ['hub', 'rim', 'spoke', 'nipple', 'lacing pattern', 'spoke count']"

**Step 3: Commit**

```bash
git add business_logic.py
git commit -m "feat: add validation logic for wheel builds

- can_calculate_spoke_length: checks required fields
- check_component_locked: prevents editing in-use components"
```

---

## Task 9: Business Logic - Spoke Length Calculation

**Files:**
- Modify: `business_logic.py`

**Step 1: Add spoke length calculation (placeholder for formulas)**

```python
# Add to business_logic.py after validation functions

import math

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
```

**Step 2: Test spoke length calculation**

```bash
python3 -c "
from database_model import initialize_database, db
from database_manager import get_all_hubs, get_all_rims, get_all_spokes, get_all_nipples, create_wheel_build
from business_logic import calculate_recommended_spoke_lengths
from seed_data import seed_components

initialize_database()
db.connect()
seed_components()

hubs = get_all_hubs()
rims = get_all_rims()
spokes = get_all_spokes()
nipples = get_all_nipples()

# Create a complete build
build = create_wheel_build(
    name='Test Calculation',
    hub_id=hubs[0].id,
    rim_id=rims[0].id,
    spoke_id=spokes[0].id,
    nipple_id=nipples[0].id,
    lacing_pattern='3-cross',
    spoke_count=36
)

lengths = calculate_recommended_spoke_lengths(build)
print(f'Spoke lengths: Left={lengths[\"left\"]}mm, Right={lengths[\"right\"]}mm')

db.close()
"
```

Expected: Spoke length values (specific numbers will depend on formula)

**Step 3: Commit**

```bash
git add business_logic.py
git commit -m "feat: add spoke length calculation logic

Implements standard spoke length formula
- Handles radial and crossed lacing patterns
- Calculates for left and right sides separately
- Returns None if required data missing"
```

---

## Task 10: Business Logic - Tension Analysis

**Files:**
- Modify: `business_logic.py`

**Step 1: Add tension analysis functions**

```python
# Add to business_logic.py after spoke length calculation

import statistics

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
    gauge_num = float(spoke.gauge.split()[0])  # Extract first number from gauge
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
```

**Step 2: Test tension analysis**

```bash
python3 -c "
from business_logic import calculate_tension_range, analyze_tension_readings
from database_model import Spoke, Rim

spoke = Spoke(material='Steel', gauge='2.0 mm', max_tension=120, length=282)
rim = Rim(material='aluminum', erd=605.4)

tension_range = calculate_tension_range(spoke, rim)
print(f'Tension range: {tension_range}')
"
```

Expected: Dict with min/max tension values

**Step 3: Commit**

```bash
git add business_logic.py
git commit -m "feat: add tension analysis logic

- calculate_tension_range: min/max kgf and TM readings
- analyze_tension_readings: statistics by side
- determine_quality_status: overall wheel quality"
```

---

## Task 11: Basic FastAPI Application

**Files:**
- Modify: `main.py`
- Create: `templates/base.html`

**Step 1: Implement basic FastAPI app**

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database_model import initialize_database, db
from seed_data import seed_components
from logger import logger
import os

app = FastAPI(title="Wheel Builder")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting Wheel Builder application...")
    initialize_database()
    db.connect()
    seed_components()
    logger.info("Application ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    logger.info("Shutting down...")
    db.close()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page showing all wheel builds."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

**Step 2: Create minimal base template**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Wheel Builder{% endblock %}</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">

    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>

    <style>
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --success-color: #27ae60;
            --warning-color: #f39c12;
        }
    </style>

    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-dark" style="background-color: var(--primary-color); box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="bi bi-gear-fill"></i> Wheel Builder
            </a>
            <div>
                <a href="/config" class="btn btn-outline-light btn-sm me-2">
                    <i class="bi bi-tools"></i> Configuration
                </a>
            </div>
        </div>
    </nav>

    {% block content %}{% endblock %}

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <!-- App JS -->
    <script src="/static/js/app.js"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

**Step 3: Create static directory and placeholder app.js**

```bash
mkdir -p static/js static/css
echo "// Wheel Builder JavaScript" > static/js/app.js
```

**Step 4: Test FastAPI app**

```bash
cd /home/xivind/code/wheel-builder/.worktrees/wheel-builder-implementation
uvicorn main:app --host 0.0.0.0 --port 8004 &
sleep 2
curl http://localhost:8004/health
killall uvicorn
```

Expected: {"status":"healthy"}

**Step 5: Commit**

```bash
git add main.py templates/base.html static/
git commit -m "feat: add basic FastAPI application structure

- FastAPI app with startup/shutdown hooks
- Database initialization on startup
- Base Jinja2 template with Bootstrap and HTMX
- Health check endpoint
- Static files directory structure"
```

---

## Task 12: Dashboard Template and Route

**Files:**
- Create: `templates/dashboard.html`
- Modify: `main.py`

**Step 1: Create dashboard template**

```html
{% extends "base.html" %}

{% block title %}My Wheel Builds - Wheel Builder{% endblock %}

{% block content %}
<!-- Page Header -->
<div class="page-header" style="background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white; padding: 2rem 0; margin-bottom: 2rem;">
    <div class="container">
        <h1 class="mb-0"><i class="bi bi-collection"></i> My Wheel Builds</h1>
        <p class="mb-0 mt-2 opacity-75">Track and manage all your wheel building projects</p>
    </div>
</div>

<div class="container pb-5">
    <!-- Stats Overview -->
    <div class="row mb-4">
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card border-0 shadow-sm">
                <div class="card-body text-center">
                    <h3 class="text-primary mb-0">{{ stats.total }}</h3>
                    <small class="text-muted">Total Builds</small>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card border-0 shadow-sm">
                <div class="card-body text-center">
                    <h3 class="text-success mb-0">{{ stats.completed }}</h3>
                    <small class="text-muted">Completed</small>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card border-0 shadow-sm">
                <div class="card-body text-center">
                    <h3 class="text-warning mb-0">{{ stats.in_progress }}</h3>
                    <small class="text-muted">In Progress</small>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-sm-6 mb-3">
            <div class="card border-0 shadow-sm">
                <div class="card-body text-center">
                    <h3 class="text-info mb-0">{{ stats.draft }}</h3>
                    <small class="text-muted">Draft</small>
                </div>
            </div>
        </div>
    </div>

    <!-- Wheel Cards Grid -->
    <div class="row" id="builds-grid">
        {% if builds %}
            {% for build in builds %}
            <div class="col-lg-4 col-md-6 mb-4">
                <div class="card wheel-card" onclick="location.href='/build/{{ build.id }}'" style="cursor: pointer; transition: transform 0.2s; border: none; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div class="card-header" style="background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); color: white; font-weight: 600;">
                        <div class="d-flex justify-content-between align-items-center">
                            <span>{{ build.name }}</span>
                            <span class="badge bg-{% if build.status == 'completed' %}success{% elif build.status == 'in_progress' %}warning text-dark{% else %}secondary{% endif %}">
                                {{ build.status|replace('_', ' ')|title }}
                            </span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="info-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #e9ecef;">
                            <span style="font-weight: 600; color: #6c757d;">Hub</span>
                            <span style="color: var(--primary-color);">{{ build.hub_display or 'Not selected' }}</span>
                        </div>
                        <div class="info-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #e9ecef;">
                            <span style="font-weight: 600; color: #6c757d;">Rim</span>
                            <span style="color: var(--primary-color);">{{ build.rim_display or 'Not selected' }}</span>
                        </div>
                        <div class="info-item" style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #e9ecef;">
                            <span style="font-weight: 600; color: #6c757d;">Spokes</span>
                            <span style="color: var(--primary-color);">{{ build.spoke_count or 'N/A' }} ({{ build.lacing_pattern or 'N/A' }})</span>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <small class="text-muted">
                            <i class="bi bi-calendar3"></i> Updated: {{ build.updated_at.strftime('%b %d, %Y') }}
                        </small>
                    </div>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> No wheel builds yet. Click the + button to create your first build!
                </div>
            </div>
        {% endif %}
    </div>
</div>

<!-- Floating Action Button -->
<button class="fab-button" onclick="alert('Create new build - to be implemented')" style="position: fixed; bottom: 2rem; right: 2rem; width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, var(--secondary-color), var(--success-color)); color: white; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-size: 1.5rem;">
    <i class="bi bi-plus-lg"></i>
</button>

<style>
.wheel-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
}
</style>
{% endblock %}
```

**Step 2: Update dashboard route in main.py**

```python
# Replace dashboard route in main.py

from database_manager import get_all_wheel_builds, get_hub_by_id, get_rim_by_id

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page showing all wheel builds."""
    builds = get_all_wheel_builds()

    # Enrich builds with component info
    for build in builds:
        if build.hub_id:
            hub = get_hub_by_id(build.hub_id)
            build.hub_display = f"{hub.make} {hub.model}" if hub else None
        else:
            build.hub_display = None

        if build.rim_id:
            rim = get_rim_by_id(build.rim_id)
            build.rim_display = f"{rim.make} {rim.model}" if rim else None
        else:
            build.rim_display = None

    # Calculate stats
    stats = {
        'total': len(builds),
        'completed': len([b for b in builds if b.status == 'completed']),
        'in_progress': len([b for b in builds if b.status == 'in_progress']),
        'draft': len([b for b in builds if b.status == 'draft'])
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "builds": builds,
        "stats": stats
    })
```

**Step 3: Test dashboard**

```bash
uvicorn main:app --host 0.0.0.0 --port 8004 &
sleep 2
curl http://localhost:8004/ | grep "My Wheel Builds"
killall uvicorn
```

Expected: HTML containing "My Wheel Builds"

**Step 4: Commit**

```bash
git add templates/dashboard.html main.py
git commit -m "feat: add dashboard template and route

- Dashboard shows all wheel builds as cards
- Stats overview (total, completed, in_progress, draft)
- Displays hub/rim info if selected
- Floating action button for new builds
- Responsive grid layout"
```

---

## Task 13: Create Wheel Build Form and Route

**Files:**
- Create: `templates/partials/build_form.html`
- Modify: `main.py`

**Step 1: Create build form partial**

```html
<div class="modal-dialog modal-lg">
    <div class="modal-content">
        <div class="modal-header" style="background-color: var(--primary-color); color: white;">
            <h5 class="modal-title"><i class="bi bi-plus-circle"></i> Create New Wheel Build</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" style="filter: invert(1);"></button>
        </div>
        <form method="POST" action="/build/create">
            <div class="modal-body">
                <div class="row">
                    <div class="col-12 mb-3">
                        <label for="name" class="form-label">Build Name *</label>
                        <input type="text" class="form-control" id="name" name="name" required placeholder="e.g., Commuter Primary - Rear">
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label for="hub_id" class="form-label">Hub</label>
                        <select class="form-select" id="hub_id" name="hub_id">
                            <option value="">Select hub...</option>
                            {% for hub in hubs %}
                            <option value="{{ hub.id }}">{{ hub.make }} {{ hub.model }} ({{ hub.type }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label for="rim_id" class="form-label">Rim</label>
                        <select class="form-select" id="rim_id" name="rim_id">
                            <option value="">Select rim...</option>
                            {% for rim in rims %}
                            <option value="{{ rim.id }}">{{ rim.make }} {{ rim.model }} ({{ rim.holes }} holes)</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label for="spoke_id" class="form-label">Spoke</label>
                        <select class="form-select" id="spoke_id" name="spoke_id">
                            <option value="">Select spoke...</option>
                            {% for spoke in spokes %}
                            <option value="{{ spoke.id }}">{{ spoke.material }} {{ spoke.gauge }} - {{ spoke.length }}mm</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label for="nipple_id" class="form-label">Nipple</label>
                        <select class="form-select" id="nipple_id" name="nipple_id">
                            <option value="">Select nipple...</option>
                            {% for nipple in nipples %}
                            <option value="{{ nipple.id }}">{{ nipple.material }} {{ nipple.diameter }}mm {{ nipple.color }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label for="lacing_pattern" class="form-label">Lacing Pattern</label>
                        <select class="form-select" id="lacing_pattern" name="lacing_pattern">
                            <option value="">Select pattern...</option>
                            <option value="radial">Radial</option>
                            <option value="1-cross">1-cross</option>
                            <option value="2-cross">2-cross</option>
                            <option value="3-cross">3-cross</option>
                            <option value="4-cross">4-cross</option>
                        </select>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label for="spoke_count" class="form-label">Spoke Count</label>
                        <select class="form-select" id="spoke_count" name="spoke_count">
                            <option value="">Select count...</option>
                            <option value="24">24</option>
                            <option value="28">28</option>
                            <option value="32">32</option>
                            <option value="36">36</option>
                        </select>
                    </div>
                </div>

                <div class="mb-3">
                    <label for="comments" class="form-label">Comments</label>
                    <textarea class="form-control" id="comments" name="comments" rows="3" placeholder="Optional notes about this build..."></textarea>
                </div>

                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> Only the build name is required. You can fill in component details later.
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-lg"></i> Create Build
                </button>
            </div>
        </form>
    </div>
</div>
```

**Step 2: Add routes to main.py**

```python
# Add these imports
from fastapi import Form
from fastapi.responses import RedirectResponse
from database_manager import (
    get_all_hubs, get_all_rims, get_all_spokes, get_all_nipples,
    create_wheel_build
)

# Add routes after dashboard route

@app.get("/partials/build-form", response_class=HTMLResponse)
async def build_form_partial(request: Request):
    """Return build form modal partial for HTMX."""
    hubs = get_all_hubs()
    rims = get_all_rims()
    spokes = get_all_spokes()
    nipples = get_all_nipples()

    return templates.TemplateResponse("partials/build_form.html", {
        "request": request,
        "hubs": hubs,
        "rims": rims,
        "spokes": spokes,
        "nipples": nipples
    })

@app.post("/build/create")
async def create_build(
    name: str = Form(...),
    hub_id: str = Form(None),
    rim_id: str = Form(None),
    spoke_id: str = Form(None),
    nipple_id: str = Form(None),
    lacing_pattern: str = Form(None),
    spoke_count: int = Form(None),
    comments: str = Form(None)
):
    """Create a new wheel build."""
    # Convert empty strings to None
    hub_id = hub_id if hub_id else None
    rim_id = rim_id if rim_id else None
    spoke_id = spoke_id if spoke_id else None
    nipple_id = nipple_id if nipple_id else None
    lacing_pattern = lacing_pattern if lacing_pattern else None
    comments = comments if comments else None

    build = create_wheel_build(
        name=name,
        status='draft',
        hub_id=hub_id,
        rim_id=rim_id,
        spoke_id=spoke_id,
        nipple_id=nipple_id,
        lacing_pattern=lacing_pattern,
        spoke_count=spoke_count,
        comments=comments
    )

    logger.info(f"Created wheel build: {name} (ID: {build.id})")

    return RedirectResponse(url=f"/build/{build.id}", status_code=303)
```

**Step 3: Update dashboard template FAB button**

In `templates/dashboard.html`, replace the FAB button with:

```html
<!-- Floating Action Button -->
<button class="fab-button"
        hx-get="/partials/build-form"
        hx-target="#build-modal-container"
        hx-swap="innerHTML"
        data-bs-toggle="modal"
        data-bs-target="#build-modal"
        style="position: fixed; bottom: 2rem; right: 2rem; width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, var(--secondary-color), var(--success-color)); color: white; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.3); font-size: 1.5rem;">
    <i class="bi bi-plus-lg"></i>
</button>

<!-- Modal Container -->
<div class="modal fade" id="build-modal" tabindex="-1">
    <div id="build-modal-container"></div>
</div>
```

**Step 4: Create partials directory**

```bash
mkdir -p templates/partials
```

**Step 5: Test build creation**

```bash
uvicorn main:app --host 0.0.0.0 --port 8004 &
sleep 2
curl -X POST http://localhost:8004/build/create -d "name=Test Build" -L | grep "Test Build"
killall uvicorn
```

Expected: HTML containing "Test Build"

**Step 6: Commit**

```bash
git add templates/partials/build_form.html templates/dashboard.html main.py
git commit -m "feat: add wheel build creation form and route

- Modal form with all build fields
- Only name is required, other fields optional
- HTMX loads form partial
- POST creates build and redirects to details page
- Form includes all components from library"
```

---

## Continuation Instructions

The plan continues with:
- Task 14: Build Details Page
- Task 15: Configuration Page (Hubs/Rims/Spokes/Nipples)
- Task 16: Component Locking UI
- Task 17: Tension Sessions
- Task 18: Tension Readings Entry
- Task 19: Charts and Visualization
- Task 20: Session Comparison
- Task 21: Docker Build Script
- Task 22: Integration Testing

**Total estimated tasks: ~25**

This plan should be executed using `@superpowers:executing-plans` or `@superpowers:subagent-driven-development`.
