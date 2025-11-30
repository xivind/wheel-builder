# Any helper methods goes here

import uuid

def generate_uuid():
    """Generate a UUID string for database records.

    Returns:
        str: UUID4 as string
    """
    return str(uuid.uuid4())

def empty_to_none(value):
    """Convert empty string or whitespace-only string to None.

    This ensures we store NULL in the database instead of empty strings,
    maintaining data integrity and query consistency.

    Args:
        value: Any value, typically a string from form input

    Returns:
        None if value is empty/whitespace/None, otherwise the value
    """
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value