from ..llm.model_loader import groq_chat
import json


def agent_route(user_text: str, history: list = None):

    history_text = ""
    if history:
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])

    prompt = f"""
You are routing requests for a dental clinic AI receptionist.

Conversation history:
{history_text}

User message:
"{user_text}"

First determine if the question is related to dental/oral care.

Examples of NON-DENTAL:
- headache
- eye problems
- skin treatment
- stomach pain
- fever
- body pain

If NON-DENTAL → domain = "non_dental"

If dental clinic related → domain = "dental"

Then choose an action based on the user's intent.

IMPORTANT RULES:

If the user says things like:
- "book karna hai"
- "appointment chahiye"
- "booking karni hai"
- "slot chahiye"
- "appointment book kar do"

Then action MUST be:
book_appointment

If the user says:
- "reschedule"
- "change appointment"
- "time change karna hai"

Then action MUST be:
reschedule_appointment

If the user says:
- "thanks"
- "ok thank you"
- "bye"
- "no thanks"

Then action MUST be:
end_call

Return ONLY JSON.

Example:
{{"domain":"dental","action":"book_appointment"}}

Example:
{{"domain":"non_dental","action":"clinic_question"}}
"""

    try:
        res = groq_chat(prompt)
        data = json.loads(res)

        domain = data.get("domain", "dental")
        action = data.get("action", "clinic_question")

        return domain, action

    except:
        return "dental", "clinic_question"