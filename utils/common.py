from datetime import datetime, timedelta

def datetime_to_seconds(datetime_string: str) -> int:
    """
    Parses a datetime string and calculates the total seconds from midnight.

    Args:
        datetime_string: The input datetime string in ISO 8601 format,
                         e.g., '2025-07-22T20:45:00+00:00'.

    Returns:
        The total number of seconds from midnight (00:00:00). Returns 0 if
        the input string is invalid.
    """
    try:
        # Parse the datetime string, handling the timezone offset
        dt_object = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S%z')

        # Extract the hour, minute, and second from the parsed datetime object
        hours = dt_object.hour
        minutes = dt_object.minute
        seconds = dt_object.second

        # Calculate the total number of seconds from midnight
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        return total_seconds

    except ValueError:
        # Handle cases where the datetime string format is incorrect
        print(f"Error: Invalid datetime format for input: '{datetime_string}'")
        return 0


def seconds_to_hhmm(seconds: int) -> str:
    """Convert solver time (seconds) to HH:MM format."""
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes = remainder // 60
    return f"{hours:02d}:{minutes:02d}"


def to_dict(obj):
    # Base case: if the object is a primitive type, return it
    if not hasattr(obj, '__dict__'):
        return obj

    # Create a new dictionary for the object's attributes
    result = {}
    for key, value in obj.__dict__.items():
        # If the value is another object, recurse
        if hasattr(value, '__dict__'):
            result[key] = to_dict(value)
        # If the value is a list of objects, convert each item
        elif isinstance(value, list) and all(hasattr(item, '__dict__') for item in value):
            result[key] = [to_dict(item) for item in value]
        else:
            result[key] = value

    return result