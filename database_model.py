from peewee import *
import os

# Database configuration
# Default to ~/code/container_data/wheel_builder.db (shared with Docker)
DEFAULT_DB_PATH = os.path.expanduser('~/code/container_data/wheel_builder.db')
DATABASE_PATH = os.getenv('DATABASE_PATH', DEFAULT_DB_PATH)

# Ensure directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

db = SqliteDatabase(DATABASE_PATH)

class BaseModel(Model):
    """Base model with common configuration."""
    class Meta:
        database = db

# Component Library Models

class Hub(BaseModel):
    id = CharField(primary_key=True)
    make = CharField()
    model = CharField()
    type = CharField()  # front or rear
    old = FloatField()  # over locknut distance
    left_flange_diameter = FloatField()
    right_flange_diameter = FloatField()
    left_flange_offset = FloatField()
    right_flange_offset = FloatField()
    spoke_hole_diameter = FloatField()
    number_of_spokes = IntegerField()  # number of spoke holes in the hub

class Rim(BaseModel):
    id = CharField(primary_key=True)
    make = CharField()
    model = CharField()
    type = CharField()  # symmetric or asymmetric
    erd = FloatField()  # effective rim diameter
    osb = FloatField()  # offset spoke bed
    inner_width = FloatField()
    outer_width = FloatField()
    holes = IntegerField()
    material = CharField()

class SpokeType(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()  # e.g., "Steel Round 2.0mm"
    material = CharField()  # Steel, Aluminum, Titanium, Carbon
    shape = CharField()  # Round or Blade
    dimensions = CharField()  # "2.0mm" or "1.4 x 2.6mm"
    min_tm_reading = IntegerField()  # Lowest TM reading in conversion table
    max_tm_reading = IntegerField()  # Highest TM reading in conversion table
    min_tension_kgf = FloatField()  # Lowest kgf in conversion table
    max_tension_kgf = FloatField()  # Highest kgf in conversion table

class ConversionPoint(BaseModel):
    id = AutoField()  # Auto-incrementing primary key
    spoke_type_id = CharField()  # Foreign key to SpokeType
    tm_reading = IntegerField()  # Park Tool TM-1 reading (0-50)
    kgf = IntegerField()  # Corresponding tension in kgf

    class Meta:
        database = db
        indexes = (
            (('spoke_type_id', 'tm_reading'), True),  # Unique constraint
        )

class Spoke(BaseModel):
    id = CharField(primary_key=True)
    spoke_type_id = CharField()  # Foreign key to SpokeType, required
    length = FloatField()  # mm

class Nipple(BaseModel):
    id = CharField(primary_key=True)
    material = CharField()
    diameter = FloatField()  # mm
    length = FloatField()  # mm
    color = CharField()

# Wheel Build Models

class WheelBuild(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()
    status = CharField(default='draft')  # draft, in_progress, completed
    hub_id = CharField(null=True)
    rim_id = CharField(null=True)
    spoke_left_id = CharField(null=True)
    spoke_right_id = CharField(null=True)
    nipple_id = CharField(null=True)
    lacing_pattern = CharField(null=True)
    spoke_count = IntegerField(null=True)
    actual_spoke_length_left = FloatField(null=True)
    actual_spoke_length_right = FloatField(null=True)
    comments = TextField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class TensionSession(BaseModel):
    id = CharField(primary_key=True)
    wheel_build_id = CharField()
    session_name = CharField()
    session_date = DateTimeField()
    notes = TextField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

class TensionReading(BaseModel):
    id = CharField(primary_key=True)
    tension_session_id = CharField()
    spoke_number = IntegerField()
    side = CharField()  # left or right
    tm_reading = FloatField()  # Park Tool TM-1 reading
    estimated_tension_kgf = FloatField(null=True)
    range_status = CharField()  # in_range, over, under
    average_deviation_status = CharField()  # in_range, over, under

def initialize_database():
    """Create tables if they don't exist. Assumes database connection is already open."""
    db.connect(reuse_if_open=True)
    db.create_tables([
        Hub, Rim, SpokeType, ConversionPoint, Spoke, Nipple,
        WheelBuild, TensionSession, TensionReading
    ], safe=True)

    # Seed spoke types if table is empty
    if SpokeType.select().count() == 0:
        from seed_spoke_types import seed_spoke_types
        seed_spoke_types()
