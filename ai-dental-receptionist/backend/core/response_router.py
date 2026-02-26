from ..rag.rag_pipeline import handle_rag_query
from ..tools.calendar.availability import get_available_slots, format_slots
from ..tools.calendar.google_calendar import book_slot, cancel_slot, find_user_event
from datetime import datetime
from ..llm.model_loader import groq_chat
import json
import re
from typing import Optional


# ======================================================
# LANGUAGE MIRROR HELPER (CORE FEATURE)
# ======================================================

def mirror_reply(user_text: str, base_message: str, language: str = "hi") -> str:
    """
        Convert system messages into natural spoken output.
        - Hindi mode → Hinglish (your tuned prompt)
        - English mode → Natural conversational English
        """

    if language == "hi":
        prompt = f"""
        You are a real Indian dental clinic receptionist speaking to patients in India.

        TASK:
        Convert the message below into NATURAL SPOKEN HINGLISH.

        STRICT RULES:
        - ALWAYS reply in Hinglish (Hindi + English mix)
        - NEVER reply in full English even if message is English
        - Convert everything into spoken Indian style
        - Sound like a polite, friendly North-Indian receptionist.
        - Keep sentences short, conversational and human.
        - Convert times into natural spoken form (examples below).

        TIME EXAMPLES:
        "09:30" -> "9:30 baje subah"
        "13:00" -> "1 baje dopahar"
        "16:00" -> "4 baje shaam"
        "4 PM" -> "4 baje shaam"

        MESSAGE:
        {base_message}

        Return ONLY the final Hinglish sentence (one short paragraph). Do NOT repeat the message or explain anything.
        """

    else:
        prompt = f"""
        You are a polite Indian dental clinic receptionist speaking in English.

        TASK:
        Convert the message below into NATURAL spoken English.

        STRICT RULES:
        - Reply ONLY in English
        - Keep tone warm, polite, and human
        - Keep sentences short and conversational
        - Sound like a real receptionist talking on phone
        - Convert times into natural spoken format

        TIME EXAMPLES:
        "09:30" -> "9:30 in the morning"
        "13:00" -> "1 in the afternoon"
        "16:00" -> "4 in the evening"
        "4 PM" -> "4 in the evening"

        MESSAGE:
        {base_message}

        Return ONLY the final spoken English sentence. Do NOT explain anything.
        """

    try:
        result = groq_chat(prompt).strip()
        if not result:
            return base_message
            return result
    except Exception:
        return base_message


# ======================================================
# TIME PARSING HELPERS
# ======================================================

NUM_WORDS = {
    # english words
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    # common hindi words (romanized)
    "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "paanchh": 5,
    "chhe": 6, "cheh": 6, "saat": 7, "aath": 8, "nau": 9, "dus": 10, "gyarah": 11, "barah": 12
}

def _word_to_hour(word: str) -> Optional[int]:
    w = word.strip().lower()
    return NUM_WORDS.get(w)

def parse_time_string_to_24h(time_str: str) -> str | None:
    """
    Accepts many formats:
    - "13:00", "1:00 PM", "1 PM", "1pm", "1.00 pm", "1 00 pm"
    - returns "HH:MM" in 24h or None if can't parse
    """
    if not time_str or not isinstance(time_str, str):
        return None

    s = time_str.strip().lower()
    s = s.replace(".", ":").replace("hrs", "").replace("hour", "")
    s = re.sub(r'\s+', ' ', s)

    # direct 24h like "13:00" or "09:30"
    m24 = re.match(r'^(\d{1,2}):(\d{2})$', s)
    if m24:
        h = int(m24.group(1))
        m = int(m24.group(2))
        if 0 <= h < 24 and 0 <= m < 60:
            return f"{h:02d}:{m:02d}"

    # patterns like "1:00 pm" or "1 pm" or "1 00 pm"
    m = re.match(r'^(\d{1,2})(?:[:\s]?(\d{2}))?\s*(am|pm)?$', s)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        period = m.group(3)

        if period == "pm" and hour != 12:
            hour += 12
        if period == "am" and hour == 12:
            hour = 0
        if 0 <= hour < 24 and 0 <= minute < 60:
            return f"{hour:02d}:{minute:02d}"

    # spelled-out words: "one pm", "ek baje"
    parts = s.split()
    # look for known number words and am/pm marker
    found_num = None
    found_period = None
    for p in parts:
        if p in ("am", "pm", "subah", "shaam", "sham", "dopahar"):
            if p in ("pm", "shaam", "sham", "dopahar"):
                found_period = "pm"
            elif p in ("am", "subah"):
                found_period = "am"
        else:
            val = _word_to_hour(p)
            if val:
                found_num = val

    if found_num:
        hour = found_num
        minute = 0
        if found_period == "pm" and hour != 12:
            hour += 12
        if found_period == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    return None

def extract_time_from_text(text: str) -> str | None:
    if not text:
        return None

    text = text.lower()

    text = text.replace("ke", " ")
    text = text.replace("ko", " ")

    # -------------------------
    # Normalize Hindi indicators
    # -------------------------
    period = None
    if "shaam" in text or "sham" in text or "dopahar" in text:
        period = "pm"
    elif "subah" in text:
        period = "am"

    text = text.replace("baje", "").replace(".", ":")
    text = re.sub(r'\s+', ' ', text)

    # -------------------------
    # Handle "dedh" = :30
    # -------------------------
    if "dedh" in text:
        hour_match = re.search(r'(\d{1,2})', text)
        if hour_match:
            hour = int(hour_match.group(1))
            minute = 30
        else:
            return None

        if period == "pm" and hour != 12:
            hour += 12
        if period == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    # -------------------------
    # Handle "sawa" = :15
    # -------------------------
    if "sawa" in text:
        hour_match = re.search(r'(\d{1,2})', text)
        if hour_match:
            hour = int(hour_match.group(1))
            minute = 15

            if period == "pm" and hour != 12:
                hour += 12
            if period == "am" and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute:02d}"

    # -------------------------
    # Handle "paune" = :45
    # paune 3 = 2:45
    # -------------------------
    if "paune" in text:
        hour_match = re.search(r'(\d{1,2})', text)
        if hour_match:
            hour = int(hour_match.group(1)) - 1
            minute = 45

            if hour < 0:
                hour = 0

            if period == "pm" and hour != 12:
                hour += 12
            if period == "am" and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute:02d}"

    # -------------------------
    # Normal numeric time
    # -------------------------
    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        p = match.group(3) or period

        if p == "pm" and hour != 12:
            hour += 12
        if p == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    return None


# ======================================================
# LLM SLOT RESOLVER (STRICT JSON ONLY)
# ======================================================

def resolve_slot_with_llm(user_text: str, slots: list) -> dict:
    """
    Asks LLM to pick one of the provided slots; LLM should return strict JSON.
    We'll normalize the returned time (12h or 24h) into 24h before using it.
    """
    slots_text = "\n".join(
        f"- {s['date']} {s['time']}"
        for s in slots
    )

    prompt = f"""
You are selecting an appointment slot.

Available slots (ONLY choose from these):
{slots_text}

User said:
"{user_text}"

Rules:
- Match the user's intent to ONE of the slots above.
- Do NOT invent new times.
- If the user says "3:30 PM" or "3:30 pm" match the closest listed slot.
- If confident, return that exact date & time.
- If not confident, return nulls.

Return ONLY JSON.

Format:
{{"date": "YYYY-MM-DD", "time": "HH:MM"}}
or
{{"date": null, "time": null}}
"""

    try:
        response = groq_chat(prompt)
        data = json.loads(response)
        # Normalize time if present (LLM may return "1:00 PM" etc.)
        if data and data.get("time"):
            normalized = parse_time_string_to_24h(str(data["time"]))
            data["time"] = normalized
        return data
    except Exception:
        return {"date": None, "time": None}


# ======================================================
# MAIN ROUTER
# ======================================================

async def route_intent(intent: str, text: str, session):

    if session.get("booking_state") == "awaiting_slot":
        intent = "booking"

    if session.get("reschedule_state") == "awaiting_new_slot":
        intent = "reschedule"

    # ---------------- GREETING ----------------
    if intent == "greeting":
        base = "Hi, I'm the AI receptionist from Bright Dental Clinic. How may I assist you today?"
        return mirror_reply(text, base)

    # ---------------- ENQUIRY ----------------
    if intent in ["enquiry", "pricing"]:
        answer = handle_rag_query(text)
        base = f"{answer}\n\nAur kuch help chahiye?"
        return mirror_reply(text, base)

    # ---------------- BOOKING ----------------
    if intent == "booking":

        session.setdefault("booking_state", None)
        session.setdefault("booking_data", {})
        session.setdefault("clinic_refresh_token", None)

        refresh_token = session["clinic_refresh_token"]

        # STEP 1 — SHOW SLOTS
        if session["booking_state"] is None:
            if not refresh_token:
                return mirror_reply(text, "Sorry, appointment booking is currently unavailable.")

            slots = get_available_slots(refresh_token=refresh_token)
            session["booking_data"]["slots"] = slots
            session["booking_state"] = "awaiting_slot"

            # show user-friendly 12h times (for LLM rewriting & speech)
            def to_12h(t):
                return datetime.strptime(t, "%H:%M").strftime("%I:%M %p").lstrip("0")

            slots_text = ", ".join([to_12h(s['time']) for s in slots])
            date_str = slots[0]['date'] if slots else ""

            base = f"""
Available appointment times:
Date: {date_str}
Times: {slots_text}

Aap kaunsa time lena chahenge?
"""
            return mirror_reply(text, base)

        # STEP 2 — SLOT SELECTION
        if session["booking_state"] == "awaiting_slot":
            slots = session["booking_data"]["slots"]

            # 1) deterministic extraction first
            extracted_time = extract_time_from_text(text)
            resolved = {"date": None, "time": None}

            if extracted_time:
                print(f"[booking] extracted_time(from user) = {extracted_time}")
                # exact match only
                slot = next((s for s in slots if s["time"] == extracted_time), None)
                if slot:
                    resolved = {"date": slot["date"], "time": slot["time"]}
                else:
                    # no exact match — let LLM try (but require normalization)
                    print("[booking] no exact slot match for extracted_time; falling back to LLM resolver")
                    resolved = resolve_slot_with_llm(text, slots)
            else:
                # LLM fallback (user said something like "the third one" etc.)
                resolved = resolve_slot_with_llm(text, slots)

            print(f"[booking] resolved = {resolved}")

            # Validate resolved
            if not resolved or not resolved.get("date") or not resolved.get("time"):
                examples = [
                    "1 baje dopahar",
                    "shaam 4 baje",
                    "dedh 1 baje",
                    "11:30 AM"
                ]

                base = f"""
            Mujhe exact time samajh nahi aaya.
            Aap is tarah bol sakte ho:
            {", ".join(examples)}
            """
                return mirror_reply(text, base)


            # final lookup
            slot = next(
                (s for s in slots if s["date"] == resolved["date"] and s["time"] == resolved["time"]),
                None
            )

            if not slot:
                def to_12h(t):
                    return datetime.strptime(t, "%H:%M").strftime("%I:%M %p").lstrip("0")

                available_times = ", ".join([to_12h(s["time"]) for s in slots])

                base = f"""
            Woh time available nahi hai.
            Available times hain:
            {available_times}

            Inme se koi ek time bol dijiye.
            """
                return mirror_reply(text, base)

            try:
                profile = session.get("user_profile") or {}
                name = profile.get("name") or "Patient"
                phone = profile.get("phone") or ""
                email = profile.get("email") or None

                event_id = book_slot(
                    refresh_token=refresh_token,
                    name=name,
                    date=slot["date"],
                    time=slot["time"],
                    user_data={
                        "name": name,
                        "phone": phone,
                        "email": email
                    }
                )

                time_12h = datetime.strptime(slot["time"], "%H:%M").strftime("%I:%M %p").lstrip("0")
                date_str = datetime.strptime(slot["date"], "%Y-%m-%d").strftime("%B %d, %Y")

                session["booking_state"] = None
                session["booking_data"].clear()

                base = f"Haan ji, aapki appointment confirm ho gayi hai: {date_str} ko {time_12h}."
                return {
                    "type": "booking_confirmation",
                    "message": mirror_reply(text, base),
                    "booking": {
                        "date": date_str,
                        "time": time_12h,
                        "event_id": event_id
                    }
                }

            except Exception as e:
                print("[booking] exception:", e)
                return mirror_reply(text, "Maaf kijiye, booking karne mein dikkat aa gayi. Kripya thodi der baad try karein.")

    # ---------------- RESCHEDULE ----------------
    if intent == "reschedule":

        session.setdefault("reschedule_state", None)
        session.setdefault("reschedule_data", {})

        refresh_token = session.get("clinic_refresh_token")
        profile = session.get("user_profile", {})

        if not refresh_token:
            return mirror_reply(text, "Sorry, rescheduling is currently unavailable.")

        name = session.get("patient_name")
        phone = session.get("patient_phone")

        # STEP 1 — find user's current appointment
        if session["reschedule_state"] is None:

            event = find_user_event(refresh_token=refresh_token, name=name, phone=phone)

            if not event:
                base = "Mujhe aapki koi pehle wali appointment nahi mili. Kripya ensure karein ki wahi phone number use hua tha."
                return mirror_reply(text, base)

            session["reschedule_data"]["event_id"] = event["event_id"]
            session["reschedule_data"]["old_time"] = event["time"]
            session["reschedule_data"]["old_date"] = event["date"]
            session["reschedule_state"] = "awaiting_new_slot"

            slots = get_available_slots(refresh_token=refresh_token)
            filtered = [
                s for s in slots
                if (s["date"] > event["date"]) or
                (s["date"] == event["date"] and s["time"] > event["time"])
            ]
            session["reschedule_data"]["slots"] = filtered[:6]

            def to_12h(t):
                return datetime.strptime(t, "%H:%M").strftime("%I:%M %p").lstrip("0")

            slots_text = ", ".join([to_12h(s['time']) for s in filtered[:6]])
            base = f"Maine aapki purani appointment payi: {event['date']} ko {datetime.strptime(event['time'],'%H:%M').strftime('%I:%M %p').lstrip('0')}. Naye available times: {slots_text}. Aap kaunsa naya time chahenge?"
            return mirror_reply(text, base)

        # STEP 2 — user selects new slot
        if session["reschedule_state"] == "awaiting_new_slot":

            slots = session["reschedule_data"]["slots"]
            extracted_time = extract_time_from_text(text)
            resolved = {"date": None, "time": None}

            if extracted_time:
                print(f"[reschedule] extracted_time = {extracted_time}")
                slot = next((s for s in slots if s["time"] == extracted_time), None)
                if slot:
                    resolved = {"date": slot["date"], "time": slot["time"]}
                else:
                    resolved = resolve_slot_with_llm(text, slots)
            else:
                resolved = resolve_slot_with_llm(text, slots)

            print(f"[reschedule] resolved = {resolved}")

            if not resolved or not resolved.get("date") or not resolved.get("time"):
                return mirror_reply(text, "Mujhe samajh nahi aaya kaunsa naya time chahiye. Kripya seedhe '3 PM' ya '11:30 AM' bolein.")

            slot = next(
                (s for s in slots if s["date"] == resolved["date"] and s["time"] == resolved["time"]),
                None
            )

            if not slot:
                return mirror_reply(text, "Woh slot ab available nahi hai. Kripya koi aur choose karein.")

            try:
                old_event_id = session["reschedule_data"]["event_id"]
                cancel_slot(old_event_id, refresh_token=refresh_token)

                event_id = book_slot(
                    refresh_token=refresh_token,
                    name=name,
                    date=slot["date"],
                    time=slot["time"],
                    user_data={
                        "name": profile.get("name"),
                        "phone": profile.get("phone"),
                        "email": profile.get("email") or None
                    }
                )

                time_12h = datetime.strptime(slot["time"], "%H:%M").strftime("%I:%M %p").lstrip("0")
                date_str = datetime.strptime(slot["date"], "%Y-%m-%d").strftime("%B %d, %Y")

                session["reschedule_state"] = None
                session["reschedule_data"].clear()

                base = f"Haan ji, aapki nayi appointment confirm ho gayi: {date_str} ko {time_12h}."
                return mirror_reply(text, base)

            except Exception as e:
                print("[reschedule] exception:", e)
                return mirror_reply(text, f"Reschedule failed: {str(e)}")

    # default fallback
    return mirror_reply(text, "Maaf kijiye, main samajh nahi paayi. Thoda clearly bolein, please.")
