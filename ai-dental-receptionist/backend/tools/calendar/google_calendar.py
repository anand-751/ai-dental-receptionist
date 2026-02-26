import json
from pathlib import Path
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from typing import Optional


SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = "Asia/Kolkata"

CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"
TOKEN_PATH = Path(__file__).parent / "token.json"


def load_google_oauth_config():
    with open(CREDENTIALS_PATH, "r") as f:
        data = json.load(f)

    config = data.get("web") or data.get("installed")
    return {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "token_uri": config["token_uri"],
    }


def get_calendar_service(refresh_token: str):
    oauth = load_google_oauth_config()

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=oauth["token_uri"],
        client_id=oauth["client_id"],
        client_secret=oauth["client_secret"],
        scopes=SCOPES,
    )

    creds.refresh(Request())

    return build(
        "calendar",
        "v3",
        credentials=creds,
        cache_discovery=False
    )


def book_slot(
    refresh_token: str,
    name: str,
    date: str,
    time: str,
    duration_minutes: int = 30,
    user_data: Optional[dict] = None,

) -> str:

    service = get_calendar_service(refresh_token)

    start_dt = datetime.fromisoformat(f"{date}T{time}")
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    user_data = user_data or {}

    final_name = name or user_data.get("name") or "Patient"
    final_phone = user_data.get("phone") or ""
    final_email = user_data.get("email") or ""

    description = (
        "Booked via AI Dental Receptionist\n\n"
        f"Name: {final_name}\n"
        f"Phone: {final_phone}\n"
        f"Email: {final_email}"
    )

    event = {
        "summary": f"Dental Appointment - {final_name}",
        "description": description,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return created_event["id"]





def cancel_slot(event_id: str, refresh_token: str = None):
    print("🗑️ Cancelling calendar event:", event_id)

    service = get_calendar_service(refresh_token)

    service.events().delete(
        calendarId="primary",
        eventId=event_id
    ).execute()

    print("✅ Calendar event cancelled")


def find_user_event(refresh_token, name, phone):
    service = get_calendar_service(refresh_token)

    now = datetime.utcnow().isoformat() + "Z"

    events = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=100,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    # Normalize phone
    phone_digits = ''.join(filter(str.isdigit, str(phone or "")))

    # Try last 10 digits (handles +91, 0 prefix, etc.)
    phone_last10 = phone_digits[-10:] if len(phone_digits) >= 10 else phone_digits

    for e in events.get("items", []):
        desc = e.get("description", "") or ""
        desc_digits = ''.join(filter(str.isdigit, desc))

        # Match using last 10 digits
        if phone_last10 and phone_last10 in desc_digits:
            start = e["start"]["dateTime"]
            dt = datetime.fromisoformat(start.replace("Z", ""))

            return {
                "event_id": e["id"],
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M")
            }

    return None
