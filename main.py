from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database_model import initialize_database, db
from seed_data import seed_components
from logger import logger
from database_manager import get_all_wheel_builds, get_hub_by_id, get_rim_by_id

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

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}