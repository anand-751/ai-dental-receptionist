"""
Helper utilities and helper functions.
"""

from datetime import datetime


def format_time(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object to string"""
    return dt.strftime(format_str)


def parse_time(time_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse time string to datetime object"""
    return datetime.strptime(time_str, format_str)


def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    # Basic validation - can be expanded
    return len(phone.replace("-", "").replace(" ", "")) >= 10


def validate_email(email: str) -> bool:
    """Validate email address"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
