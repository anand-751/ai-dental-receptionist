import os
from dotenv import load_dotenv

load_dotenv()

# ---- GROQ ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---- GEMINI (ADD THIS) ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SESSION_DURATION_SECONDS = int(
    os.getenv("SESSION_DURATION_SECONDS", 120)  # 2 minutes default
)

COMPANY_NAME = os.getenv("COMPANY_NAME", "Bright Dental Clinic")

# ---- CLINIC OPERATIONAL HOURS ----
CLINIC_OPENING_HOUR = 9  # 9:00 AM
CLINIC_CLOSING_HOUR = 18  # 6:00 PM
CLINIC_SLOT_DURATION = 30  # minutes
CLINIC_TIMEZONE = "Asia/Kolkata"

