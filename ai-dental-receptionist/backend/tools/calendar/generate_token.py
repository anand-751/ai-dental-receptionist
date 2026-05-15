import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

CURRENT_DIR = Path(__file__).parent
CREDENTIALS_FILE = CURRENT_DIR / "credentials.json"
TOKEN_FILE = CURRENT_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def generate_refresh_token():

    if not CREDENTIALS_FILE.exists():
        print(f"❌ Error: {CREDENTIALS_FILE} not found!")
        return

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES
    )

    # IMPORTANT PARAMETERS
    creds = flow.run_local_server(
        port=0,
        access_type="offline",  
        prompt="consent"         
    )

    print("\n--- AUTHENTICATION SUCCESSFUL ---")

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"✅ Token saved to: {TOKEN_FILE}")

    print("\n🔑 REFRESH TOKEN:")
    print(creds.refresh_token)


if __name__ == "__main__":
    generate_refresh_token()