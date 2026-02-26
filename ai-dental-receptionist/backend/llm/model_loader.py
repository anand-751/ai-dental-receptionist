import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Load .env explicitly from backend directory
backend_dir = Path(__file__).resolve().parent.parent
env_file = backend_dir / ".env"
load_dotenv(env_file)

# Read key ONCE
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 🔒 Hard fail fast (never debug this again)
if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY is missing from .env file")

if not GROQ_API_KEY.startswith("gsk_"):
    raise RuntimeError(f"❌ Invalid GROQ_API_KEY loaded: {GROQ_API_KEY}")

def groq_chat(messages):
    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.2,
        max_tokens=512,
    )

    return response.choices[0].message.content
