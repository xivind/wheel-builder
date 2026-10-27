# Graph Report - wheel-builder  (2026-10-27)

## Corpus Check
- 4 files · ~35,876 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 256 nodes · 452 edges · 16 communities (9 shown, 7 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 73 edges (avg confidence: 0.94)
- Token cost: 61,466 input · 0 output

## Community Hubs (Navigation)
- FastAPI Routes & Templates
- Component CRUD & UUIDs
- Tension Analysis & Quality
- TM-1 Conversion & Sessions
- Wheel Build Management
- Spoke Length Calculation
- Architecture & Deployment Docs
- App Lifecycle Events
- Form Input Helpers
- Database Backup Script
- Docker Deployment Script
- App Logo & Branding
- Conversion Table Data
- Package Root
- Favicon Icon

## God Nodes (most connected - your core abstractions)
1. `WheelBuild` - 14 edges
2. `BaseModel` - 13 edges
3. `TensionReading` - 12 edges
4. `SpokeType` - 11 edges
5. `generate_uuid()` - 11 edges
6. `Tension Tracking System` - 11 edges
7. `TensionSession` - 10 edges
8. `Hub` - 10 edges
9. `Rim` - 10 edges
10. `Spoke` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Spoke Length Calculation` --shares_data_with--> `Rim`  [INFERRED]
  CLAUDE.md → database_model.py
- `Component Locking` --shares_data_with--> `WheelBuild`  [INFERRED]
  CLAUDE.md → database_model.py
- `Progressive Build Creation` --rationale_for--> `WheelBuild`  [INFERRED]
  CLAUDE.md → database_model.py
- `Deviation Tracking (Dual Approach)` --shares_data_with--> `TensionReading`  [INFERRED]
  CLAUDE.md → database_model.py
- `Tension Tracking System` --references--> `TensionSession`  [EXTRACTED]
  CLAUDE.md → database_model.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Build Create/Edit Form Duplication (Modal vs Full Page)** — templates_partials_build_form_partial, templates_build_edit_page, templates_dashboard_page, templates_build_details_page [INFERRED 0.75]
- **Component Library Locked-Editing Pattern** — templates_config_page, templates_partials_hub_form_partial, templates_partials_rim_form_partial, templates_partials_spoke_form_partial, templates_partials_nipple_form_partial [INFERRED 0.85]
- **Tension Reading HTMX Live Update Flow** — templates_build_details_page, templates_partials_tension_reading_response_partial, templates_partials_tension_reading_clear_partial [INFERRED 0.85]
- **Tension reading to quality status pipeline** — business_logic_tm_reading_to_kgf, business_logic_analyze_tension_readings, business_logic_determine_quality_status, database_manager_bulk_create_or_update_readings [INFERRED 0.85]
- **Three-layer architecture (routing, logic, data)** — claude_routing_layer, claude_business_logic_layer, claude_data_access_layer [EXTRACTED 1.00]
- **Persistent data storage across Docker and local dev** — claude_sqlite_storage, claude_docker_deployment, claude_database_backup, readme_database_path_override [INFERRED 0.85]

## Communities (16 total, 7 thin omitted)

### Community 0 - "FastAPI Routes & Templates"
Cohesion: 0.06
Nodes (59): fastapi, fastapi_responses, fastapi_staticfiles, fastapi_templating, get, auto_save_tension_reading(), build_details(), build_form_partial() (+51 more)

### Community 1 - "Component CRUD & UUIDs"
Cohesion: 0.07
Nodes (46): UUID Primary Keys, create_hub(), create_nipple(), create_rim(), create_spoke(), create_tension_session(), create_wheel_build(), delete_nipple() (+38 more)

### Community 2 - "Tension Analysis & Quality"
Cohesion: 0.08
Nodes (34): analyze_tension_readings(), determine_quality_status(), Analyze tension readings for a session. Args: readings: List of TensionReading…, Determine overall quality status of wheel using percentage-based thresholds.…, Deviation Tracking (Dual Approach), HTMX Partial Updates, Quality Status Logic (Industry Standards), Radar Charts (tension visualization) (+26 more)

### Community 3 - "TM-1 Conversion & Sessions"
Cohesion: 0.10
Nodes (28): Convert Park Tool TM-1 reading to kgf tension using table lookup. Uses…, tm_reading_to_kgf(), conversion_table.txt (TM-1 calibration table), Park Tool TM-1 Conversion System, get_sessions_by_build(), get_tension_session_by_id(), Get all tension sessions for a wheel build., Get a specific tension session by ID. (+20 more)

### Community 4 - "Wheel Build Management"
Cohesion: 0.08
Nodes (28): calculate_tension_range(), Calculate recommended min/max tension for a spoke/rim combination. Uses spoke…, Progressive Build Creation, delete_wheel_build(), get_all_wheel_builds(), get_builds_using_hub(), get_builds_using_nipple(), get_builds_using_rim() (+20 more)

### Community 5 - "Spoke Length Calculation"
Cohesion: 0.12
Nodes (17): calculate_spoke_length(), can_calculate_spoke_length(), Check if wheel build has all required data for spoke length calculation. Args:…, Calculate recommended spoke length for one side of the wheel. Based on Damon…, Spoke Length Calculation, delete_hub(), get_hubs_by_ids(), Get multiple hubs by their IDs (batch fetch). (+9 more)

### Community 6 - "Architecture & Deployment Docs"
Cohesion: 0.14
Nodes (17): Business Logic Layer (business_logic.py), Component Locking, Data Access Layer (database_manager.py), Database Backup (backup_db.sh), Docker Deployment (create-container-wheelbuilder.sh), graphify Knowledge Graph, Docker Health Check, Logging Guidelines (standard logging, no logger.py) (+9 more)

### Community 7 - "App Lifecycle Events"
Cohesion: 0.40
Nodes (5): Initialize database on startup., Close database connection on shutdown., shutdown_event(), startup_event(), on_event

### Community 8 - "Form Input Helpers"
Cohesion: 0.50
Nodes (3): empty_to_none(), Convert empty string or whitespace-only string to None. This ensures we store…, uuid

## Knowledge Gaps
- **22 isolated node(s):** `backup_db.sh script`, `create-container-wheelbuilder.sh script`, `wheel-builder`, `error.html (Error Page)`, `nipple_form.html (Nipple Create/Edit Modal Partial)` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 116 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WheelBuild` connect `Wheel Build Management` to `Component CRUD & UUIDs`, `TM-1 Conversion & Sessions`, `Architecture & Deployment Docs`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `Component Locking` connect `Architecture & Deployment Docs` to `Wheel Build Management`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `TensionReading` connect `Tension Analysis & Quality` to `Component CRUD & UUIDs`, `TM-1 Conversion & Sessions`, `Wheel Build Management`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `WheelBuild` (e.g. with `Component Locking` and `Progressive Build Creation`) actually correct?**
  _`WheelBuild` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `TensionReading` (e.g. with `Deviation Tracking (Dual Approach)` and `bulk_create_or_update_readings()`) actually correct?**
  _`TensionReading` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `backup_db.sh script`, `create-container-wheelbuilder.sh script`, `wheel-builder` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `FastAPI Routes & Templates` be split into smaller, more focused modules?**
  _Cohesion score 0.06271186440677966 - nodes in this community are weakly interconnected._