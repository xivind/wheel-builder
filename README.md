# Wheel Builder

A self-hosted web application to help bicycle wheel builders select components, calculate spoke lengths, track tension measurements, and visualize build quality over time.

![Gas Gauge Logo](static/img/wheelbuilder.png)

## Features

- **Component Library Management**: Add, edit, and manage hubs, rims, spokes, and nipples with automatic locking to preserve build history
- **Wheel Build Tracking**: Create and manage wheel builds with comprehensive component specifications
- **Spoke Length Calculation**: Automatic calculation of recommended spoke lengths based on hub, rim, and lacing pattern
- **Tension Tracking**: Record and track spoke tension measurements across multiple sessions
- **Quality Analysis**: Automatic analysis of tension readings with range and deviation status
- **Visual Charts**: Interactive radar charts showing tension distribution around the wheel
- **Session Comparison**: Track tension changes over time (initial build, after truing, after riding)
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Docker Deployment**: Easy deployment with persistent data storage

## Quick Start

### Prerequisites

- Docker installed on your system
- Docker running

### Deployment

1. Clone the repository:
```bash
git clone <repository-url>
cd wheel-builder
```

2. Run the deployment script:
```bash
chmod +x create-container-wheelbuilder.sh
./create-container-wheelbuilder.sh
```

3. Access the application at `http://localhost:8004`

The application will be running in a Docker container named `wheel-builder` with data persisted to `~/code/container_data/wheel_builder.db`.

### Useful Docker Commands

```bash
# View logs
docker logs wheel-builder

# Stop the container
docker stop wheel-builder

# Start the container
docker start wheel-builder

# Restart the container
docker restart wheel-builder

# Remove the container (data persists in ~/code/container_data)
docker rm wheel-builder
```

## Usage Guide

### 1. Component Library

Navigate to **Configuration** (top right) to manage your component library:

- **Hubs**: Add hub specifications (make, model, flange dimensions, etc.)
- **Rims**: Add rim specifications (make, model, ERD, spoke holes, etc.)
- **Spokes**: Add spoke specifications (material, gauge, max tension, length)
- **Nipples**: Add nipple specifications (material, diameter, length, color)

The application comes pre-seeded with sample components. Components in use by builds are locked and cannot be edited or deleted.

### 2. Create a Wheel Build

1. Click the **+ button** on the dashboard
2. Enter a build name (required)
3. Optionally select components (hub, rim, spoke, nipple, lacing pattern, spoke count)
4. Click **Create Build**

You can fill in component details later or progressively as you plan your build.

### 3. View Build Details

Click on any build card to view details:

- Build information and status
- Component specifications
- Spoke length recommendations (calculated automatically when all required data is present)
- Tension tracking sessions
- Quality indicators

### 4. Track Tension

1. On the build details page, click **Add Session**
2. Enter a session name (e.g., "Initial Build", "After First True", "After 500km")
3. Select or enter the session date
4. Add optional notes
5. Click **Create Session**

### 5. Record Tension Readings

1. Select a tension session from the dropdown
2. Enter Park Tool TM-1 readings for each spoke (left and right sides)
3. Click **Save Readings**

The application automatically:
- Converts TM-1 readings to kgf based on spoke gauge
- Calculates statistics (average, std deviation, min, max) for each side
- Determines range status (in range, over, under)
- Identifies quality issues (uneven tension, needs truing, etc.)
- Visualizes tension distribution in radar charts

### 6. Analyze Build Quality

After entering tension readings, view:

- **Statistics**: Average, standard deviation, min, and max tension per side
- **Quality Status**: Overall wheel quality (Well Balanced, Needs Truing, Uneven Tension)
- **Radar Chart**: Visual representation of tension distribution around the wheel
- **Status Indicators**: Color-coded badges showing which spokes are outside recommended range

## Technology Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite with PeeWee ORM
- **Frontend**: Bootstrap 5, HTMX, Jinja2 templates
- **JavaScript**: Vanilla JS (Chart.js for visualizations)
- **Deployment**: Docker with persistent data volume

## Architecture

The application follows a strict 3-layer architecture:

- **main.py**: Routing layer (FastAPI routes, request/response handling)
- **business_logic.py**: Calculation and orchestration (spoke length, tension analysis, validation)
- **database_manager.py**: Data access layer (all CRUD operations)
- **database_model.py**: ORM models (PeeWee model definitions)
- **utils.py**: Helper functions (UUID generation, etc.)
- **logger.py**: Logging configuration

## Data Persistence

- Database location: `~/code/container_data/wheel_builder.db` (both Docker and local development)
- Automatically created on first run with directory creation
- Survives container restarts and rebuilds
- Seed data added automatically if database is new
- Can be overridden with `DATABASE_PATH` environment variable

## Logging

- Logs are written to **both stdout and file**
- Log format: `YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE`
- Includes uvicorn, access, and application logs
- **File location**: `~/code/container_data/logs/wheel_builder.log` (persisted on host)
- **Log rotation**: Application-level RotatingFileHandler (max 3 files × 10KB each)

To view logs:
```bash
# Docker logs (stdout)
docker logs wheel-builder
docker logs -f wheel-builder  # Follow in real-time

# Log file (persisted)
tail -f ~/code/container_data/logs/wheel_builder.log
cat ~/code/container_data/logs/wheel_builder.log

# Backup log files (rotated)
ls -lh ~/code/container_data/logs/
```

For local development, logs appear in both the console and `~/code/container_data/logs/wheel_builder.log`.

## Backup

Use the provided backup script:
```bash
./backup_db.sh
```

Or manually backup your data:
```bash
cp ~/code/container_data/wheel_builder.db ~/backup/wheel_builder_$(date +%Y%m%d).db
```

To restore from backup:
```bash
docker stop wheel-builder
cp ~/backup/wheel_builder_20250115.db ~/code/container_data/wheel_builder.db
docker start wheel-builder
```

## Development

### Local Development (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8004 --reload --log-config uvicorn_log_config.ini
```

The database will be automatically created at `~/code/container_data/wheel_builder.db` (same location as Docker).

3. Access at `http://localhost:8004`

To use a different database location:
```bash
DATABASE_PATH=/path/to/custom.db uvicorn main:app --host 0.0.0.0 --port 8004 --reload --log-config uvicorn_log_config.ini
```

### Project Structure

```
wheel-builder/
├── main.py                      # FastAPI routes
├── business_logic.py            # Calculations and logic
├── database_manager.py          # Database operations
├── database_model.py            # ORM models
├── utils.py                     # Helper functions
├── logger.py                    # Logging config
├── seed_data.py                 # Sample data population
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image definition
├── create-container-wheelbuilder.sh  # Deployment script
├── static/
│   └── js/
│       └── app.js              # JavaScript functionality
└── templates/
    ├── base.html               # Base template
    ├── dashboard.html          # Dashboard page
    ├── build_details.html      # Build details page
    ├── config.html             # Configuration page
    ├── error.html              # Error page
    └── partials/               # HTMX partials
        ├── build_form.html
        ├── hub_form.html
        ├── rim_form.html
        ├── spoke_form.html
        ├── nipple_form.html
        └── tension_session_form.html
```

## License

[Add your license here]

## Credits

Developed for bicycle wheel builders who want to track their builds and ensure proper spoke tension.
