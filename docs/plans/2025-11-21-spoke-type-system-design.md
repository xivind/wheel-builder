# Spoke Type System with Conversion Table Design

**Date:** 2025-11-21
**Status:** Approved for Implementation

## Overview

Replace the current formula-based tension meter conversion with a table lookup system based on Park Tool's complete conversion data. Spoke configuration changes from fully user-customizable to type-selection based, ensuring accurate tension measurements for 36 different spoke types.

## Problem Statement

The current system uses an exponential formula to convert Park Tool TM-1 readings to kgf based only on spoke gauge (diameter). This approach:
- Only works for a limited number of spoke types
- Doesn't account for material differences (steel vs aluminum vs titanium)
- Doesn't account for spoke shape (round vs blade)
- Provides estimates rather than Park Tool's actual calibration data

## Solution

Implement a spoke type system with:
1. Pre-seeded database of 36 spoke types from Park Tool conversion table
2. Normalized conversion points for accurate TM→kgf lookups
3. Linear interpolation for readings between table values
4. User-friendly type selection with length as the only custom input

## Database Schema

### SpokeType Table (NEW)

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | String | Full name (e.g., "Steel Round 2.0mm") |
| `material` | String | "Steel", "Aluminum", "Titanium", "Carbon" |
| `shape` | String | "Round" or "Blade" |
| `dimensions` | String | "2.0mm" or "1.4 x 2.6mm" |
| `min_tm_reading` | Integer | Lowest TM reading in conversion table |
| `max_tm_reading` | Integer | Highest TM reading in conversion table |
| `min_tension_kgf` | Float | Lowest kgf in conversion table |
| `max_tension_kgf` | Float | Highest kgf in conversion table |

### ConversionPoint Table (NEW)

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key (auto-increment) |
| `spoke_type_id` | UUID | Foreign key to SpokeType |
| `tm_reading` | Integer | Park Tool TM-1 reading (0-50) |
| `kgf` | Integer | Corresponding tension in kgf |

**Constraints:**
- Unique constraint on (spoke_type_id, tm_reading)
- Index on spoke_type_id for fast lookups

**Data volume:** ~400 rows total (36 spoke types × ~10-15 points each)

### Spoke Table (UPDATED)

| Field | Type | Change |
|-------|------|--------|
| `id` | UUID | Unchanged |
| `spoke_type_id` | UUID | **NEW** - Foreign key to SpokeType (required) |
| `length` | Float | Unchanged |
| ~~`material`~~ | - | **REMOVED** - now from SpokeType |
| ~~`gauge`~~ | - | **REMOVED** - now from SpokeType |
| ~~`max_tension`~~ | - | **REMOVED** - now from SpokeType |

### TensionReading Table (UPDATED)

**New enum values:**

`range_status` field:
- Existing: 'in_range', 'over', 'under'
- **NEW:** 'below_table', 'above_table'

`average_deviation_status` field:
- Existing: 'in_range', 'over', 'under'
- **NEW:** 'unknown'

## Data Seeding

**Source:** `conversion_table.txt` (JSON with 36 spoke types)

**Seeding process:**
1. Parse conversion_table.txt JSON structure
2. For each spoke type:
   - Create SpokeType record:
     - `name` = key from JSON (e.g., "Steel Round 2.0mm")
     - `material` = parsed from name ("Steel", "Aluminum", "Titanium", detect "carbon")
     - `shape` = parsed from name ("Round" or "Blade")
     - `dimensions` = size portion of name
     - `min_tm_reading` = min(TM reading keys)
     - `max_tm_reading` = max(TM reading keys)
     - `min_tension_kgf` = kgf at min_tm_reading
     - `max_tension_kgf` = kgf at max_tm_reading
   - Create ConversionPoint records for each TM→kgf pair

**Execution:** Run during `initialize_database()`, idempotent (check if SpokeType table is empty)

**Example data:**
```
SpokeType: "Steel Round 2.0mm"
- material: "Steel"
- shape: "Round"
- dimensions: "2.0mm"
- min_tm_reading: 17, max_tm_reading: 28
- min_tension_kgf: 53, max_tension_kgf: 173

ConversionPoints:
- (17, 53)
- (18, 58)
- (19, 63)
- ...
- (28, 173)
```

## Tension Conversion Logic

### tm_reading_to_kgf() Function

**Old signature:**
```python
tm_reading_to_kgf(tm_reading, spoke_gauge) → float
```

**New signature:**
```python
tm_reading_to_kgf(tm_reading, spoke_type_id) → dict
```

**Return value:**
```python
{
    'kgf': float or None,
    'status': 'exact' | 'interpolated' | 'below_table' | 'above_table'
}
```

**Algorithm:**

1. **Fetch conversion points** - Query ConversionPoint table for spoke_type_id, ordered by tm_reading
2. **Check exact match** - If tm_reading matches exactly, return `{'kgf': value, 'status': 'exact'}`
3. **Check if out of range:**
   - If `tm_reading < min_tm_reading`: return `{'kgf': None, 'status': 'below_table'}`
   - If `tm_reading > max_tm_reading`: return `{'kgf': None, 'status': 'above_table'}`
   - Log warning with spoke type name and valid range
4. **Linear interpolation:**
   - Find adjacent points where `tm_low <= tm_reading <= tm_high`
   - Calculate: `ratio = (tm_reading - tm_low) / (tm_high - tm_low)`
   - Calculate: `kgf = kgf_low + ratio * (kgf_high - kgf_low)`
   - Return `{'kgf': round(kgf, 1), 'status': 'interpolated'}`

**No extrapolation:** Conversion curves are non-linear. Values outside the table cannot be accurately estimated.

**Caching:** Not implemented initially. Can add in-memory caching by spoke_type_id if performance becomes an issue.

### calculate_tension_range() Function

**Old logic:**
```python
max_tension = spoke.max_tension
min_tension = max_tension * 0.6  # 60% rule of thumb
# Calculate TM readings using inverse formula
```

**New logic:**
```python
return {
    'min_kgf': spoke.spoke_type.min_tension_kgf,
    'max_kgf': spoke.spoke_type.max_tension_kgf,
    'min_tm_reading': spoke.spoke_type.min_tm_reading,
    'max_tm_reading': spoke.spoke_type.max_tm_reading
}
```

**Removed:** All exponential formula coefficients and inverse calculations.

## TensionReading Creation Flow

**Process when user submits TM reading:**

1. Get spoke from wheel_build (via tension_session)
2. Call `tm_reading_to_kgf(tm_reading, spoke.spoke_type_id)`
3. **If status is 'below_table' or 'above_table':**
   - `estimated_tension_kgf` = NULL
   - `range_status` = status value ('below_table' or 'above_table')
   - `average_deviation_status` = 'unknown'
   - Do NOT include in average calculations
4. **If status is 'exact' or 'interpolated':**
   - `estimated_tension_kgf` = kgf value
   - Calculate `range_status` by comparing to tension range (normal logic)
   - Calculate `average_deviation_status` after all readings (normal logic)
   - Include in average calculations

## Average Deviation (±20%) Calculation

**Updated logic in analyze_tension_readings():**

1. **Filter readings:** Only include readings where `estimated_tension_kgf` IS NOT NULL
2. **Calculate average:** `avg = mean(valid_tensions)`
3. **Calculate ±20% limits:** `lower = avg * 0.8`, `upper = avg * 1.2`
4. **For each reading:**
   - If `estimated_tension_kgf` IS NULL: `average_deviation_status` = 'unknown'
   - Else: Compare to limits and set 'in_range', 'over', or 'under'

**Example:**
```
Left side:
- Spoke 1: 120 kgf → included
- Spoke 2: NULL (below_table) → excluded
- Spoke 3: 125 kgf → included
- Spoke 4: 118 kgf → included

Average = (120 + 125 + 118) / 3 = 121 kgf
±20% range = 96.8 - 145.2 kgf

Results:
- Spoke 1: 120 kgf → IN RANGE
- Spoke 2: NULL → UNKNOWN (grey badge)
- Spoke 3: 125 kgf → IN RANGE
- Spoke 4: 118 kgf → IN RANGE
```

## UI/UX Changes

### Spoke Configuration Form

**Current:** All fields manually entered (material, gauge, max_tension, length)

**New:** Two-step selection process

**Step 1: Select Spoke Type** (dropdown/searchable list)
- Shows all 36 SpokeType entries
- Format: "{name}" (e.g., "Steel Round 2.0mm")
- Optional: Group by material or provide search/filter

**Step 2: Enter Length**
- Single editable field for length (mm)

**Display after selection:**
```
Spoke Type:  Steel Round 2.0mm           [readonly badge]
Material:    Steel                        [readonly]
Dimensions:  2.0mm                        [readonly]
Range:       17 (53 kgf) - 28 (173 kgf)  [readonly]
Length:      260 mm                       [editable input]
```

**Config page spoke list:**
- Display: "Steel Round 2.0mm @ 260mm"
- Edit: Can only change length (spoke_type locked if used in builds)
- Delete: Standard locking rules apply

### Tension Reading Table Display

**Badge display for out-of-table readings:**

| Spoke | Side | TM Reading | Tension (kgf) | Range | Deviation |
|-------|------|------------|---------------|-------|-----------|
| 1 | L | 15 | - | BELOW RANGE (red) | UNKNOWN (grey) |
| 2 | L | 24 | 120.5 | IN RANGE (green) | IN RANGE (green) |
| 3 | L | 45 | - | ABOVE RANGE (red) | UNKNOWN (grey) |

**Normal readings** (exact/interpolated):
- Show kgf value normally
- Calculate range_status and average_deviation_status normally

**Out-of-table readings** (below_table/above_table):
- Tension column: "-" (no value)
- Range column: "BELOW RANGE" or "ABOVE RANGE" badge (red/warning)
- Deviation column: "UNKNOWN" badge (grey)

## API/Route Changes

### /config/spoke/create (POST)

**Old parameters:**
- material, gauge, max_tension, length

**New parameters:**
- spoke_type_id, length

**Validation:**
- spoke_type_id must exist in SpokeType table
- length > 0

### /config/spoke/<id>/update (POST)

**Editable:**
- length (only if spoke not locked)

**Not editable:**
- spoke_type_id (cannot change if used in builds)

### /config/spoke/form (GET)

**New functionality:**
- Load all SpokeType records
- Pass to template for dropdown/selection UI

## Migration Strategy

**Approach:** Fresh start (not in production)

- Drop existing database
- Create new schema with SpokeType and ConversionPoint tables
- Updated Spoke table schema (spoke_type_id required, removed fields)
- Updated TensionReading enum values
- Seed 36 spoke types on database initialization
- No data migration needed

## Implementation Notes

1. **Remove old code:**
   - Delete exponential formula coefficients from `tm_reading_to_kgf()`
   - Delete inverse formula from `calculate_tension_range()`
   - Remove spoke gauge-based logic

2. **Template updates:**
   - Update `templates/partials/spoke_form.html` for type selection
   - Update tension reading display to handle new badges

3. **Testing:**
   - Verify all 36 spoke types seed correctly
   - Test interpolation accuracy against known values
   - Test out-of-range handling (below_table, above_table)
   - Verify badge display for all status combinations
   - Verify ±20% calculation excludes NULL readings

4. **Future optimization:**
   - Add in-memory caching for ConversionPoint lookups if needed
   - Consider adding spoke type search/filter in UI if 36 types becomes unwieldy

## Success Criteria

- ✅ All 36 spoke types seeded from conversion_table.txt
- ✅ TM readings convert accurately using table lookup + interpolation
- ✅ Out-of-range readings show appropriate badges and warnings
- ✅ Users can only select from predefined spoke types
- ✅ Tension range displays both TM readings and kgf values
- ✅ Average deviation calculation excludes unmeasurable readings
- ✅ Old exponential formula completely removed
