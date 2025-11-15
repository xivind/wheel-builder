from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database_model import initialize_database, db
from seed_data import seed_components
from logger import logger
from database_manager import get_all_wheel_builds, get_hubs_by_ids, get_rims_by_ids

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
    try:
        builds = get_all_wheel_builds()

        # Batch fetch hubs and rims to avoid N+1 queries
        hub_ids = {b.hub_id for b in builds if b.hub_id}
        rim_ids = {b.rim_id for b in builds if b.rim_id}

        hubs = {h.id: h for h in get_hubs_by_ids(list(hub_ids))} if hub_ids else {}
        rims = {r.id: r for r in get_rims_by_ids(list(rim_ids))} if rim_ids else {}

        # Enrich builds with component info and calculate stats in single pass
        stats = {'total': len(builds), 'completed': 0, 'in_progress': 0, 'draft': 0}

        for build in builds:
            # Enrich with hub info
            if build.hub_id and build.hub_id in hubs:
                hub = hubs[build.hub_id]
                build.hub_display = f"{hub.make} {hub.model}"
            else:
                build.hub_display = None

            # Enrich with rim info
            if build.rim_id and build.rim_id in rims:
                rim = rims[build.rim_id]
                build.rim_display = f"{rim.make} {rim.model}"
            else:
                build.rim_display = None

            # Calculate stats in same pass
            if build.status in stats:
                stats[build.status] += 1

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "builds": builds,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to load dashboard. Please try again later."
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}