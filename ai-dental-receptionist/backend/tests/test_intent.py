"""
Manual test runner for intent classification.
Run with:
    python3 -m backend.tests.test_intent
"""

from core.intent_classifier import classify_intent, intent_changed
from core.conversation_manager import create_session


def run_test(message: str, session):
    intent = classify_intent(message, session)
    changed = intent_changed(session, intent)

    print(f"User:    {message}")
    print(f"Intent:  {intent}")
    print(f"Changed: {changed}")
    print("-" * 50)


def main():
    print("\n🧪 INTENT CLASSIFIER TEST\n")

    session = create_session()

    test_inputs = [
        # "Hi, I want to know your clinic timings",
        # "What are your working hours?",
        # "How much do braces cost?",
        # "I want to book an appointment",
        # "Book a slot for tomorrow",
        # "Actually, I want to reschedule my appointment",
        # "I need to change my appointment date",
        # "Thanks"
        
    ]

    for text in test_inputs:
        run_test(text, session)

    print("\n📊 Final intent history:")
    print(getattr(session, "_intent_history", []))


if __name__ == "__main__":
    main()
