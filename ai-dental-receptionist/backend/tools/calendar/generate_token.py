import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# This finds the directory where THIS script is located
CURRENT_DIR = Path(__file__).parent
CREDENTIALS_FILE = CURRENT_DIR / "credentials.json"
TOKEN_FILE = CURRENT_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def generate_refresh_token():
    if not CREDENTIALS_FILE.exists():
        print(f"❌ Error: {CREDENTIALS_FILE} not found!")
        return

    # Use the absolute path
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE), 
        scopes=SCOPES
    )
    
    # This will open your browser
    creds = flow.run_local_server(port=0)
    
    print("\n--- AUTHENTICATION SUCCESSFUL ---")
    
    # Save the full credentials (including refresh token) to token.json
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    
    print(f"✅ Success! Token saved to: {TOKEN_FILE}")
    print(f"Refresh Token: {creds.refresh_token}")

if __name__ == "__main__":
    generate_refresh_token()