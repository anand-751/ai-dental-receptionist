from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class ConversationSession(BaseModel):
    session_id: str
    started_at: datetime
    expires_at: datetime
    messages: List[Dict] = Field(default_factory=list)

    # User profile
    user_profile: Optional[Dict] = None

    # state machine
    booking_state: Optional[str] = None
    reschedule_state: Optional[str] = None

    # temp data
    booking_data: Dict = Field(default_factory=dict)
    reschedule_data: Dict = Field(default_factory=dict)
