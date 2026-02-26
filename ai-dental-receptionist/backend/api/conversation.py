from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import uuid
import asyncio

from backend.core.intent_classifier import classify_intent
from backend.core.response_router import route_intent
from backend.tools.calendar.token_store import get_refresh_token

from backend.core.call_manager import (
    can_accept_call,
    add_active_call,
    remove_active_call,
    add_to_queue,
    pop_next_from_queue,   # ← IMPORTANT (you missed this)
    active_calls,
    waiting_queue,
)

from backend.core.profile_store import LATEST_PROFILE

router = APIRouter(
    prefix="/conversation",
    tags=["conversation"]
)


@router.websocket("/stream")
async def conversation_stream(websocket: WebSocket):
    await websocket.accept()
    client_id = str(uuid.uuid4())

    # ---------------- QUEUE LOGIC ----------------
    if not can_accept_call():
        add_to_queue(client_id)
        try:
            await websocket.send_json({"type": "busy"})
        except:
            return

        # Wait until promoted
        while client_id in waiting_queue:
            await asyncio.sleep(1)

    add_active_call(client_id)
    print(f"🟢 Active calls: {len(active_calls)}")

    # SEND START SIGNAL
    try:
        await websocket.send_json({"type": "start"})
    except:
        return

    refresh_token = get_refresh_token()

    profile = LATEST_PROFILE if LATEST_PROFILE else {
        "name": "Guest",
        "phone": None,
        "email": None,
    }

    session = {
        "booking_state": None,
        "booking_data": {},
        "reschedule_state": None,
        "reschedule_data": {},
        "clinic_refresh_token": refresh_token,
        "user_profile": profile,
        "patient_name": profile.get("name"),
        "patient_phone": profile.get("phone"),
    }

    print("🔐 SESSION STARTED WITH PROFILE:", profile)

    try:
        while True:
            raw = await websocket.receive_text()
            print(f"⬅️ RAW RECV: {raw}")

            try:
                payload = json.loads(raw)
            except Exception as e:
                print(f"JSON Parse Error: {e}")
                continue

            incoming_profile = payload.get("user_profile")

            if incoming_profile and incoming_profile.get("name"):
                session["user_profile"] = incoming_profile
                session["patient_name"] = incoming_profile.get("name")
                session["patient_phone"] = incoming_profile.get("phone")

                print("✅ PROFILE UPDATED FROM PAYLOAD:", session["user_profile"])

            user_input = payload.get("user_input", "").strip()
            if not user_input:
                continue

            force_process = (
                session.get("booking_state") == "awaiting_slot" or
                session.get("reschedule_state") is not None
            )

            if force_process or user_input.endswith((".", "?", "!")) or len(user_input) > 15:
                try:
                    intent = classify_intent(user_input)

                    print(f"🤖 Processing '{intent}' for user:", session["patient_name"])

                    response = await route_intent(
                        intent=intent,
                        text=user_input,
                        session=session
                    )

                    # GUARANTEE response is never None
                    if response is None:
                        response = "Sorry, I couldn't process that. Please try again."

                    await websocket.send_json({"response": response})

                except Exception as route_err:
                    print(f"❌ ROUTING ERROR: {route_err}")
                    await websocket.send_json({
                        "response": "I encountered an error processing that."
                    })

    except WebSocketDisconnect:
        print(f"🔌 Client {client_id} disconnected")
        remove_active_call(client_id)

        # 🔥 Promote next queued client
        next_client = pop_next_from_queue()
        if next_client:
            print(f"🚀 Promoted from queue: {next_client}")

    except Exception as e:
        print(f"💀 CRITICAL WS ERROR: {e}")
        remove_active_call(client_id)

        # 🔥 Promote next queued client
        next_client = pop_next_from_queue()
        if next_client:
            print(f"🚀 Promoted from queue: {next_client}")
