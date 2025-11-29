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
    update_wheel_build, delete_wheel_build,
    create_hub, create_rim, create_spoke, create_nipple,
    delete_hub, delete_rim, delete_spoke, delete_nipple,
    update_hub, update_rim, update_spoke, update_nipple,
    get_builds_using_hub, get_builds_using_rim,
    get_builds_using_spoke, get_builds_using_nipple,
    get_sessions_by_build, get_tension_session_by_id, create_tension_session,
    get_readings_by_session, bulk_create_or_update_readings, upsert_tension_reading,
    delete_tension_reading, get_all_spoke_types, get_spoke_type_by_id
)
from business_logic import (
    can_calculate_spoke_length, calculate_spoke_length,
    analyze_tension_readings, calculate_tension_range,
    determine_quality_status, tm_reading_to_kgf
)
from datetime import datetime

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
async def build_form_partial(request: Request, id: str = None):
    """Return build form modal partial for HTMX."""
    try:
        build = None
        if id:
            build = get_wheel_build_by_id(id)
            if not build:
                return HTMLResponse("<div class='alert alert-danger'>Build not found.</div>", status_code=404)

        hubs = get_all_hubs()
        rims = get_all_rims()
        spokes = get_all_spokes()
        nipples = get_all_nipples()

        return templates.TemplateResponse("partials/build_form.html", {
            "request": request,
            "build": build,
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
    spoke_left_id: str = Form(None),
    spoke_right_id: str = Form(None),
    nipple_id: str = Form(None),
    lacing_pattern: str = Form(None),
    comments: str = Form(None)
):
    """Create a new wheel build."""
    try:
        # Convert empty strings to None
        hub_id = hub_id if hub_id else None
        rim_id = rim_id if rim_id else None
        spoke_left_id = spoke_left_id if spoke_left_id else None
        spoke_right_id = spoke_right_id if spoke_right_id else None
        nipple_id = nipple_id if nipple_id else None
        lacing_pattern = lacing_pattern if lacing_pattern else None
        comments = comments if comments else None

        # Auto-compute spoke_count from rim if rim is selected
        spoke_count = None
        if rim_id:
            rim = get_rim_by_id(rim_id)
            if rim:
                spoke_count = rim.holes

        # Validate spoke count matches between hub and rim if both are set
        if hub_id and rim_id:
            hub = get_hub_by_id(hub_id)
            rim = get_rim_by_id(rim_id)

            if hub and hub.number_of_spokes and rim and rim.holes:
                if hub.number_of_spokes != rim.holes:
                    return templates.TemplateResponse("error.html", {
                        "request": request,
                        "error_message": f"Spoke count mismatch: Hub has {hub.number_of_spokes} holes, but rim has {rim.holes} holes. These must match."
                    }, status_code=400)

        build = create_wheel_build(
            name=name,
            status='draft',
            hub_id=hub_id,
            rim_id=rim_id,
            spoke_left_id=spoke_left_id,
            spoke_right_id=spoke_right_id,
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
async def build_details(request: Request, build_id: str, session: str = None):
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
        spoke_left = get_spoke_by_id(build.spoke_left_id) if build.spoke_left_id else None
        spoke_right = get_spoke_by_id(build.spoke_right_id) if build.spoke_right_id else None
        nipple = get_nipple_by_id(build.nipple_id) if build.nipple_id else None

        # Check if we can calculate spoke length
        can_calc, missing = can_calculate_spoke_length(build)

        calculated_left = None
        calculated_right = None

        if can_calc:
            # Calculate spoke lengths for both sides
            calculated_left = calculate_spoke_length(
                hub, rim, nipple,
                build.spoke_count,
                build.lacing_pattern,
                "left"
            )
            calculated_right = calculate_spoke_length(
                hub, rim, nipple,
                build.spoke_count,
                build.lacing_pattern,
                "right"
            )

        # Calculate tension range if spoke and rim are available
        tension_range = None
        spoke_for_tension = spoke_left or spoke_right
        if spoke_for_tension and rim:
            tension_range = calculate_tension_range(spoke_left, spoke_right, rim)

        # Fetch tension sessions for this build
        sessions = get_sessions_by_build(build_id)

        # If a specific session is requested, fetch it
        selected_session = None
        readings_left = {}
        readings_right = {}
        stats_left = None
        stats_right = None
        quality_status = None

        if session:
            selected_session = get_tension_session_by_id(session)
            # Verify session belongs to this build
            if selected_session and selected_session.wheel_build_id != build_id:
                selected_session = None

            # If valid session, fetch and analyze readings
            if selected_session:
                readings = get_readings_by_session(selected_session.id)

                # Organize readings by side and spoke number
                for reading in readings:
                    reading_data = {
                        'tm_reading': reading.tm_reading,
                        'kgf': reading.estimated_tension_kgf,
                        'range_status': reading.range_status,
                        'avg_deviation_status': reading.average_deviation_status
                    }

                    if reading.side == 'left':
                        readings_left[reading.spoke_number] = reading_data
                    else:
                        readings_right[reading.spoke_number] = reading_data

                # Calculate statistics and quality status if we have readings
                if readings and spoke_for_tension and rim:
                    tension_range = calculate_tension_range(spoke_left, spoke_right, rim)
                    analysis = analyze_tension_readings(readings, tension_range)

                    stats_left = analysis['left']
                    stats_right = analysis['right']

                    quality_status = determine_quality_status(analysis, tension_range)

        return templates.TemplateResponse("build_details.html", {
            "request": request,
            "build": build,
            "hub": hub,
            "rim": rim,
            "spoke_left": spoke_left,
            "spoke_right": spoke_right,
            "nipple": nipple,
            "can_calculate": can_calc,
            "missing_data": missing,
            "calculated_left": calculated_left,
            "calculated_right": calculated_right,
            "sessions": sessions,
            "selected_session": selected_session,
            "readings_left": readings_left,
            "readings_right": readings_right,
            "stats_left": stats_left,
            "stats_right": stats_right,
            "quality_status": quality_status,
            "tension_range": tension_range
        })
    except Exception as e:
        logger.error(f"Error loading build details: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to load build details. Please try again later."
        }, status_code=500)

@app.get("/build/{build_id}/edit", response_class=HTMLResponse)
async def edit_build_form(request: Request, build_id: str):
    """Display build edit form."""
    try:
        build = get_wheel_build_by_id(build_id)
        if not build:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Build not found."
            }, status_code=404)

        # Get all components for dropdowns
        hubs = get_all_hubs()
        rims = get_all_rims()
        spokes = get_all_spokes()
        nipples = get_all_nipples()

        return templates.TemplateResponse("build_edit.html", {
            "request": request,
            "build": build,
            "hubs": hubs,
            "rims": rims,
            "spokes": spokes,
            "nipples": nipples
        })
    except Exception as e:
        logger.error(f"Error loading build edit form: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to load build edit form. Please try again later."
        }, status_code=500)

@app.post("/build/{build_id}/update")
async def update_build_route(
    request: Request,
    build_id: str,
    name: str = Form(...),
    hub_id: Optional[str] = Form(None),
    rim_id: Optional[str] = Form(None),
    spoke_left_id: Optional[str] = Form(None),
    spoke_right_id: Optional[str] = Form(None),
    nipple_id: Optional[str] = Form(None),
    lacing_pattern: Optional[str] = Form(None),
    comments: Optional[str] = Form(None),
    status: Optional[str] = Form("draft")
):
    """Handle build update."""
    try:
        # Convert empty strings to None
        hub_id = hub_id if hub_id else None
        rim_id = rim_id if rim_id else None
        spoke_left_id = spoke_left_id if spoke_left_id else None
        spoke_right_id = spoke_right_id if spoke_right_id else None
        nipple_id = nipple_id if nipple_id else None
        lacing_pattern = lacing_pattern if lacing_pattern else None
        comments = comments if comments else None

        # Auto-compute spoke_count from rim if rim is selected
        spoke_count = None
        if rim_id:
            rim = get_rim_by_id(rim_id)
            if rim:
                spoke_count = rim.holes

        # Validate spoke count matches between hub and rim if both are set
        if hub_id and rim_id:
            hub = get_hub_by_id(hub_id)
            rim = get_rim_by_id(rim_id)

            if hub and hub.number_of_spokes and rim and rim.holes:
                if hub.number_of_spokes != rim.holes:
                    return templates.TemplateResponse("error.html", {
                        "request": request,
                        "error_message": f"Spoke count mismatch: Hub has {hub.number_of_spokes} holes, but rim has {rim.holes} holes. These must match."
                    }, status_code=400)

        success = update_wheel_build(
            build_id=build_id,
            name=name,
            hub_id=hub_id,
            rim_id=rim_id,
            spoke_left_id=spoke_left_id,
            spoke_right_id=spoke_right_id,
            nipple_id=nipple_id,
            lacing_pattern=lacing_pattern,
            spoke_count=spoke_count,
            comments=comments,
            status=status
        )

        if success:
            logger.info(f"Updated build: {build_id}")
            return RedirectResponse(url=f"/build/{build_id}", status_code=303)
        else:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Failed to update build. Please try again."
            }, status_code=500)
    except Exception as e:
        logger.error(f"Error updating build: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Error updating build: {str(e)}"
        }, status_code=500)

@app.get("/api/calculate-spoke-length")
async def calculate_spoke_length_api(
    hub_id: str,
    rim_id: str,
    nipple_id: str,
    lacing_pattern: str
):
    """Calculate recommended spoke lengths based on hub, rim, nipple, and lacing pattern.

    Returns JSON with left and right spoke lengths and spoke count.
    """
    try:
        # Get components
        hub = get_hub_by_id(hub_id)
        rim = get_rim_by_id(rim_id)
        nipple = get_nipple_by_id(nipple_id)

        if not hub or not rim or not nipple:
            return {"error": "One or more components not found"}

        # Spoke count is determined by rim holes
        spoke_count = rim.holes

        # Calculate lengths for both sides
        left_length = calculate_spoke_length(
            hub, rim, nipple, spoke_count, lacing_pattern, "left"
        )
        right_length = calculate_spoke_length(
            hub, rim, nipple, spoke_count, lacing_pattern, "right"
        )

        return {
            "left_length": left_length,
            "right_length": right_length,
            "spoke_count": spoke_count
        }
    except Exception as e:
        logger.error(f"Error calculating spoke length: {e}")
        return {"error": str(e)}

@app.get("/partials/tension-session-form", response_class=HTMLResponse)
async def tension_session_form_partial(request: Request, build_id: str):
    """Return tension session form modal partial for HTMX."""
    try:
        # Verify the build exists
        build = get_wheel_build_by_id(build_id)
        if not build:
            return HTMLResponse("<div class='alert alert-danger'>Build not found.</div>", status_code=404)

        # Get today's date in YYYY-MM-DD format
        today_date = datetime.now().strftime('%Y-%m-%d')

        return templates.TemplateResponse("partials/tension_session_form.html", {
            "request": request,
            "build_id": build_id,
            "today_date": today_date
        })
    except Exception as e:
        logger.error(f"Error loading tension session form: {e}")
        return HTMLResponse("<div class='alert alert-danger'>Unable to load form. Please try again later.</div>", status_code=500)

@app.post("/build/{build_id}/session/create")
async def create_session_route(
    request: Request,
    build_id: str,
    session_name: str = Form(...),
    session_date: str = Form(...),
    notes: str = Form(None)
):
    """Create a new tension session for a build."""
    try:
        # Verify the build exists
        build = get_wheel_build_by_id(build_id)
        if not build:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Build not found."
            }, status_code=404)

        # Convert date string to datetime object
        try:
            session_date_obj = datetime.strptime(session_date, '%Y-%m-%d')
        except ValueError:
            logger.error(f"Invalid date format: {session_date}")
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Invalid date format."
            }, status_code=400)

        # Convert empty notes to None
        notes = notes if notes else None

        # Create the tension session
        session = create_tension_session(
            wheel_build_id=build_id,
            session_name=session_name,
            session_date=session_date_obj,
            notes=notes
        )

        logger.info(f"Created tension session: {session_name} for build {build_id} (ID: {session.id})")

        # Redirect to build details with the new session selected, maintaining scroll position
        return RedirectResponse(url=f"/build/{build_id}?session={session.id}#tension-tracking", status_code=303)
    except Exception as e:
        logger.error(f"Error creating tension session: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to create tension session. Please try again later."
        }, status_code=500)

@app.post("/build/{build_id}/session/{session_id}/delete")
async def delete_session_route(
    request: Request,
    build_id: str,
    session_id: str
):
    """Delete a tension session and all its readings."""
    try:
        from database_manager import delete_tension_session

        # Verify the build exists
        build = get_wheel_build_by_id(build_id)
        if not build:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Build not found."
            }, status_code=404)

        # Verify the session exists and belongs to this build
        session = get_tension_session_by_id(session_id)
        if not session or session.wheel_build_id != build_id:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Session not found."
            }, status_code=404)

        # Delete the session
        if delete_tension_session(session_id):
            logger.info(f"Deleted tension session {session_id} from build {build_id}")
            # Redirect back to build details, staying in the tension tracking section
            return RedirectResponse(url=f"/build/{build_id}#tension-tracking", status_code=303)
        else:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Failed to delete session."
            }, status_code=500)
    except Exception as e:
        logger.error(f"Error deleting tension session: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to delete tension session. Please try again later."
        }, status_code=500)

@app.post("/build/{build_id}/session/{session_id}/readings")
async def save_tension_readings(
    request: Request,
    build_id: str,
    session_id: str
):
    """Save tension readings for a session."""
    try:
        # Verify the build and session exist
        build = get_wheel_build_by_id(build_id)
        if not build:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Build not found."
            }, status_code=404)

        session = get_tension_session_by_id(session_id)
        if not session or session.wheel_build_id != build_id:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Session not found."
            }, status_code=404)

        # Get spoke and rim for tension calculations
        # Use spoke_left if available, otherwise spoke_right (for tension range calculation)
        spoke_left = get_spoke_by_id(build.spoke_left_id) if build.spoke_left_id else None
        spoke_right = get_spoke_by_id(build.spoke_right_id) if build.spoke_right_id else None
        spoke_for_tension = spoke_left or spoke_right
        rim = get_rim_by_id(build.rim_id) if build.rim_id else None

        if not spoke_for_tension or not rim:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Build missing spoke or rim configuration."
            }, status_code=400)

        # Parse form data
        form_data = await request.form()

        # Calculate tension range
        tension_range = calculate_tension_range(spoke_left, spoke_right, rim)

        # Collect all readings data
        readings_data = []
        all_readings_for_stats = []

        # First pass: collect all readings and convert to kgf
        for key, value in form_data.items():
            if not key.startswith('tm_') or not value:
                continue

            # Parse field name: tm_{spoke_number}_{side}
            parts = key.split('_')
            if len(parts) != 3:
                continue

            spoke_number = int(parts[1])
            side = parts[2]  # 'left' or 'right'
            tm_reading = float(value)

            # Convert to kgf using side-specific spoke type
            spoke_for_conversion = spoke_left if side == 'left' else spoke_right
            if not spoke_for_conversion:
                spoke_for_conversion = spoke_for_tension  # Fallback if one side is missing
            conversion_result = tm_reading_to_kgf(tm_reading, spoke_for_conversion.spoke_type_id)

            # Handle conversion status
            if conversion_result['status'] in ['below_table', 'above_table']:
                # Out of range - save NULL for kgf
                estimated_tension_kgf = None
                range_status = conversion_result['status']
                average_deviation_status = 'unknown'
            else:
                # Valid conversion
                estimated_tension_kgf = conversion_result['kgf']

                # Determine side-specific max tension
                if tension_range.get('different_spoke_types'):
                    # Use side-specific max when different spoke types are used
                    max_kgf = tension_range['left_max_kgf'] if side == 'left' else tension_range['right_max_kgf']
                else:
                    # Use common max when same spoke type on both sides
                    max_kgf = tension_range['max_kgf']

                # Calculate range status using side-specific max
                if estimated_tension_kgf < tension_range['min_kgf']:
                    range_status = 'under'
                elif estimated_tension_kgf > max_kgf:
                    range_status = 'over'
                else:
                    range_status = 'in_range'

                # average_deviation_status will be updated in second pass
                average_deviation_status = 'in_range'

            reading_info = {
                'spoke_number': spoke_number,
                'side': side,
                'tm_reading': tm_reading,
                'estimated_tension_kgf': estimated_tension_kgf,
                'range_status': range_status,
                'average_deviation_status': average_deviation_status
            }

            readings_data.append(reading_info)
            all_readings_for_stats.append(reading_info)

        # Second pass: calculate average deviation status
        # Separate by side, filtering out NULL values (out-of-range readings)
        left_tensions = [r['estimated_tension_kgf'] for r in readings_data
                        if r['side'] == 'left' and r['estimated_tension_kgf'] is not None]
        right_tensions = [r['estimated_tension_kgf'] for r in readings_data
                         if r['side'] == 'right' and r['estimated_tension_kgf'] is not None]

        left_avg = sum(left_tensions) / len(left_tensions) if left_tensions else 0
        right_avg = sum(right_tensions) / len(right_tensions) if right_tensions else 0

        # Update average deviation status (only for valid readings)
        for reading in readings_data:
            # Skip readings that are already marked as 'unknown' (out of range)
            if reading['average_deviation_status'] == 'unknown':
                continue

            avg = left_avg if reading['side'] == 'left' else right_avg

            if avg > 0:
                upper_limit = avg * 1.2
                lower_limit = avg * 0.8

                if reading['estimated_tension_kgf'] < lower_limit:
                    reading['average_deviation_status'] = 'under'
                elif reading['estimated_tension_kgf'] > upper_limit:
                    reading['average_deviation_status'] = 'over'
                else:
                    reading['average_deviation_status'] = 'in_range'

        # Save to database
        if readings_data:
            bulk_create_or_update_readings(session_id, readings_data)
            logger.info(f"Saved {len(readings_data)} tension readings for session {session_id}")

        # Redirect back to build details with session selected
        return RedirectResponse(url=f"/build/{build_id}?session={session_id}", status_code=303)

    except ValueError as e:
        logger.error(f"Error parsing tension readings: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Invalid reading values. Please check your inputs."
        }, status_code=400)
    except Exception as e:
        logger.error(f"Error saving tension readings: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to save tension readings. Please try again later."
        }, status_code=500)

@app.post("/build/{build_id}/session/{session_id}/reading/{spoke_num}/{side}")
async def auto_save_tension_reading(
    request: Request,
    build_id: str,
    session_id: str,
    spoke_num: int,
    side: str,
    tm_reading: Optional[str] = Form(None)
):
    """Auto-save a single tension reading and return updated HTML fragments."""
    try:
        logger.debug(f"Received tm_reading: '{tm_reading}' for spoke {spoke_num} {side}")

        # Handle deletion if empty value
        if not tm_reading or tm_reading.strip() == '':
            logger.debug(f"Empty value, deleting reading if exists")

            # Verify build and session exist
            build = get_wheel_build_by_id(build_id)
            if not build:
                return HTMLResponse("Build not found", status_code=404)

            session = get_tension_session_by_id(session_id)
            if not session or session.wheel_build_id != build_id:
                return HTMLResponse("Session not found", status_code=404)

            # Delete the reading
            delete_tension_reading(session_id, spoke_num, side)

            # Get spoke and rim for stats calculation
            spoke_left = get_spoke_by_id(build.spoke_left_id) if build.spoke_left_id else None
            spoke_right = get_spoke_by_id(build.spoke_right_id) if build.spoke_right_id else None
            spoke_for_tension = spoke_left or spoke_right
            rim = get_rim_by_id(build.rim_id) if build.rim_id else None

            if not spoke_for_tension or not rim:
                return HTMLResponse("Build missing spoke or rim", status_code=400)

            tension_range = calculate_tension_range(spoke_left, spoke_right, rim)

            # Fetch ALL readings again for stats calculation
            readings = get_readings_by_session(session_id)
            analysis = analyze_tension_readings(readings, tension_range)
            stats_left = analysis['left']
            stats_right = analysis['right']
            quality_status = determine_quality_status(analysis, tension_range)

            # Organize readings by side for template
            readings_left = {}
            readings_right = {}
            for reading in readings:
                reading_data = {
                    'tm_reading': reading.tm_reading,
                    'kgf': reading.estimated_tension_kgf,
                    'range_status': reading.range_status,
                    'avg_deviation_status': reading.average_deviation_status
                }
                if reading.side == 'left':
                    readings_left[reading.spoke_number] = reading_data
                else:
                    readings_right[reading.spoke_number] = reading_data

            # Return OOB swaps with cleared values
            return templates.TemplateResponse("partials/tension_reading_clear.html", {
                "request": request,
                "spoke_num": spoke_num,
                "side": side,
                "stats_left": stats_left,
                "stats_right": stats_right,
                "quality_status": quality_status,
                "readings_left": readings_left,
                "readings_right": readings_right,
                "build": build,
                "tension_range": tension_range
            })

        # Convert to float
        try:
            tm_reading_float = float(tm_reading)
            logger.debug(f"Converted to float: {tm_reading_float}")
        except ValueError:
            logger.error(f"Invalid number: '{tm_reading}'")
            return HTMLResponse("Invalid number", status_code=400)
        # Verify build and session exist
        build = get_wheel_build_by_id(build_id)
        if not build:
            return HTMLResponse("Build not found", status_code=404)

        session = get_tension_session_by_id(session_id)
        if not session or session.wheel_build_id != build_id:
            return HTMLResponse("Session not found", status_code=404)

        # Get spoke and rim for calculations
        spoke_left = get_spoke_by_id(build.spoke_left_id) if build.spoke_left_id else None
        spoke_right = get_spoke_by_id(build.spoke_right_id) if build.spoke_right_id else None
        spoke_for_tension = spoke_left or spoke_right
        rim = get_rim_by_id(build.rim_id) if build.rim_id else None

        if not spoke_for_tension or not rim:
            return HTMLResponse("Build missing spoke or rim", status_code=400)

        # Calculate tension range and convert TM reading to kgf using side-specific spoke type
        tension_range = calculate_tension_range(spoke_left, spoke_right, rim)
        spoke_for_conversion = spoke_left if side == 'left' else spoke_right
        if not spoke_for_conversion:
            spoke_for_conversion = spoke_for_tension  # Fallback if one side is missing
        conversion_result = tm_reading_to_kgf(tm_reading_float, spoke_for_conversion.spoke_type_id)

        # Handle conversion status
        if conversion_result['status'] in ['below_table', 'above_table']:
            # Out of range - save NULL for kgf
            estimated_tension_kgf = None
            range_status = conversion_result['status']
            avg_deviation_status = 'unknown'
        else:
            # Valid conversion
            estimated_tension_kgf = conversion_result['kgf']

            # Determine side-specific max tension
            if tension_range.get('different_spoke_types'):
                # Use side-specific max when different spoke types are used
                max_kgf = tension_range['left_max_kgf'] if side == 'left' else tension_range['right_max_kgf']
            else:
                # Use common max when same spoke type on both sides
                max_kgf = tension_range['max_kgf']

            # Calculate range status using side-specific max
            if estimated_tension_kgf < tension_range['min_kgf']:
                range_status = 'under'
            elif estimated_tension_kgf > max_kgf:
                range_status = 'over'
            else:
                range_status = 'in_range'

            # Get all readings to calculate average deviation
            all_readings = get_readings_by_session(session_id)

            # Build temporary list including this new reading for average calculation
            # Filter out NULL values (out-of-range readings)
            temp_readings = []
            for r in all_readings:
                if r.spoke_number == spoke_num and r.side == side:
                    # Skip - we'll add the updated one
                    continue
                if r.estimated_tension_kgf is not None:
                    temp_readings.append({'side': r.side, 'kgf': r.estimated_tension_kgf})

            # Add the new/updated reading (it's valid since we're in this branch)
            temp_readings.append({'side': side, 'kgf': estimated_tension_kgf})

            # Calculate averages
            left_tensions = [r['kgf'] for r in temp_readings if r['side'] == 'left']
            right_tensions = [r['kgf'] for r in temp_readings if r['side'] == 'right']
            left_avg = sum(left_tensions) / len(left_tensions) if left_tensions else 0
            right_avg = sum(right_tensions) / len(right_tensions) if right_tensions else 0

            # Determine average deviation status
            avg = left_avg if side == 'left' else right_avg
            if avg > 0:
                upper_limit = avg * 1.2
                lower_limit = avg * 0.8
                if estimated_tension_kgf < lower_limit:
                    avg_deviation_status = 'under'
                elif estimated_tension_kgf > upper_limit:
                    avg_deviation_status = 'over'
                else:
                    avg_deviation_status = 'in_range'
            else:
                avg_deviation_status = 'in_range'

        # WRITE TO DATABASE
        upsert_tension_reading(
            tension_session_id=session_id,
            spoke_number=spoke_num,
            side=side,
            tm_reading=tm_reading_float,
            estimated_tension_kgf=estimated_tension_kgf,
            range_status=range_status,
            average_deviation_status=avg_deviation_status
        )

        # Fetch ALL readings again for stats calculation
        readings = get_readings_by_session(session_id)
        analysis = analyze_tension_readings(readings, tension_range)
        stats_left = analysis['left']
        stats_right = analysis['right']
        quality_status = determine_quality_status(analysis, tension_range)

        # Organize readings by side for template
        readings_left = {}
        readings_right = {}
        for reading in readings:
            reading_data = {
                'tm_reading': reading.tm_reading,
                'kgf': reading.estimated_tension_kgf,
                'range_status': reading.range_status,
                'avg_deviation_status': reading.average_deviation_status
            }
            if reading.side == 'left':
                readings_left[reading.spoke_number] = reading_data
            else:
                readings_right[reading.spoke_number] = reading_data

        # Return HTML fragments with out-of-band swaps
        return templates.TemplateResponse("partials/tension_reading_response.html", {
            "request": request,
            "spoke_num": spoke_num,
            "side": side,
            "kgf": estimated_tension_kgf,
            "range_status": range_status,
            "avg_deviation_status": avg_deviation_status,
            "stats_left": stats_left,
            "stats_right": stats_right,
            "quality_status": quality_status,
            "readings_left": readings_left,
            "readings_right": readings_right,
            "build": build,
            "tension_range": tension_range
        })

    except Exception as e:
        logger.error(f"Error auto-saving tension reading: {e}")
        return HTMLResponse(f"Error: {str(e)}", status_code=500)

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page for managing component library."""
    try:
        hubs = get_all_hubs()
        rims = get_all_rims()
        spokes = get_all_spokes()
        nipples = get_all_nipples()

        # Add locking information to each component
        for hub in hubs:
            builds_using = get_builds_using_hub(hub.id)
            hub.locked = len(builds_using) > 0
            hub.used_by_builds = builds_using

        for rim in rims:
            builds_using = get_builds_using_rim(rim.id)
            rim.locked = len(builds_using) > 0
            rim.used_by_builds = builds_using

        for spoke in spokes:
            builds_using = get_builds_using_spoke(spoke.id)
            spoke.locked = len(builds_using) > 0
            spoke.used_by_builds = builds_using

        for nipple in nipples:
            builds_using = get_builds_using_nipple(nipple.id)
            nipple.locked = len(builds_using) > 0
            nipple.used_by_builds = builds_using

        return templates.TemplateResponse("config.html", {
            "request": request,
            "hubs": hubs,
            "rims": rims,
            "spokes": spokes,
            "nipples": nipples
        })
    except Exception as e:
        logger.error(f"Error loading configuration page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to load configuration page. Please try again later."
        }, status_code=500)

@app.get("/partials/hub-form", response_class=HTMLResponse)
async def hub_form_partial(request: Request, id: str = None):
    """Return hub form modal partial for HTMX."""
    try:
        hub = None
        locked = False
        used_by_builds = []

        if id:
            hub = get_hub_by_id(id)
            if not hub:
                return HTMLResponse("<div class='alert alert-danger'>Hub not found.</div>", status_code=404)

            # Check if component is locked
            used_by_builds = get_builds_using_hub(id)
            locked = len(used_by_builds) > 0

        return templates.TemplateResponse("partials/hub_form.html", {
            "request": request,
            "hub": hub,
            "locked": locked,
            "used_by_builds": used_by_builds
        })
    except Exception as e:
        logger.error(f"Error loading hub form: {e}")
        return HTMLResponse("<div class='alert alert-danger'>Unable to load form. Please try again later.</div>", status_code=500)

@app.get("/partials/rim-form", response_class=HTMLResponse)
async def rim_form_partial(request: Request, id: str = None):
    """Return rim form modal partial for HTMX."""
    try:
        rim = None
        locked = False
        used_by_builds = []

        if id:
            rim = get_rim_by_id(id)
            if not rim:
                return HTMLResponse("<div class='alert alert-danger'>Rim not found.</div>", status_code=404)

            # Check if component is locked
            used_by_builds = get_builds_using_rim(id)
            locked = len(used_by_builds) > 0

        return templates.TemplateResponse("partials/rim_form.html", {
            "request": request,
            "rim": rim,
            "locked": locked,
            "used_by_builds": used_by_builds
        })
    except Exception as e:
        logger.error(f"Error loading rim form: {e}")
        return HTMLResponse("<div class='alert alert-danger'>Unable to load form. Please try again later.</div>", status_code=500)

@app.get("/partials/spoke-form", response_class=HTMLResponse)
async def spoke_form_partial(request: Request, id: str = None):
    """Return spoke form modal partial for HTMX."""
    try:
        spoke = None
        locked = False
        used_by_builds = []
        spoke_types = get_all_spoke_types()  # Load all spoke types

        if id:
            spoke = get_spoke_by_id(id)
            if not spoke:
                return HTMLResponse("<div class='alert alert-danger'>Spoke not found.</div>", status_code=404)

            # Check if component is locked
            used_by_builds = get_builds_using_spoke(id)
            locked = len(used_by_builds) > 0

        return templates.TemplateResponse("partials/spoke_form.html", {
            "request": request,
            "spoke": spoke,
            "locked": locked,
            "used_by_builds": used_by_builds,
            "spoke_types": spoke_types  # Pass to template
        })
    except Exception as e:
        logger.error(f"Error loading spoke form: {e}")
        return HTMLResponse("<div class='alert alert-danger'>Unable to load form. Please try again later.</div>", status_code=500)

@app.get("/partials/nipple-form", response_class=HTMLResponse)
async def nipple_form_partial(request: Request, id: str = None):
    """Return nipple form modal partial for HTMX."""
    try:
        nipple = None
        locked = False
        used_by_builds = []

        if id:
            nipple = get_nipple_by_id(id)
            if not nipple:
                return HTMLResponse("<div class='alert alert-danger'>Nipple not found.</div>", status_code=404)

            # Check if component is locked
            used_by_builds = get_builds_using_nipple(id)
            locked = len(used_by_builds) > 0

        return templates.TemplateResponse("partials/nipple_form.html", {
            "request": request,
            "nipple": nipple,
            "locked": locked,
            "used_by_builds": used_by_builds
        })
    except Exception as e:
        logger.error(f"Error loading nipple form: {e}")
        return HTMLResponse("<div class='alert alert-danger'>Unable to load form. Please try again later.</div>", status_code=500)

@app.post("/config/hub/create")
async def create_hub_route(
    request: Request,
    make: str = Form(...),
    model: str = Form(...),
    type: str = Form(...),
    old: float = Form(...),
    left_flange_diameter: float = Form(...),
    right_flange_diameter: float = Form(...),
    left_flange_offset: float = Form(...),
    right_flange_offset: float = Form(...),
    spoke_hole_diameter: float = Form(...),
    number_of_spokes: int = Form(None)
):
    """Create a new hub."""
    try:
        hub = create_hub(
            make=make,
            model=model,
            hub_type=type,
            old=old,
            left_flange_diameter=left_flange_diameter,
            right_flange_diameter=right_flange_diameter,
            left_flange_offset=left_flange_offset,
            right_flange_offset=right_flange_offset,
            spoke_hole_diameter=spoke_hole_diameter,
            number_of_spokes=number_of_spokes
        )
        logger.info(f"Created hub: {make} {model} (ID: {hub.id})")
        return RedirectResponse(url="/config#hubs", status_code=303)
    except Exception as e:
        logger.error(f"Error creating hub: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to create hub. Please try again later."
        }, status_code=500)

@app.post("/config/hub/{hub_id}/update")
async def update_hub_route(
    hub_id: str,
    request: Request,
    make: str = Form(...),
    model: str = Form(...),
    type: str = Form(...),
    old: float = Form(...),
    left_flange_diameter: float = Form(...),
    right_flange_diameter: float = Form(...),
    left_flange_offset: float = Form(...),
    right_flange_offset: float = Form(...),
    spoke_hole_diameter: float = Form(...),
    number_of_spokes: int = Form(None)
):
    """Update an existing hub."""
    try:
        # Check if component is locked
        builds_using = get_builds_using_hub(hub_id)
        if builds_using:
            logger.warning(f"Cannot update hub {hub_id}: used by {len(builds_using)} build(s)")
            return RedirectResponse(url="/config#hubs", status_code=303)

        success = update_hub(
            hub_id,
            make=make,
            model=model,
            type=type,
            old=old,
            left_flange_diameter=left_flange_diameter,
            right_flange_diameter=right_flange_diameter,
            left_flange_offset=left_flange_offset,
            right_flange_offset=right_flange_offset,
            spoke_hole_diameter=spoke_hole_diameter,
            number_of_spokes=number_of_spokes
        )
        if not success:
            logger.warning(f"Failed to update hub {hub_id}")
        return RedirectResponse(url="/config#hubs", status_code=303)
    except Exception as e:
        logger.error(f"Error updating hub: {e}")
        return RedirectResponse(url="/config#hubs", status_code=303)

@app.post("/config/rim/create")
async def create_rim_route(
    request: Request,
    make: str = Form(...),
    model: str = Form(...),
    type: str = Form(...),
    erd: float = Form(...),
    osb: float = Form(...),
    inner_width: float = Form(...),
    outer_width: float = Form(...),
    holes: int = Form(...),
    material: str = Form(...)
):
    """Create a new rim."""
    try:
        rim = create_rim(
            make=make,
            model=model,
            rim_type=type,
            erd=erd,
            osb=osb,
            inner_width=inner_width,
            outer_width=outer_width,
            holes=holes,
            material=material
        )
        logger.info(f"Created rim: {make} {model} (ID: {rim.id})")
        return RedirectResponse(url="/config#rims", status_code=303)
    except Exception as e:
        logger.error(f"Error creating rim: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to create rim. Please try again later."
        }, status_code=500)

@app.post("/config/rim/{rim_id}/update")
async def update_rim_route(
    rim_id: str,
    request: Request,
    make: str = Form(...),
    model: str = Form(...),
    type: str = Form(...),
    erd: float = Form(...),
    osb: float = Form(...),
    inner_width: float = Form(...),
    outer_width: float = Form(...),
    holes: int = Form(...),
    material: str = Form(...)
):
    """Update an existing rim."""
    try:
        # Check if component is locked
        builds_using = get_builds_using_rim(rim_id)
        if builds_using:
            logger.warning(f"Cannot update rim {rim_id}: used by {len(builds_using)} build(s)")
            return RedirectResponse(url="/config#rims", status_code=303)

        success = update_rim(
            rim_id,
            make=make,
            model=model,
            type=type,
            erd=erd,
            osb=osb,
            inner_width=inner_width,
            outer_width=outer_width,
            holes=holes,
            material=material
        )
        if not success:
            logger.warning(f"Failed to update rim {rim_id}")
        return RedirectResponse(url="/config#rims", status_code=303)
    except Exception as e:
        logger.error(f"Error updating rim: {e}")
        return RedirectResponse(url="/config#rims", status_code=303)

@app.post("/config/spoke/create")
async def create_spoke_route(
    request: Request,
    spoke_type_id: str = Form(...),
    length: float = Form(...)
):
    """Create a new spoke."""
    try:
        # Validate spoke type exists
        spoke_type = get_spoke_type_by_id(spoke_type_id)
        if not spoke_type:
            logger.error(f"Invalid spoke_type_id: {spoke_type_id}")
            return templates.TemplateResponse("partials/spoke_form.html", {
                "request": request,
                "error": "Invalid spoke type selected",
                "spoke_types": get_all_spoke_types()
            }, status_code=400)

        # Validate length
        if length <= 0:
            return templates.TemplateResponse("partials/spoke_form.html", {
                "request": request,
                "error": "Length must be greater than 0",
                "spoke_types": get_all_spoke_types()
            }, status_code=400)

        # Create spoke with spoke_type_id and length
        from database_model import Spoke
        import uuid
        spoke = Spoke.create(
            id=str(uuid.uuid4()),
            spoke_type_id=spoke_type_id,
            length=length
        )

        logger.info(f"Created spoke: {spoke.id} (type: {spoke_type.name}, length: {length}mm)")
        return RedirectResponse(url="/config#spokes", status_code=303)
    except Exception as e:
        logger.error(f"Error creating spoke: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to create spoke. Please try again later."
        }, status_code=500)

@app.post("/config/spoke/{spoke_id}/update")
async def update_spoke_route(
    spoke_id: str,
    request: Request,
    length: float = Form(...)
):
    """Update an existing spoke (only length can be changed)."""
    try:
        spoke = get_spoke_by_id(spoke_id)
        if not spoke:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": "Spoke not found"
            }, status_code=404)

        # Check if component is locked
        builds_using = get_builds_using_spoke(spoke_id)
        if builds_using:
            logger.warning(f"Cannot update spoke {spoke_id}: used by {len(builds_using)} build(s)")
            return templates.TemplateResponse("partials/spoke_form.html", {
                "request": request,
                "spoke": spoke,
                "locked": True,
                "used_by_builds": builds_using,
                "spoke_types": get_all_spoke_types(),
                "error": "Cannot edit spoke - it is being used in wheel builds"
            }, status_code=403)

        # Validate length
        if length <= 0:
            return templates.TemplateResponse("partials/spoke_form.html", {
                "request": request,
                "spoke": spoke,
                "spoke_types": get_all_spoke_types(),
                "error": "Length must be greater than 0"
            }, status_code=400)

        # Update only length (spoke_type_id cannot be changed)
        spoke.length = length
        spoke.save()

        logger.info(f"Updated spoke {spoke_id}: length={length}mm")
        return RedirectResponse(url="/config#spokes", status_code=303)
    except Exception as e:
        logger.error(f"Error updating spoke: {e}")
        return RedirectResponse(url="/config#spokes", status_code=303)

@app.post("/config/nipple/create")
async def create_nipple_route(
    request: Request,
    material: str = Form(...),
    diameter: float = Form(...),
    length: float = Form(...),
    color: str = Form(...)
):
    """Create a new nipple."""
    try:
        nipple = create_nipple(
            material=material,
            diameter=diameter,
            length=length,
            color=color
        )
        logger.info(f"Created nipple: {material} {diameter}mm (ID: {nipple.id})")
        return RedirectResponse(url="/config#nipples", status_code=303)
    except Exception as e:
        logger.error(f"Error creating nipple: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": "Unable to create nipple. Please try again later."
        }, status_code=500)

@app.post("/config/nipple/{nipple_id}/update")
async def update_nipple_route(
    nipple_id: str,
    request: Request,
    material: str = Form(...),
    diameter: float = Form(...),
    length: float = Form(...),
    color: str = Form(...)
):
    """Update an existing nipple."""
    try:
        # Check if component is locked
        builds_using = get_builds_using_nipple(nipple_id)
        if builds_using:
            logger.warning(f"Cannot update nipple {nipple_id}: used by {len(builds_using)} build(s)")
            return RedirectResponse(url="/config#nipples", status_code=303)

        success = update_nipple(
            nipple_id,
            material=material,
            diameter=diameter,
            length=length,
            color=color
        )
        if not success:
            logger.warning(f"Failed to update nipple {nipple_id}")
        return RedirectResponse(url="/config#nipples", status_code=303)
    except Exception as e:
        logger.error(f"Error updating nipple: {e}")
        return RedirectResponse(url="/config#nipples", status_code=303)

@app.post("/config/hub/{hub_id}/delete")
async def delete_hub_route(hub_id: str):
    """Delete a hub."""
    try:
        # Check if component is locked
        builds_using = get_builds_using_hub(hub_id)
        if builds_using:
            logger.warning(f"Cannot delete hub {hub_id}: used by {len(builds_using)} build(s)")
            return RedirectResponse(url="/config#hubs", status_code=303)

        delete_hub(hub_id)
        logger.info(f"Deleted hub: {hub_id}")
        return RedirectResponse(url="/config#hubs", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting hub: {e}")
        return RedirectResponse(url="/config#hubs", status_code=303)

@app.post("/config/rim/{rim_id}/delete")
async def delete_rim_route(rim_id: str):
    """Delete a rim."""
    try:
        # Check if component is locked
        builds_using = get_builds_using_rim(rim_id)
        if builds_using:
            logger.warning(f"Cannot delete rim {rim_id}: used by {len(builds_using)} build(s)")
            return RedirectResponse(url="/config#rims", status_code=303)

        delete_rim(rim_id)
        logger.info(f"Deleted rim: {rim_id}")
        return RedirectResponse(url="/config#rims", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting rim: {e}")
        return RedirectResponse(url="/config#rims", status_code=303)

@app.post("/config/spoke/{spoke_id}/delete")
async def delete_spoke_route(spoke_id: str):
    """Delete a spoke."""
    try:
        # Check if component is locked
        builds_using = get_builds_using_spoke(spoke_id)
        if builds_using:
            logger.warning(f"Cannot delete spoke {spoke_id}: used by {len(builds_using)} build(s)")
            return RedirectResponse(url="/config#spokes", status_code=303)

        delete_spoke(spoke_id)
        logger.info(f"Deleted spoke: {spoke_id}")
        return RedirectResponse(url="/config#spokes", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting spoke: {e}")
        return RedirectResponse(url="/config#spokes", status_code=303)

@app.post("/config/nipple/{nipple_id}/delete")
async def delete_nipple_route(nipple_id: str):
    """Delete a nipple."""
    try:
        # Check if component is locked
        builds_using = get_builds_using_nipple(nipple_id)
        if builds_using:
            logger.warning(f"Cannot delete nipple {nipple_id}: used by {len(builds_using)} build(s)")
            return RedirectResponse(url="/config#nipples", status_code=303)

        delete_nipple(nipple_id)
        logger.info(f"Deleted nipple: {nipple_id}")
        return RedirectResponse(url="/config#nipples", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting nipple: {e}")
        return RedirectResponse(url="/config#nipples", status_code=303)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}