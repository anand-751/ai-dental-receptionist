"""
Pydantic models for intent classification.
"""

from pydantic import BaseModel


class IntentResult(BaseModel):
    """Intent classification result"""
    intent: str
    confidence: float
    entities: dict = {}
    metadata: dict = {}
