from peewee import *
import os

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', '/app/data/wheel_builder.db')
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

class Spoke(BaseModel):
    id = CharField(primary_key=True)
    material = CharField()
    gauge = FloatField()  # mm - for butted spokes, use thinnest diameter
    max_tension = FloatField()  # kgf
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
    estimated_tension_kgf = FloatField()
    range_status = CharField()  # in_range, over, under
    average_deviation_status = CharField()  # in_range, over, under

def initialize_database():
    """Create tables if they don't exist."""
    db.connect()
    db.create_tables([
        Hub, Rim, Spoke, Nipple,
        WheelBuild, TensionSession, TensionReading
    ], safe=True)
    db.close()
