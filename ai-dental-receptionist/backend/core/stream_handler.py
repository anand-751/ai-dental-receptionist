# stream.handler.py
from fastapi import WebSocket, WebSocketDisconnect
import json
import traceback

from .intent_classifier import classify_intent, intent_changed
from .response_router import route_intent
from .conversation_manager import get_session, delete_session, create_session_if_missing  # optional helper


async def handle_stream(websocket: WebSocket, session_id: str):
    # 🔴 THIS LINE IS NON-NEGOTIABLE
    await websocket.accept()
    print(f"🟢 WebSocket accepted for session {session_id}")

    session = get_session(session_id)
    if not session:
        await websocket.send_json({"error": "session not found"})
        await websocket.close()
        return

    buffer = ""
    last_sent_message = None

    try:
        while True:
            data = await websocket.receive_text()
            if not data:
                continue

            try:
                payload = json.loads(data)
                user_input = payload.get("user_input", "").strip()
            except json.JSONDecodeError:
                user_input = data.strip()

            if not user_input:
                continue

            buffer = user_input

            if buffer.endswith((".", "?", "!")) or len(buffer) > 20:
                if buffer == last_sent_message:
                    buffer = ""
                    continue

                intent = classify_intent(buffer, session)
                response = await route_intent(intent, buffer, session)

                await websocket.send_json({
                    "response": response,
                    "session_id": session_id
                })

                last_sent_message = buffer
                buffer = ""

    except WebSocketDisconnect:
        print(f"🔌 Client disconnected {session_id}")
        delete_session(session_id)

    except Exception as e:
        print(f"❌ WS crash {session_id}:", e)
        delete_session(session_id)
        await websocket.close()



