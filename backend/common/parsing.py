"""Input parsing helpers kept separate from endpoint modules."""

from datetime import datetime


def parse_datetime(value, field_name):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (AttributeError, ValueError):
        raise ValueError(f"{field_name} must be an ISO-8601 datetime")
