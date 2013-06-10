from datetime import datetime


def to_datetime(milliseconds):
    """
    Converts milliseconds (e.g., from JS `new Date().getTime()` into Python datetime
    """
    try:
        value = datetime.fromtimestamp(int(milliseconds) / 1000)
        if isinstance(value, datetime):
            return value
    except:
        pass
    return milliseconds


def to_list(items):
    """
    Converts comma-delimited string into list of items
    """
    try:
        values = items.split(',')
        if isinstance(values, list):
            return values
    except:
        pass
    return items
