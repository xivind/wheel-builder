# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Claude must always read this file.

## Project Overview

Wheel Builder is a self-hosted web application for bicycle wheel builders to select components, calculate spoke lengths, track spoke tension measurements, and visualize build quality over time. It helps wheelbuilders ensure proper spoke tension and maintain comprehensive build records.

## Technology Stack

- **Backend:** FastAPI, Uvicorn, Peewee ORM, SQLite
- **Frontend:** Jinja2 templates, Bootstrap 5, Chart.js, HTMX, Vanilla JavaScript
- **Deployment:** Docker (no docker-compose)
- **Testing:** pytest (if implemented)

## Development Commands

### Deployment

**Using deployment script (recommended):**
```bash
./create-container-wheelbuilder.sh
```

The script handles complete deployment lifecycle:
- Stops and removes existing container
- Removes old image
- Builds fresh image
- Creates container with persistent data volume
- Database stored in `~/code/container_data/wheel_builder.db` (persists across rebuilds)
- Logs stored in `~/code/container_data/logs/wheel_builder.log`

**Manual Docker commands:**
```bash
# Build
docker build -t wheel-builder .

# Run (with data persistence)
mkdir -p ~/code/container_data/logs
docker run -d \
  --name=wheel-builder \
  -e TZ=Europe/Stockholm \
  -v ~/code/container_data:/app/data \
  --restart unless-stopped \
  -p 8004:8004 \
  wheel-builder

# View logs
docker logs -f wheel-builder
# or view log file
tail -f ~/code/container_data/logs/wheel_builder.log

# Stop/Start
docker stop wheel-builder
docker start wheel-builder
```

### Running the App

**Without Docker:**
```bash
# Install dependencies
pip install -r requirements.txt

# Development with hot reload (detects code changes automatically)
# Note: You may see "1 change detected" messages due to log files being written.
# This is harmless - uvicorn detects the changes but doesn't actually reload.
uvicorn main:app --host 0.0.0.0 --port 8004 --reload --log-config uvicorn_log_config.ini

# Development without hot reload (clean console output, manual restart needed)
uvicorn main:app --host 0.0.0.0 --port 8004 --log-config uvicorn_log_config.ini

# Production (same as above, no reload)
uvicorn main:app --host 0.0.0.0 --port 8004 --log-config uvicorn_log_config.ini
```

The application will be available at `http://localhost:8004`

## Architecture

### Strict Layer Separation

This codebase follows a strict three-layer architecture. **Do not violate these boundaries:**

1. **main.py** - Routing layer only
   - FastAPI routes and HTTP handling
   - Template rendering
   - Request/response handling
   - **NO business logic or database operations**

2. **business_logic.py** - Business logic layer
   - All calculations (spoke length, tension analysis, kgf conversions)
   - Data transformation and validation
   - Orchestration between database operations
   - **MUST call database_manager.py for all CRUD operations**
   - **NEVER call Peewee models directly**

3. **database_manager.py** - Data access layer
   - All CRUD operations
   - Direct interaction with Peewee models
   - Component locking logic (components in use cannot be edited/deleted)

### Supporting Modules

- **database_model.py** - Peewee ORM models (7 tables)
- **utils.py** - Helper functions (UUID generation)
- **logger.py** - Standard logging using Python's logging module
- **seed_sample_components.py** - Seeds sample components on first run
- **seed_spoke_types.py** - Loads Park Tool TM-1 conversion table from conversion_table.txt

### Database Models

The application uses UUID strings for all primary keys (generated via `utils.generate_uuid()`). Seven main tables:

**Component Library:**
1. **Hub**: Flange specifications for spoke length calculation
   - Fields: make, model, type (front/rear), OLD, flange diameters, flange offsets, spoke hole diameter, spoke count

2. **Rim**: ERD and drilling specifications
   - Fields: make, model, ERD, spoke holes, material, width, height, weight

3. **Spoke**: Material and tension specs
   - Fields: make, model, material, gauge, max_tension, length, color

4. **Nipple**: Nipple specifications
   - Fields: make, model, material, diameter, length, color

5. **SpokeType**: Spoke type definitions with Park Tool TM-1 conversion metadata
   - Fields: name, material, shape, dimensions
   - Has many: conversion_points

6. **ConversionPoint**: Park Tool TM-1 to kgf conversion data
   - Fields: tm_reading (0-40), kgf_value, spoke_type_id

**Wheel Build & Tension Tracking:**
7. **WheelBuild**: Complete wheel build specification
   - Fields: name, hub_id, rim_id, spoke_id, nipple_id, lacing_pattern, spoke_count, build_date, notes
   - Has many: tension_sessions

8. **TensionSession**: Snapshot of tension measurements at a point in time
   - Fields: name, session_date, notes, build_id
   - Has many: tension_readings

9. **TensionReading**: Individual spoke tension measurement
   - Fields: spoke_position, side (left/right), tm_reading, kgf_value, session_id

### Frontend Organization

- `templates/base.html`: Base template with Bootstrap 5, Chart.js, HTMX, navbar
- `templates/dashboard.html`: All wheel builds in card grid layout
- `templates/build_details.html`: Individual build with spoke length calculation, tension sessions, radar charts
- `templates/config.html`: Manage component library (tabs for hubs, rims, spokes, nipples)
- `templates/error.html`: Error page for exceptions
- `templates/partials/`: HTMX partials for forms and components
- `static/js/app.js`: Form handling, radar charts, tab state management
- `static/css/styles.css`: Custom styling and color-coded status indicators

### Logging

Unified logging configuration for both FastAPI/uvicorn and application logs:
- Format: `YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE`
- Configured in `uvicorn_log_config.ini`
- Dual output: stdout + file (`~/code/container_data/logs/wheel_builder.log`)
- Application-level log rotation (3 files × 10KB each)
- All loggers use `logging.getLogger(__name__)`
- **No custom logger.py module** - uses standard Python logging

**Important:** Always run uvicorn with `--log-config uvicorn_log_config.ini` for consistent formatting.

## Key Features

### Spoke Length Calculation

Automatic calculation of recommended spoke lengths based on hub, rim, and lacing pattern:

**Formula:**
```python
spoke_length = sqrt(
    (rim_radius - flange_radius * cos(spoke_angle))^2 +
    (flange_offset)^2 +
    (flange_radius * sin(spoke_angle))^2
) - nipple_length
```

**Implementation:**
- `business_logic.py::calculate_spoke_length()`: Core calculation function
- `business_logic.py::can_calculate_spoke_length()`: Validates required data is present
- Returns separate lengths for left and right sides (due to asymmetric hub flanges)
- Displayed in build details page when all required components are selected

### Tension Tracking System

Multi-session tension tracking with Park Tool TM-1 integration:

**Workflow:**
1. Create tension session for a build (e.g., "Initial Build", "After First True")
2. Enter Park Tool TM-1 readings for each spoke position
3. System converts TM-1 readings to kgf using spoke type conversion table
4. Calculates statistics (average, std dev, min, max) per side
5. Determines quality status based on tension range and deviation

**Quality Status Logic:**
- **Well Balanced**: Std dev < 5% of average, all spokes within recommended range
- **Needs Truing**: Std dev 5-10% of average
- **Uneven Tension**: Std dev > 10% of average
- **Over/Under Tension**: Spokes outside recommended range

**Implementation:**
- `business_logic.py::analyze_tension_readings()`: Quality analysis
- `business_logic.py::tm_reading_to_kgf()`: TM-1 to kgf conversion
- `database_manager.py::bulk_create_or_update_readings()`: Efficient batch updates
- Radar charts visualize tension distribution around the wheel

### Component Locking

Components in use by wheel builds are automatically locked:
- Locked components cannot be edited or deleted
- Preserves build history integrity
- UI shows lock icon and disables edit/delete buttons
- Implemented via `get_builds_using_*()` functions in database_manager.py

### Park Tool TM-1 Conversion System

Comprehensive spoke type definitions with tension meter calibration:

**Conversion Table:**
- Loaded from `conversion_table.txt` (tab-separated format)
- Maps Park Tool TM-1 readings (0-40) to kgf values
- Different spoke types have different calibration curves
- Spoke types: Steel Round (1.8mm, 2.0mm, 2.3mm), Steel Bladed (2.0mm), Aluminum Round (2.1mm)

**Implementation:**
- `seed_spoke_types.py`: Parses conversion table and populates database
- `database_model.py`: SpokeType and ConversionPoint models
- `business_logic.py::tm_reading_to_kgf()`: Lookup function with linear interpolation

## Database Management

### Location

- **Development (local):** `~/code/container_data/wheel_builder.db` (via symlink from `./data`)
- **Production (Docker):** `~/code/container_data/wheel_builder.db`
  - Persisted via volume mount `-v ~/code/container_data:/app/data`
  - Survives container rebuilds and updates
- **Logs:** `~/code/container_data/logs/wheel_builder.log`

### Initialization

- Tables created automatically on first run via `initialize_database()`
- Sample components populated by `seed_components()` in main.py startup
- Spoke types and conversion table loaded by `seed_spoke_types.py`

### Backup

```bash
# Use the provided backup script
./backup_db.sh

# Manual backup
cp ~/code/container_data/wheel_builder.db ~/backup/wheel_builder_$(date +%Y%m%d).db
```

### Health Check

The application includes Docker-based health monitoring:
- Docker HEALTHCHECK uses curl to test the HTTP endpoint every 10 minutes
- Tests that the application is responding to requests (returns HTTP 200)
- Container is marked unhealthy if endpoint fails to respond
- Command: `curl -sSf -o /dev/null -w "%{http_code}" http://127.0.0.1:8004 || exit 1`

## Important Constraints

- **Always use UUID for new records** - Call `utils.generate_uuid()`, never rely on auto-increment
- **Component locking is mandatory** - Never allow deletion/editing of components in use
- **TM-1 readings are integers 0-40** - Validate input range
- **Spoke positions start at 1** - Not zero-indexed
- **Sessions require a build_id** - Cannot exist independently
- **Tension readings require spoke type** - For kgf conversion
- **Spoke length requires all components** - Hub, rim, spoke count, and lacing pattern

## Common Patterns

### Adding a Component

1. User submits form with component specifications
2. `main.py` route receives form data
3. Calls `database_manager.create_*()` function
4. Redirects back to config page with success message

### Creating a Wheel Build

1. User fills out build form (name + optional components)
2. `main.py::create_build_route()` receives form data
3. Calls `database_manager.create_wheel_build()`
4. Redirects to build details page
5. User can progressively fill in components later

### Editing Component Selection

1. Build details page shows edit form for each component type
2. User selects new component from dropdown
3. HTMX POST updates component association
4. Page section refreshes to show new component details
5. Spoke length recalculated if all required data present

### Recording Tension Measurements

1. Create tension session from build details page
2. Enter TM-1 readings for each spoke position (left and right sides)
3. System converts to kgf using spoke type conversion table
4. `database_manager.bulk_create_or_update_readings()` saves all readings
5. Statistics and quality analysis displayed
6. Radar chart visualizes tension distribution

## Key Design Decisions

1. **Single-user per instance**: No authentication, simpler deployment
2. **SQLite**: Lightweight, file-based, easy backup
3. **Component locking**: Preserve build history integrity
4. **Multi-session tracking**: Track tension changes over time (initial, after truing, after riding)
5. **Park Tool TM-1 integration**: Industry-standard tension meter calibration
6. **UUID primary keys**: Robust unique identifiers
7. **Progressive build creation**: Allow partial builds, fill in details later
8. **Separate spoke lengths**: Left and right calculated independently (asymmetric hubs)
9. **HTMX for component updates**: Partial page updates without full reload
10. **Radar charts**: Visual representation of tension distribution
11. **Standard Python logging**: No custom logger.py, uses logging.getLogger(__name__)
12. **Dual log output**: Both stdout and rotating file for flexibility
13. **Data directory symlink**: Local and Docker share same database location

## Worktree Configuration

Worktrees should be created in `.worktrees/` (already in .gitignore).

## Testing

When testing spoke length calculations:
- Use known good hub/rim combinations
- Verify left and right lengths are calculated separately
- Check results against online calculators (e.g., Spocalc, Edd)
- Typical spoke lengths: 250-310mm for road bikes, 260-295mm for MTB

When testing tension tracking:
- Verify TM-1 to kgf conversion matches Park Tool tables
- Check quality status thresholds (5% and 10% std dev)
- Ensure radar chart displays correctly with different spoke counts (28, 32, 36)
- Test edge cases: no readings, single reading, all identical readings
