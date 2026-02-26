import json
from pathlib import Path

TOKEN_PATH = Path(__file__).parent / "token.json"


def get_refresh_token() -> str | None:
    if not TOKEN_PATH.exists():
        return None

    with open(TOKEN_PATH, "r") as f:
        data = json.load(f)

    return data.get("refresh_token")
