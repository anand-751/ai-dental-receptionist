# import uuid
# from datetime import datetime
# from ..models.conversation import ConversationSession
# from ..utils.timers import get_expiry_time

# # In-memory session store
# SESSIONS = {}


# def create_session():
#     session_id = str(uuid.uuid4())

#     session = ConversationSession(
#         session_id=session_id,
#         started_at=datetime.utcnow(),
#         expires_at=get_expiry_time(),
#         messages=[]
#     )

#     SESSIONS[session_id] = session
#     return session


# def get_session(session_id: str):
#     session = SESSIONS.get(session_id)

#     # auto-expire safety
#     if session and session.expires_at < datetime.utcnow():
#         delete_session(session_id)
#         return None

#     return session


# def delete_session(session_id: str):
#     if session_id in SESSIONS:
#         del SESSIONS[session_id]


# def cleanup_expired_sessions():
#     now = datetime.utcnow()
#     expired = [
#         sid for sid, s in SESSIONS.items()
#         if s.expires_at < now
#     ]

#     for sid in expired:
#         delete_session(sid)




from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid

# ============================================
# MODELS
# ============================================

class ConversationSession(BaseModel):
    session_id: str
    started_at: datetime
    expires_at: datetime
    messages: List[Dict] = Field(default_factory=list)

    user_profile: Optional[Dict] = None

    booking_state: Optional[str] = None
    reschedule_state: Optional[str] = None

    booking_data: Dict = Field(default_factory=dict)
    reschedule_data: Dict = Field(default_factory=dict)


class UserProfileData(BaseModel):
    name: str
    phone: str
    email: str
    address: str
    city: str
    purpose_of_visit: str
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    notes: Optional[str] = None


# ============================================
# SESSION STORAGE (IN-MEMORY)
# ============================================

SESSIONS: Dict[str, ConversationSession] = {}


def create_session(user_profile: Optional[UserProfileData] = None) -> ConversationSession:
    session_id = str(uuid.uuid4())

    session = ConversationSession(
        session_id=session_id,
        started_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=2),
        user_profile=user_profile.dict() if user_profile else None
    )

    SESSIONS[session_id] = session
    print(f"✅ Session created: {session_id}")
    return session


def get_session(session_id: str) -> Optional[ConversationSession]:
    session = SESSIONS.get(session_id)

    if session and datetime.utcnow() > session.expires_at:
        delete_session(session_id)
        return None

    return session


def delete_session(session_id: str) -> bool:
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        print(f"🧹 Session deleted: {session_id}")
        return True
    return False


def cleanup_expired_sessions() -> int:
    now = datetime.utcnow()
    expired = [
        sid for sid, s in SESSIONS.items()
        if now > s.expires_at
    ]

    for sid in expired:
        delete_session(sid)

    return len(expired)


# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/conversation", tags=["conversation"])


# ============================================
# START CONVERSATION (REST)
# ============================================

@router.post("/start")
def start_conversation(
    user_data: Optional[UserProfileData] = Body(default=None)
):
    try:
        session = create_session(user_data)

        # Import here to avoid circular imports
        from llm.prompt_templates import opening_prompt
        from config import COMPANY_NAME

        opening_message = opening_prompt(COMPANY_NAME)

        session.messages.append({
            "role": "assistant",
            "content": opening_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {
            "status": "success",
            "session_id": session.session_id,
            "message": opening_message,
            "expires_at": session.expires_at.isoformat()
        }

    except Exception as e:
        print(f"❌ start_conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STREAM CONVERSATION (WEBSOCKET)
# ============================================

@router.websocket("/stream/{session_id}")
async def stream_conversation(websocket: WebSocket, session_id: str):
    session = get_session(session_id)

    if not session:
        await websocket.accept()
        await websocket.close(code=1008, reason="Session not found or expired")
        return

    await websocket.accept()
    print(f"🟢 WebSocket connected: {session_id}")

    try:
        # Lazy import to avoid circular dependency
        from core.stream_handler import handle_stream

        await handle_stream(websocket, session_id)

    except WebSocketDisconnect:
        print(f"🔌 Client disconnected: {session_id}")

    except Exception as e:
        print(f"❌ WebSocket error ({session_id}): {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass

    finally:
        print(f"🟡 WebSocket closed: {session_id}")


# ============================================
# CLEANUP SESSION
# ============================================

@router.post("/cleanup/{session_id}")
def cleanup_session(session_id: str):
    session = get_session(session_id)

    if not session:
        return {
            "status": "not_found",
            "session_id": session_id
        }

    delete_session(session_id)

    return {
        "status": "success",
        "session_id": session_id
    }


# ============================================
# DEBUG ENDPOINTS
# ============================================

@router.get("/session/{session_id}")
def get_session_info(session_id: str):
    session = get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "started_at": session.started_at.isoformat(),
        "expires_at": session.expires_at.isoformat(),
        "messages": len(session.messages),
        "has_user_profile": session.user_profile is not None
    }


@router.get("/sessions")
def list_sessions():
    active = []

    for sid, session in list(SESSIONS.items()):
        if datetime.utcnow() > session.expires_at:
            delete_session(sid)
            continue

        active.append({
            "session_id": sid,
            "expires_at": session.expires_at.isoformat(),
            "messages": len(session.messages),
            "user": session.user_profile.get("name") if session.user_profile else None
        })

    return {
        "total": len(active),
        "sessions": active
    }
