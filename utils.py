# Any helper methods goes here



def generate_unique_id():
    """
    Generate unique ID using UUID + timestamp.
    Format: GC-{uuid[:6]}{timestamp[-4:]}
    Example: GC-a3f8e52468
    """
    uuid_part = uuid.uuid4().hex[:6]
    timestamp_part = str(int(datetime.now().timestamp()))[-4:]
    return f"GC-{uuid_part}{timestamp_part}"