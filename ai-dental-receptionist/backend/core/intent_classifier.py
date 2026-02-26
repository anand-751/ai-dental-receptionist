
from ..llm.model_loader import groq_chat
from ..llm.prompt_templates import INTENT_CLASSIFICATION_PROMPT

def classify_intent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": INTENT_CLASSIFICATION_PROMPT},
        {"role": "user", "content": user_message}
    ]

    intent = groq_chat(messages).strip().lower()
    return intent
