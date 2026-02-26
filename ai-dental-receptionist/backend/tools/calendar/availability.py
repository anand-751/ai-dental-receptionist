from datetime import datetime, timedelta
from typing import List, Tuple
import pytz

from ...config import (
    CLINIC_OPENING_HOUR,
    CLINIC_CLOSING_HOUR,
    CLINIC_SLOT_DURATION,
    CLINIC_TIMEZONE,
)

from .google_calendar import get_calendar_service


# ------------------------------------------------------
# Fetch busy ranges ONCE per day
# ------------------------------------------------------
def get_busy_ranges(
    service,
    start: datetime,
    end: datetime,
) -> List[Tuple[datetime, datetime]]:
    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": CLINIC_TIMEZONE,
        "items": [{"id": "primary"}],
    }

    response = service.freebusy().query(body=body).execute()
    busy = response.get("calendars", {}).get("primary", {}).get("busy", [])

    busy_ranges = []
    for item in busy:
        busy_ranges.append((
            datetime.fromisoformat(item["start"]),
            datetime.fromisoformat(item["end"]),
        ))

    return busy_ranges


# ------------------------------------------------------
# Overlap check
# ------------------------------------------------------
def overlaps(
    slot_start: datetime,
    slot_end: datetime,
    busy_ranges: List[Tuple[datetime, datetime]],
) -> bool:
    for busy_start, busy_end in busy_ranges:
        if slot_start < busy_end and slot_end > busy_start:
            return True
    return False


# ------------------------------------------------------
# MAIN: Get available slots
# ------------------------------------------------------
def get_available_slots(
    refresh_token: str,
    days_ahead: int = 3,
    limit: int = 6,
):
    """
    Returns ONLY future FREE slots.
    Past times from today are filtered out.
    """

    service = get_calendar_service(refresh_token)
    tz = pytz.timezone(CLINIC_TIMEZONE)

    now = datetime.now(tz)
    slots = []

    for day_offset in range(days_ahead):
        day = now.date() + timedelta(days=day_offset)

        day_start = tz.localize(datetime.combine(day, datetime.min.time())).replace(
            hour=CLINIC_OPENING_HOUR,
            minute=0,
            second=0,
            microsecond=0,
        )

        day_end = tz.localize(datetime.combine(day, datetime.min.time())).replace(
            hour=CLINIC_CLOSING_HOUR,
            minute=0,
            second=0,
            microsecond=0,
        )

        busy_ranges = get_busy_ranges(service, day_start, day_end)

        current = day_start

        while current + timedelta(minutes=CLINIC_SLOT_DURATION) <= day_end:
            slot_end = current + timedelta(minutes=CLINIC_SLOT_DURATION)

            # --------------------------------------------------
            # 🔥 CRITICAL FIX: skip past times (today only)
            # --------------------------------------------------
            if current <= now:
                current += timedelta(minutes=CLINIC_SLOT_DURATION)
                continue

            # --------------------------------------------------
            # Only include if NOT overlapping with bookings
            # --------------------------------------------------
            if not overlaps(current, slot_end, busy_ranges):
                slots.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "time": current.strftime("%H:%M"),
                })

                if len(slots) >= limit:
                    return slots

            current += timedelta(minutes=CLINIC_SLOT_DURATION)

    return slots


# ------------------------------------------------------
# Format slots for user / LLM
# ------------------------------------------------------
def format_slots(slots: list) -> str:
    if not slots:
        return "❌ No available slots found."

    first_date = datetime.strptime(
        slots[0]["date"], "%Y-%m-%d"
    ).strftime("%B %d, %Y")

    times = []
    for slot in slots:
        time_12h = datetime.strptime(
            slot["time"], "%H:%M"
        ).strftime("%I:%M %p").lstrip("0")
        times.append(time_12h)

    if len(times) == 1:
        times_str = times[0]
    else:
        times_str = ", ".join(times[:-1]) + f", and {times[-1]}"

    return (
        f"On {first_date}, the available slots are:\n\n"
        f"{times_str}."
    )
