from typing import Optional
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database_model import initialize_database, db
from seed_data import seed_components
from logger import logger
from database_manager import (
    get_all_wheel_builds, get_hubs_by_ids, get_rims_by_ids,
    get_all_hubs, get_all_rims, get_all_spokes, get_all_nipples,
    create_wheel_build, get_wheel_build_by_id, get_hub_by_id,
    get_rim_by_id, get_spoke_by_id, get_nipple_by_id,
    update_wheel_build, delete_wheel_build
)
from business_logic import can_calculate_spoke_length, calculate_spoke_length

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

@app.get("/partials/build-form", response_class=HTMLResponse)
async def build_form_partial(request: Request):
    """Return build form modal partial for HTMX."""
    try:
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
    except Exception as e:
        logger.error(f"Error loading build form: {e}")
        return HTMLResponse("<div class='alert alert-danger'>Unable to load form. Please try again later.</div>", status_code=500)

@app.post("/build/create")
async def create_build(
    request: Request,
    name: str = Form(...),
    hub_id: str = Form(None),
    rim_id: str = Form(None),
    spoke_id: str = Form(None),
    nipple_id: str = Form(None),
    lacing_pattern: str = Form(None),
    spoke_count: Optional[int] = Form(None),
    comments: str = Form(None)
):
    """Create a new wheel build."""
    try:
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
    except Exception as e:
        logger.error(f"Error creating wheel build: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to create wheel build. Please try again later."
        }, status_code=500)

@app.post("/build/{build_id}/status")
async def update_build_status(build_id: str, status: str = Form(...)):
    """Update build status."""
    try:
        success = update_wheel_build(build_id, status=status)
        if not success:
            logger.warning(f"Failed to update status for build {build_id}")

        return RedirectResponse(url=f"/build/{build_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error updating build status: {e}")
        return RedirectResponse(url=f"/build/{build_id}", status_code=303)

@app.post("/build/{build_id}/delete")
async def delete_build(build_id: str):
    """Delete a wheel build."""
    try:
        delete_wheel_build(build_id)
        logger.info(f"Deleted build: {build_id}")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting build: {e}")
        return RedirectResponse(url="/", status_code=303)

@app.get("/build/{build_id}", response_class=HTMLResponse)
async def build_details(request: Request, build_id: str):
    """Build details page showing full build information."""
    try:
        # Fetch the build
        build = get_wheel_build_by_id(build_id)
        if not build:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Build not found."
            }, status_code=404)

        # Fetch related components
        hub = get_hub_by_id(build.hub_id) if build.hub_id else None
        rim = get_rim_by_id(build.rim_id) if build.rim_id else None
        spoke = get_spoke_by_id(build.spoke_id) if build.spoke_id else None
        nipple = get_nipple_by_id(build.nipple_id) if build.nipple_id else None

        # Check if we can calculate spoke length
        can_calc, missing = can_calculate_spoke_length(build)

        calculated_left = None
        calculated_right = None

        if can_calc:
            # Calculate spoke lengths for both sides
            calculated_left = calculate_spoke_length(
                hub, rim, spoke, nipple,
                build.spoke_count,
                build.lacing_pattern,
                "left"
            )
            calculated_right = calculate_spoke_length(
                hub, rim, spoke, nipple,
                build.spoke_count,
                build.lacing_pattern,
                "right"
            )

        return templates.TemplateResponse("build_details.html", {
            "request": request,
            "build": build,
            "hub": hub,
            "rim": rim,
            "spoke": spoke,
            "nipple": nipple,
            "can_calculate": can_calc,
            "missing_data": missing,
            "calculated_left": calculated_left,
            "calculated_right": calculated_right
        })
    except Exception as e:
        logger.error(f"Error loading build details: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to load build details. Please try again later."
        }, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}