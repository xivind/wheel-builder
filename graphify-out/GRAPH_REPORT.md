# Graph Report - wheel-builder  (2026-09-17)

## Corpus Check
- Corpus is ~36,070 words - fits in a single context window. You may not need a graph.

## Summary
- 235 nodes · 580 edges · 15 communities (9 shown, 5 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 76 edges (avg confidence: 0.94)
- Token cost: 238,432 input · 0 output

## Community Hubs (Navigation)
- Business Logic & Data Models
- Documentation & Frontend Templates
- Tension Tracking & Builds
- Hub Management & App Lifecycle
- Component Config Forms
- Build & Session CRUD Routes
- Spoke Component Management
- Nipple Component Management
- Rim Component Management
- Database Backup Script
- Docker Deployment Script
- App Logo & Branding
- Package Root
- Favicon Icon

## God Nodes (most connected - your core abstractions)
1. `build_details()` - 17 edges
2. `auto_save_tension_reading()` - 16 edges
3. `Wheel Builder Project Overview` - 15 edges
4. `BaseModel` - 13 edges
5. `WheelBuild` - 12 edges
6. `TensionReading` - 12 edges
7. `config_page()` - 12 edges
8. `get_rim_by_id()` - 11 edges
9. `get_wheel_build_by_id()` - 11 edges
10. `get_hub_by_id()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `get_all_hubs()` --uses--> `Hub`  [INFERRED]
  database_manager.py → database_model.py
- `get_hub_by_id()` --uses--> `Hub`  [INFERRED]
  database_manager.py → database_model.py
- `get_builds_using_hub()` --uses--> `WheelBuild`  [INFERRED]
  database_manager.py → database_model.py
- `create_rim()` --uses--> `Rim`  [INFERRED]
  database_manager.py → database_model.py
- `get_all_rims()` --uses--> `Rim`  [INFERRED]
  database_manager.py → database_model.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Component Library Locked-Editing Pattern** — templates_config_page, templates_partials_hub_form_partial, templates_partials_rim_form_partial, templates_partials_spoke_form_partial, templates_partials_nipple_form_partial [INFERRED 0.85]
- **Tension Reading HTMX Live Update Flow** — templates_build_details_page, templates_partials_tension_reading_response_partial, templates_partials_tension_reading_clear_partial [INFERRED 0.85]
- **Build Create/Edit Form Duplication (Modal vs Full Page)** — templates_partials_build_form_partial, templates_build_edit_page, templates_dashboard_page, templates_build_details_page [INFERRED 0.75]

## Communities (15 total, 5 thin omitted)

### Community 0 - "Business Logic & Data Models"
Cohesion: 0.09
Nodes (37): analyze_tension_readings(), calculate_spoke_length(), calculate_tension_range(), can_calculate_spoke_length(), determine_quality_status(), Calculate recommended min/max tension for a spoke/rim combination. Uses spoke…, Check if wheel build has all required data for spoke length calculation. Args:…, Analyze tension readings for a session. Args: readings: List of TensionReading… (+29 more)

### Community 1 - "Documentation & Frontend Templates"
Cohesion: 0.09
Nodes (38): Component Locking, Database Management (Location, Initialization, Backup), Database Models (7 Tables), Deviation Tracking (Dual Approach), Docker Deployment, Frontend Organization, Graphify Knowledge Graph Integration, Important Constraints (+30 more)

### Community 2 - "Tension Tracking & Builds"
Cohesion: 0.10
Nodes (35): bulk_create_or_update_readings(), create_tension_reading(), create_tension_session(), create_wheel_build(), delete_tension_reading(), delete_tension_session(), delete_wheel_build(), get_readings_by_session() (+27 more)

### Community 3 - "Hub Management & App Lifecycle"
Cohesion: 0.09
Nodes (35): create_hub(), create_nipple(), create_rim(), delete_hub(), delete_spoke(), get_all_wheel_builds(), get_builds_using_hub(), get_hubs_by_ids() (+27 more)

### Community 4 - "Component Config Forms"
Cohesion: 0.13
Nodes (24): get_all_hubs(), get_all_nipples(), get_all_rims(), Get all nipples from database., Get all hubs from database., Get all rims from database., get, build_form_partial() (+16 more)

### Community 5 - "Build & Session CRUD Routes"
Cohesion: 0.13
Nodes (21): get_hub_by_id(), get_rim_by_id(), Update a wheel build's fields., Get a specific hub by ID., Get a specific rim by ID., update_wheel_build(), calculate_spoke_length_api(), create_build() (+13 more)

### Community 6 - "Spoke Component Management"
Cohesion: 0.18
Nodes (11): create_spoke(), get_all_spoke_types(), get_builds_using_spoke(), Create a new spoke in the database., Update a spoke's fields., Get all wheel builds using this spoke (left or right)., Get all spoke types for selection. Returns: list: All SpokeType instances,…, update_spoke() (+3 more)

### Community 7 - "Nipple Component Management"
Cohesion: 0.25
Nodes (8): delete_nipple(), get_builds_using_nipple(), Update a nipple's fields., Get all wheel builds using this nipple., update_nipple(), delete_nipple_route(), Update an existing nipple., update_nipple_route()

### Community 8 - "Rim Component Management"
Cohesion: 0.25
Nodes (8): delete_rim(), get_builds_using_rim(), Update a rim's fields., Get all wheel builds using this rim., update_rim(), delete_rim_route(), Update an existing rim., update_rim_route()

## Knowledge Gaps
- **12 isolated node(s):** `backup_db.sh script`, `create-container-wheelbuilder.sh script`, `wheel-builder`, `Quality Status Logic (Industry Standards)`, `Graphify Knowledge Graph Integration` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 94 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BaseModel` connect `Business Logic & Data Models` to `Tension Tracking & Builds`, `Hub Management & App Lifecycle`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `initialize_database()` connect `Business Logic & Data Models` to `Hub Management & App Lifecycle`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `backup_db.sh script`, `create-container-wheelbuilder.sh script`, `wheel-builder` to the rest of the system?**
  _12 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Business Logic & Data Models` be split into smaller, more focused modules?**
  _Cohesion score 0.08780487804878048 - nodes in this community are weakly interconnected._
- **Should `Documentation & Frontend Templates` be split into smaller, more focused modules?**
  _Cohesion score 0.08677098150782361 - nodes in this community are weakly interconnected._
- **Should `Tension Tracking & Builds` be split into smaller, more focused modules?**
  _Cohesion score 0.09759759759759759 - nodes in this community are weakly interconnected._
- **Should `Hub Management & App Lifecycle` be split into smaller, more focused modules?**
  _Cohesion score 0.08571428571428572 - nodes in this community are weakly interconnected._