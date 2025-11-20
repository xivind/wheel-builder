# Spoke Template System Implementation Plan

**Date:** 2025-11-20
**Status:** Planning
**Author:** Claude

## Executive Summary

This document describes the implementation of a spoke template system that uses official Park Tool TM-1 conversion tables to accurately convert tension meter readings to kgf values. The system replaces the current formula-based approach with a lookup-table method that supports 38 different spoke types across steel, aluminum, titanium, and specialty materials.

## Goals

1. **Accuracy**: Use official Park Tool calibration data instead of approximated formulas
2. **Data Integrity**: Prevent user errors by seeding validated spoke specifications
3. **User Experience**: Simplify spoke creation through template selection
4. **Safety**: Ensure tension measurements are reliable for safety-critical wheel building
5. **Maintainability**: Easy to update when new spoke types are released

## Current vs. New System

### Current System
- Users manually enter spoke properties (material, gauge, max_tension, length)
- Tension conversion uses exponential formula with 4 coefficient sets
- Formula: `kgf = a + b * exp(c * reading)` where coefficients vary by gauge
- Limited accuracy, especially for non-steel or blade spokes

### New System
- 38 pre-configured spoke templates seeded from Park Tool data
- Users select template → customize name and length → create spoke
- Tension conversion uses lookup table with interpolation
- Accurate for all materials: steel, aluminum, titanium, carbon, specialty
- Supports both round and blade spoke geometries

---

## Database Changes

### 1. Spoke Model Schema Updates

**File:** `database_model.py`

Add the following fields to the `Spoke` model:

```python
class Spoke(BaseModel):
    # Existing fields
    id = UUIDField(primary_key=True)
    material = CharField()
    gauge = FloatField()  # Keep for backward compatibility
    max_tension = FloatField()
    length = FloatField(null=True)  # Now nullable for templates

    # NEW FIELDS
    is_template = BooleanField(default=False)  # True for Park Tool templates
    template_id = ForeignKeyField('self', null=True, backref='instances')  # Parent template
    park_tool_designation = CharField(null=True)  # e.g., "Steel Round 2.0mm"

    # Spoke geometry
    shape = CharField(null=True)  # 'round' or 'blade'
    width = FloatField(null=True)  # For blade spokes (mm)
    thickness = FloatField(null=True)  # For blade spokes (mm)

    # Tension specifications
    min_tension = FloatField(null=True)  # Minimum recommended tension (kgf)
    conversion_table = JSONField(null=True)  # Park Tool TM→kgf mappings

    # Renamed for clarity
    name = CharField()  # User-friendly name (was 'material' in UI)
```

**Key Design Decisions:**
- `is_template`: Distinguishes read-only templates from user spokes
- `template_id`: Tracks which template a spoke is based on
- `conversion_table`: Stores Park Tool data as JSON `{tm_reading: kgf}`
- `length`: Nullable because templates don't have specific lengths
- `min_tension`: Derived from conversion table (min kgf value)
- `max_tension`: Derived from conversion table (max kgf value)

**Migration Strategy:**
- No migration needed - rebuild database from scratch
- User instructed: "We're not in production yet"

---

### 2. Database Manager Updates

**File:** `database_manager.py`

Update `create_spoke()` function signature:

```python
def create_spoke(
    name,
    is_template=False,
    template_id=None,
    park_tool_designation=None,
    material=None,
    shape=None,
    gauge=None,
    width=None,
    thickness=None,
    min_tension=None,
    max_tension=None,
    conversion_table=None,
    length=None
):
    """Create a new spoke (template or user spoke).

    Args:
        name: Display name (for templates: Park Tool designation)
        is_template: True for Park Tool templates (read-only)
        template_id: UUID of parent template (for user spokes)
        park_tool_designation: Official Park Tool name
        material: steel/aluminum/titanium/carbon
        shape: round/blade
        gauge: Diameter (mm) for round spokes, thickness for blade
        width: Width (mm) for blade spokes only
        thickness: Thickness (mm) for blade spokes only
        min_tension: Minimum recommended tension (kgf)
        max_tension: Maximum recommended tension (kgf)
        conversion_table: Dict of {tm_reading: kgf}
        length: Spoke length (mm), None for templates
    """
    spoke_id = generate_uuid()
    spoke = Spoke.create(
        id=spoke_id,
        name=name,
        is_template=is_template,
        template_id=template_id,
        park_tool_designation=park_tool_designation,
        material=material,
        shape=shape,
        gauge=gauge,
        width=width,
        thickness=thickness,
        min_tension=min_tension,
        max_tension=max_tension,
        conversion_table=conversion_table,
        length=length
    )
    return spoke
```

Add new query functions:

```python
def get_spoke_templates():
    """Get all spoke templates (is_template=True)."""
    return list(Spoke.select().where(Spoke.is_template == True).order_by(Spoke.name))

def get_user_spokes():
    """Get all user-created spokes (is_template=False)."""
    return list(Spoke.select().where(Spoke.is_template == False).order_by(Spoke.name))

def get_spoke_by_template(template_id):
    """Get all spokes created from a specific template."""
    return list(Spoke.select().where(Spoke.template_id == template_id))
```

---

## Business Logic Changes

### 1. Tension Conversion Function

**File:** `business_logic.py`

Replace `tm_reading_to_kgf()` with lookup-based implementation:

```python
def tm_reading_to_kgf(tm_reading, spoke):
    """Convert Park Tool TM-1 reading to kgf using lookup table.

    Uses official Park Tool conversion tables with exponential interpolation
    for values between table entries.

    Args:
        tm_reading: Park Tool TM-1 reading (0-50 range)
        spoke: Spoke model instance with conversion_table

    Returns:
        float: Estimated tension in kgf
    """
    if not spoke.conversion_table:
        logger.warning(f"Spoke {spoke.id} has no conversion table, cannot convert TM reading")
        return 0.0

    conversion_table = spoke.conversion_table
    tm_readings = sorted(conversion_table.keys())

    # Exact match
    if tm_reading in conversion_table:
        return float(conversion_table[tm_reading])

    # Outside range - extrapolate with warning
    if tm_reading < tm_readings[0]:
        logger.warning(f"TM reading {tm_reading} below calibrated range ({tm_readings[0]}-{tm_readings[-1]})")
        return float(conversion_table[tm_readings[0]])

    if tm_reading > tm_readings[-1]:
        logger.warning(f"TM reading {tm_reading} above calibrated range ({tm_readings[0]}-{tm_readings[-1]})")
        return float(conversion_table[tm_readings[-1]])

    # Interpolate between two points
    # Find bracketing values
    lower_tm = max([r for r in tm_readings if r <= tm_reading])
    upper_tm = min([r for r in tm_readings if r >= tm_reading])

    lower_kgf = conversion_table[lower_tm]
    upper_kgf = conversion_table[upper_tm]

    # Exponential interpolation (more accurate for tension curves)
    # kgf = lower_kgf * exp(ln(upper_kgf/lower_kgf) * (tm_reading - lower_tm) / (upper_tm - lower_tm))
    if lower_kgf > 0 and upper_kgf > 0:
        ratio = (tm_reading - lower_tm) / (upper_tm - lower_tm)
        kgf = lower_kgf * math.exp(math.log(upper_kgf / lower_kgf) * ratio)
    else:
        # Fallback to linear interpolation if values are problematic
        ratio = (tm_reading - lower_tm) / (upper_tm - lower_tm)
        kgf = lower_kgf + (upper_kgf - lower_kgf) * ratio

    logger.debug(f"TM {tm_reading} → {kgf:.1f} kgf (interpolated between {lower_tm}→{lower_kgf} and {upper_tm}→{upper_kgf})")

    return round(kgf, 1)
```

**Why Exponential Interpolation:**
- Tension vs. deflection follows exponential relationship
- More accurate than linear interpolation
- Matches the physics of material deformation

### 2. Tension Range Calculation

**File:** `business_logic.py`

Simplify `calculate_tension_range()`:

```python
def calculate_tension_range(spoke, rim):
    """Calculate recommended min/max tension for a spoke/rim combination.

    Uses min/max values directly from Park Tool conversion tables.

    Args:
        spoke: Spoke model instance
        rim: Rim model instance (for future rim-specific limits)

    Returns:
        dict: {
            'min_kgf': float,
            'max_kgf': float,
            'min_tm_reading': float,
            'max_tm_reading': float
        }
    """
    # Use spoke min/max tension from Park Tool data
    min_tension = spoke.min_tension if spoke.min_tension else spoke.max_tension * 0.6
    max_tension = spoke.max_tension

    # Get TM reading range from conversion table
    if spoke.conversion_table:
        tm_readings = sorted(spoke.conversion_table.keys())
        min_tm = tm_readings[0]
        max_tm = tm_readings[-1]
    else:
        # Fallback if no conversion table (legacy spokes)
        min_tm = 0
        max_tm = 50

    logger.info(f"Tension range: {min_tension:.1f}-{max_tension:.1f} kgf, TM: {min_tm}-{max_tm}")

    return {
        'min_kgf': round(min_tension, 1),
        'max_kgf': round(max_tension, 1),
        'min_tm_reading': round(min_tm, 1),
        'max_tm_reading': round(max_tm, 1)
    }
```

**Key Changes:**
- No more inverse exponential formula calculation
- TM range comes directly from conversion table keys
- min_tension uses Park Tool data (min kgf from table)
- Fallback to 60% rule only for legacy spokes without conversion tables

---

## Frontend Changes

### 1. New Component: Template Selection Modal

**File:** `templates/components/spoke_template_selector.html` (new file)

Create a modal for selecting spoke templates:

```html
<!-- Template Selection Modal -->
<div id="spokeTemplateSelectorModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>Select Spoke Template</h2>
            <span class="close" onclick="closeSpokeTemplateSelector()">&times;</span>
        </div>
        <div class="modal-body">
            <p>Choose a spoke type from the Park Tool calibrated templates:</p>

            <!-- Search and filter -->
            <input type="text" id="templateSearch" placeholder="Search spoke types..."
                   oninput="filterSpokeTemplates()" class="form-control">

            <!-- Template list -->
            <div id="templateList" class="template-list">
                <!-- Populated dynamically via JavaScript -->
            </div>
        </div>
        <div class="modal-footer">
            <button onclick="closeSpokeTemplateSelector()" class="btn-secondary">Cancel</button>
            <button onclick="selectSpokeTemplate()" class="btn-primary" id="selectTemplateBtn" disabled>
                Continue
            </button>
        </div>
    </div>
</div>
```

**JavaScript Functions:**

```javascript
let selectedTemplateId = null;

function openSpokeTemplateSelector() {
    // Fetch templates from server
    fetch('/api/spoke-templates')
        .then(response => response.json())
        .then(templates => {
            renderTemplateList(templates);
            document.getElementById('spokeTemplateSelectorModal').style.display = 'block';
        });
}

function renderTemplateList(templates) {
    const listDiv = document.getElementById('templateList');
    listDiv.innerHTML = '';

    // Group by material
    const grouped = {
        'Steel Round': [],
        'Steel Blade': [],
        'Aluminum': [],
        'Titanium & Specialty': []
    };

    templates.forEach(t => {
        if (t.material === 'steel' && t.shape === 'round') grouped['Steel Round'].push(t);
        else if (t.material === 'steel' && t.shape === 'blade') grouped['Steel Blade'].push(t);
        else if (t.material === 'aluminum') grouped['Aluminum'].push(t);
        else grouped['Titanium & Specialty'].push(t);
    });

    for (const [group, items] of Object.entries(grouped)) {
        if (items.length === 0) continue;

        const groupDiv = document.createElement('div');
        groupDiv.className = 'template-group';
        groupDiv.innerHTML = `<h3>${group}</h3>`;

        items.forEach(template => {
            const item = document.createElement('div');
            item.className = 'template-item';
            item.innerHTML = `
                <input type="radio" name="template" value="${template.id}"
                       id="template_${template.id}" onchange="onTemplateSelected('${template.id}')">
                <label for="template_${template.id}">
                    <strong>${template.park_tool_designation}</strong>
                    <span class="template-specs">
                        ${template.min_tension}-${template.max_tension} kgf
                    </span>
                </label>
            `;
            groupDiv.appendChild(item);
        });

        listDiv.appendChild(groupDiv);
    }
}

function onTemplateSelected(templateId) {
    selectedTemplateId = templateId;
    document.getElementById('selectTemplateBtn').disabled = false;
}

function filterSpokeTemplates() {
    const searchTerm = document.getElementById('templateSearch').value.toLowerCase();
    const items = document.querySelectorAll('.template-item');

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
}

function selectSpokeTemplate() {
    if (!selectedTemplateId) return;

    // Fetch template details and open spoke modal with pre-filled data
    fetch(`/api/spoke-templates/${selectedTemplateId}`)
        .then(response => response.json())
        .then(template => {
            closeSpokeTemplateSelector();
            openSpokeModalWithTemplate(template);
        });
}

function closeSpokeTemplateSelector() {
    document.getElementById('spokeTemplateSelectorModal').style.display = 'none';
    selectedTemplateId = null;
}
```

### 2. Update Spoke Modal

**File:** `templates/components/spoke_modal.html`

Modify existing spoke modal to handle templates:

```html
<!-- Modified Spoke Modal -->
<div id="spokeModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2 id="spokeModalTitle">Spoke Details</h2>
            <!-- NEW: Template badge -->
            <span id="templateBadge" class="badge badge-info" style="display: none;">
                Template - Read Only
            </span>
            <span class="close" onclick="closeSpokeModal()">&times;</span>
        </div>
        <form id="spokeForm" onsubmit="saveSpokeForm(event)">
            <div class="modal-body">
                <!-- Hidden fields -->
                <input type="hidden" id="spokeId" name="id">
                <input type="hidden" id="isTemplate" name="is_template" value="false">
                <input type="hidden" id="templateId" name="template_id">

                <!-- Name field - ALWAYS editable -->
                <div class="form-group">
                    <label for="spokeName">Name *</label>
                    <input type="text" id="spokeName" name="name" required
                           class="form-control" placeholder="e.g., Front Left DT Competition 260mm">
                </div>

                <!-- Length field - ALWAYS editable (except templates) -->
                <div class="form-group">
                    <label for="spokeLength">Length (mm)</label>
                    <input type="number" id="spokeLength" name="length" step="0.1"
                           class="form-control" placeholder="e.g., 260.0">
                </div>

                <!-- Material field - LOCKED for non-templates -->
                <div class="form-group">
                    <label for="spokeMaterial">Material</label>
                    <input type="text" id="spokeMaterial" name="material"
                           class="form-control" readonly>
                </div>

                <!-- Shape field - Display only -->
                <div class="form-group">
                    <label for="spokeShape">Shape</label>
                    <input type="text" id="spokeShape" name="shape"
                           class="form-control" readonly>
                </div>

                <!-- Gauge/Dimensions - Display only -->
                <div class="form-group">
                    <label for="spokeGauge">Gauge / Dimensions</label>
                    <input type="text" id="spokeGauge" name="gauge_display"
                           class="form-control" readonly>
                </div>

                <!-- Tension Range - Display only -->
                <div class="form-group">
                    <label>Tension Range</label>
                    <div class="tension-range-display">
                        <span id="minTensionDisplay">-- kgf</span> to
                        <span id="maxTensionDisplay">-- kgf</span>
                    </div>
                </div>

                <!-- Park Tool Designation - Display only -->
                <div class="form-group" id="parkToolDesignationGroup" style="display: none;">
                    <label>Park Tool Designation</label>
                    <input type="text" id="parkToolDesignation" class="form-control" readonly>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" onclick="closeSpokeModal()" class="btn-secondary">
                    <span id="closeButtonText">Close</span>
                </button>
                <button type="submit" class="btn-primary" id="saveSpokeBtn">
                    Save
                </button>
            </div>
        </form>
    </div>
</div>
```

**JavaScript Updates:**

```javascript
function openSpokeModalWithTemplate(template) {
    // Populate form with template data
    document.getElementById('spokeId').value = '';  // New spoke
    document.getElementById('isTemplate').value = 'false';
    document.getElementById('templateId').value = template.id;

    // User-editable fields
    document.getElementById('spokeName').value = '';  // User must provide name
    document.getElementById('spokeName').disabled = false;
    document.getElementById('spokeLength').value = '';  // User must provide length
    document.getElementById('spokeLength').disabled = false;

    // Locked fields (from template)
    document.getElementById('spokeMaterial').value = template.material;
    document.getElementById('spokeShape').value = template.shape;

    // Format gauge display
    let gaugeDisplay = '';
    if (template.shape === 'round') {
        gaugeDisplay = `${template.gauge} mm`;
    } else {
        gaugeDisplay = `${template.thickness} × ${template.width} mm`;
    }
    document.getElementById('spokeGauge').value = gaugeDisplay;

    // Tension range
    document.getElementById('minTensionDisplay').textContent = `${template.min_tension} kgf`;
    document.getElementById('maxTensionDisplay').textContent = `${template.max_tension} kgf`;

    // Park Tool designation
    document.getElementById('parkToolDesignation').value = template.park_tool_designation;
    document.getElementById('parkToolDesignationGroup').style.display = 'block';

    // Hide template badge (this is a new spoke, not a template)
    document.getElementById('templateBadge').style.display = 'none';

    // Show modal
    document.getElementById('spokeModalTitle').textContent = 'Create Spoke from Template';
    document.getElementById('saveSpokeBtn').style.display = 'inline-block';
    document.getElementById('spokeModal').style.display = 'block';
}

function openSpokeModalForView(spoke) {
    // View existing spoke (template or user spoke)
    document.getElementById('spokeId').value = spoke.id;
    document.getElementById('isTemplate').value = spoke.is_template;
    document.getElementById('templateId').value = spoke.template_id || '';

    document.getElementById('spokeName').value = spoke.name;
    document.getElementById('spokeLength').value = spoke.length || '';
    document.getElementById('spokeMaterial').value = spoke.material;
    document.getElementById('spokeShape').value = spoke.shape;

    let gaugeDisplay = '';
    if (spoke.shape === 'round') {
        gaugeDisplay = `${spoke.gauge} mm`;
    } else {
        gaugeDisplay = `${spoke.thickness} × ${spoke.width} mm`;
    }
    document.getElementById('spokeGauge').value = gaugeDisplay;

    document.getElementById('minTensionDisplay').textContent = `${spoke.min_tension} kgf`;
    document.getElementById('maxTensionDisplay').textContent = `${spoke.max_tension} kgf`;

    if (spoke.park_tool_designation) {
        document.getElementById('parkToolDesignation').value = spoke.park_tool_designation;
        document.getElementById('parkToolDesignationGroup').style.display = 'block';
    }

    // If template: show badge and disable all fields
    if (spoke.is_template) {
        document.getElementById('templateBadge').style.display = 'inline-block';
        document.getElementById('spokeName').disabled = true;
        document.getElementById('spokeLength').disabled = true;
        document.getElementById('saveSpokeBtn').style.display = 'none';
        document.getElementById('closeButtonText').textContent = 'Close';
        document.getElementById('spokeModalTitle').textContent = 'Spoke Template';
    } else {
        document.getElementById('templateBadge').style.display = 'none';
        document.getElementById('spokeName').disabled = false;
        document.getElementById('spokeLength').disabled = false;
        document.getElementById('saveSpokeBtn').style.display = 'inline-block';
        document.getElementById('closeButtonText').textContent = 'Cancel';
        document.getElementById('spokeModalTitle').textContent = 'Edit Spoke';
    }

    document.getElementById('spokeModal').style.display = 'block';
}
```

### 3. Update Spokes List/Table

**File:** `templates/components.html` (spokes section)

Add filter buttons above the spokes table:

```html
<div class="component-section" id="spokesSection">
    <div class="section-header">
        <h2>Spokes</h2>
        <div class="header-actions">
            <!-- NEW: Filter buttons -->
            <div class="filter-group">
                <button class="btn-filter active" data-filter="all" onclick="filterSpokes('all')">
                    All
                </button>
                <button class="btn-filter" data-filter="templates" onclick="filterSpokes('templates')">
                    Templates
                </button>
                <button class="btn-filter" data-filter="user" onclick="filterSpokes('user')">
                    My Spokes
                </button>
            </div>
            <button class="btn-primary" onclick="openSpokeTemplateSelector()">
                + Add New Spoke
            </button>
        </div>
    </div>

    <table class="component-table" id="spokesTable">
        <thead>
            <tr>
                <th>Name</th>
                <th>Material</th>
                <th>Shape</th>
                <th>Gauge</th>
                <th>Length</th>
                <th>Tension Range</th>
                <th>Type</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody id="spokesTableBody">
            <!-- Populated dynamically -->
        </tbody>
    </table>
</div>
```

**Update table rendering:**

```javascript
function renderSpokesTable(spokes) {
    const tbody = document.getElementById('spokesTableBody');
    tbody.innerHTML = '';

    spokes.forEach(spoke => {
        const row = document.createElement('tr');
        row.setAttribute('data-spoke-type', spoke.is_template ? 'template' : 'user');

        // Format gauge
        let gaugeDisplay = '';
        if (spoke.shape === 'round') {
            gaugeDisplay = `${spoke.gauge} mm`;
        } else {
            gaugeDisplay = `${spoke.thickness} × ${spoke.width} mm`;
        }

        // Type badge
        const typeBadge = spoke.is_template
            ? '<span class="badge badge-info">Template</span>'
            : '<span class="badge badge-success">User</span>';

        row.innerHTML = `
            <td>${spoke.name}</td>
            <td>${spoke.material}</td>
            <td>${spoke.shape}</td>
            <td>${gaugeDisplay}</td>
            <td>${spoke.length ? spoke.length + ' mm' : '-'}</td>
            <td>${spoke.min_tension}-${spoke.max_tension} kgf</td>
            <td>${typeBadge}</td>
            <td>
                <button onclick="viewSpoke('${spoke.id}')" class="btn-icon" title="View">
                    👁
                </button>
                ${!spoke.is_template ? `
                    <button onclick="deleteSpoke('${spoke.id}')" class="btn-icon btn-danger" title="Delete">
                        🗑
                    </button>
                ` : ''}
            </td>
        `;

        tbody.appendChild(row);
    });
}

function filterSpokes(filter) {
    // Update active filter button
    document.querySelectorAll('.btn-filter').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Show/hide rows
    const rows = document.querySelectorAll('#spokesTable tbody tr');
    rows.forEach(row => {
        const type = row.getAttribute('data-spoke-type');
        if (filter === 'all') {
            row.style.display = '';
        } else if (filter === 'templates' && type === 'template') {
            row.style.display = '';
        } else if (filter === 'user' && type === 'user') {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}
```

---

## API Endpoint Changes

**File:** `main.py`

### New Endpoints:

```python
@app.get("/api/spoke-templates")
async def get_spoke_templates_api():
    """Get all spoke templates for selection modal."""
    from database_manager import get_spoke_templates
    templates = get_spoke_templates()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "park_tool_designation": t.park_tool_designation,
            "material": t.material,
            "shape": t.shape,
            "gauge": t.gauge,
            "width": t.width,
            "thickness": t.thickness,
            "min_tension": t.min_tension,
            "max_tension": t.max_tension,
        }
        for t in templates
    ]

@app.get("/api/spoke-templates/{template_id}")
async def get_spoke_template_by_id(template_id: str):
    """Get specific spoke template details."""
    from database_manager import get_spoke_by_id
    template = get_spoke_by_id(template_id)
    if not template or not template.is_template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": str(template.id),
        "name": template.name,
        "park_tool_designation": template.park_tool_designation,
        "material": template.material,
        "shape": template.shape,
        "gauge": template.gauge,
        "width": template.width,
        "thickness": template.thickness,
        "min_tension": template.min_tension,
        "max_tension": template.max_tension,
        "conversion_table": template.conversion_table,
    }
```

### Update Existing Endpoint:

```python
@app.post("/spokes")
async def create_spoke_route(
    request: Request,
    name: str = Form(...),
    length: float = Form(None),  # Nullable
    is_template: bool = Form(False),
    template_id: str = Form(None),
    # Template fields (only for templates)
    park_tool_designation: str = Form(None),
    material: str = Form(None),
    shape: str = Form(None),
    gauge: float = Form(None),
    width: float = Form(None),
    thickness: float = Form(None),
    min_tension: float = Form(None),
    max_tension: float = Form(None),
    conversion_table: str = Form(None),  # JSON string
):
    """Create a new spoke (from template or standalone)."""
    try:
        # If template_id provided, inherit properties from template
        if template_id:
            template = get_spoke_by_id(template_id)
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")

            spoke = create_spoke(
                name=name,
                length=length,
                is_template=False,
                template_id=template_id,
                park_tool_designation=template.park_tool_designation,
                material=template.material,
                shape=template.shape,
                gauge=template.gauge,
                width=template.width,
                thickness=template.thickness,
                min_tension=template.min_tension,
                max_tension=template.max_tension,
                conversion_table=template.conversion_table,
            )
        else:
            # Manual creation (for templates or legacy)
            conversion_table_dict = json.loads(conversion_table) if conversion_table else None

            spoke = create_spoke(
                name=name,
                length=length,
                is_template=is_template,
                template_id=None,
                park_tool_designation=park_tool_designation,
                material=material,
                shape=shape,
                gauge=gauge,
                width=width,
                thickness=thickness,
                min_tension=min_tension,
                max_tension=max_tension,
                conversion_table=conversion_table_dict,
            )

        logger.info(f"Created spoke: {name} (ID: {spoke.id})")
        return RedirectResponse(url="/components", status_code=303)

    except Exception as e:
        logger.error(f"Error creating spoke: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/spokes/{spoke_id}")
async def delete_spoke_route(spoke_id: str):
    """Delete a spoke (templates cannot be deleted)."""
    spoke = get_spoke_by_id(spoke_id)
    if not spoke:
        raise HTTPException(status_code=404, detail="Spoke not found")

    if spoke.is_template:
        raise HTTPException(status_code=403, detail="Cannot delete spoke templates")

    # Check if used in any wheel builds
    is_locked = check_component_locked('spoke', spoke_id)
    if is_locked['locked']:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: used in {len(is_locked['builds'])} wheel builds"
        )

    delete_spoke(spoke_id)
    return {"status": "success"}
```

---

## CSS Styling

**File:** `static/styles.css`

Add styles for new UI elements:

```css
/* Template Badge */
.badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85em;
    font-weight: 600;
    margin-left: 8px;
}

.badge-info {
    background-color: #3498db;
    color: white;
}

.badge-success {
    background-color: #2ecc71;
    color: white;
}

/* Filter Buttons */
.filter-group {
    display: inline-flex;
    gap: 8px;
    margin-right: 16px;
}

.btn-filter {
    padding: 8px 16px;
    border: 1px solid #ddd;
    background-color: white;
    color: #333;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-filter:hover {
    background-color: #f5f5f5;
}

.btn-filter.active {
    background-color: #3498db;
    color: white;
    border-color: #3498db;
}

/* Template Selection Modal */
.template-list {
    max-height: 500px;
    overflow-y: auto;
    margin-top: 16px;
}

.template-group {
    margin-bottom: 24px;
}

.template-group h3 {
    font-size: 1.1em;
    color: #666;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #eee;
}

.template-item {
    display: flex;
    align-items: center;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.template-item:hover {
    background-color: #f8f9fa;
    border-color: #3498db;
}

.template-item input[type="radio"] {
    margin-right: 12px;
    cursor: pointer;
}

.template-item label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    cursor: pointer;
    margin: 0;
}

.template-specs {
    color: #666;
    font-size: 0.9em;
}

/* Tension Range Display */
.tension-range-display {
    padding: 12px;
    background-color: #f8f9fa;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-weight: 600;
    color: #333;
}

/* Read-only inputs styling */
input[readonly] {
    background-color: #f5f5f5;
    color: #666;
    cursor: not-allowed;
}
```

---

## Implementation Order

### Phase 1: Database & Models ✅
1. ✅ Update `seed_data.py` with 38 Park Tool spoke templates
2. Update `database_model.py` - Add new fields to Spoke model
3. Update `database_manager.py` - Modify create_spoke() and add new queries
4. Rebuild database from scratch (delete `wheel_builder.db`)
5. Run seed script: `python seed_data.py`
6. Verify: 38 templates + 5 hubs + 5 rims + 4 nipples

### Phase 2: Business Logic
7. Update `business_logic.py` - Replace `tm_reading_to_kgf()` with lookup implementation
8. Update `calculate_tension_range()` to use min/max from spoke
9. Test conversion accuracy against Park Tool data

### Phase 3: Backend API
10. Update `main.py` - Add `/api/spoke-templates` endpoint
11. Update `main.py` - Add `/api/spoke-templates/{id}` endpoint
12. Update `main.py` - Modify `/spokes` POST endpoint
13. Update `main.py` - Modify `/spokes/{id}` DELETE endpoint (prevent template deletion)

### Phase 4: Frontend - Template Selection
14. Create `templates/components/spoke_template_selector.html`
15. Add JavaScript for template selection modal
16. Wire up "Add New Spoke" button to open template selector

### Phase 5: Frontend - Spoke Modal
17. Update spoke modal HTML for template/user spoke differences
18. Add `openSpokeModalWithTemplate()` JavaScript function
19. Add `openSpokeModalForView()` JavaScript function
20. Update form submission to handle template_id

### Phase 6: Frontend - Spokes Table
21. Add filter buttons (All / Templates / My Spokes)
22. Update table rendering to show type badges
23. Prevent deletion of templates
24. Add `filterSpokes()` JavaScript function

### Phase 7: Styling
25. Add CSS for badges, filters, template list
26. Test responsive design

### Phase 8: Testing
27. Test template selection workflow
28. Test spoke creation from templates
29. Test tension conversions (compare to Park Tool values)
30. Test filtering (All / Templates / User)
31. Test edge cases (out-of-range TM readings, missing conversion tables)
32. Test wheel build integration (can spokes based on templates be used?)

---

## Testing Checklist

### Database Tests
- [ ] 38 spoke templates seeded correctly
- [ ] All templates have `is_template=True`
- [ ] All templates have `length=None`
- [ ] Conversion tables stored as valid JSON
- [ ] min_tension and max_tension calculated correctly from conversion tables

### Business Logic Tests
- [ ] Test exact TM reading matches (e.g., TM=20 for Steel Round 2.0mm → 77 kgf)
- [ ] Test interpolation (e.g., TM=20.5 for Steel Round 2.0mm → ~81 kgf)
- [ ] Test out-of-range warnings (TM below min or above max)
- [ ] Test calculate_tension_range() with new fields
- [ ] Verify exponential interpolation is more accurate than linear

### API Tests
- [ ] GET `/api/spoke-templates` returns 38 templates
- [ ] GET `/api/spoke-templates/{id}` returns template details
- [ ] POST `/spokes` creates user spoke from template
- [ ] POST `/spokes` inherits all properties from template
- [ ] DELETE `/spokes/{template_id}` is rejected (403 Forbidden)
- [ ] DELETE `/spokes/{user_spoke_id}` succeeds

### UI Tests
- [ ] Template selection modal opens
- [ ] Search filters templates correctly
- [ ] Templates grouped by material/shape
- [ ] Selecting template opens spoke modal with pre-filled data
- [ ] Name and length fields are editable
- [ ] Material, gauge, tension fields are read-only
- [ ] Template badge displays when viewing templates
- [ ] Filter buttons work (All / Templates / User)
- [ ] Templates show "Template" badge in table
- [ ] User spokes show "User" badge in table
- [ ] Delete button hidden for templates
- [ ] Viewing template shows all fields as disabled

### Integration Tests
- [ ] Create wheel build using spoke based on template
- [ ] Record tension readings for wheel build
- [ ] Verify TM readings convert correctly to kgf
- [ ] Verify tension range displays correctly
- [ ] Verify tension status indicators work (in_range, too_low, too_high)

---

## Rollback Plan

If issues arise:

1. **Database**: Keep backup of `wheel_builder.db` before changes
2. **Code**: Use git to revert to previous commit
3. **Seeds**: Old seed_data.py is in git history
4. **Formula**: Old tm_reading_to_kgf() preserved in git history

---

## Future Enhancements

### Short Term
- Add "duplicate spoke" feature (base new spoke on existing spoke)
- Export spoke library to JSON/CSV
- Import custom spoke specifications

### Long Term
- Support for custom/exotic spokes not in Park Tool tables
- Community-contributed spoke calibration data
- Integration with spoke manufacturer databases (DT Swiss, Sapim, etc.)
- Butted spoke support (track multiple gauge measurements)

---

## References

- Park Tool TM-1 Tension Meter: https://www.parktool.com/en-us/product/spoke-tension-meter-tm-1
- Conversion table source: Official Park Tool calibration data (provided by user)
- Wheel building standards: Professional Wheelbuilding Guide by Roger Musson

---

## Approval & Sign-off

**Technical Reviewer:** _Pending_
**User Acceptance:** _Pending_
**Implementation Start Date:** _TBD_
**Target Completion Date:** _TBD_

---

**Document Version:** 1.0
**Last Updated:** 2025-11-20
