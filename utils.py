# Any helper methods goes here

import uuid

def generate_uuid():
    """Generate a UUID string for database records.

    Returns:
        str: UUID4 as string
    """
    return str(uuid.uuid4())