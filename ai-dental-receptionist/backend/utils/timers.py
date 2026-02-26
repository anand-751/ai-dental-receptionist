from datetime import datetime, timedelta
from ..config import SESSION_DURATION_SECONDS

def get_expiry_time():
    return datetime.utcnow() + timedelta(seconds=SESSION_DURATION_SECONDS)
