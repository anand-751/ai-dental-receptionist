def interpret_slot_with_llm(text: str, slots: list) -> int:
    """
    Use LLM to interpret vague slot choices like:
    - "third one"
    - "fourth slot"
    - "10 am slot"
    """

    slots_text = "\n".join(
        f"{i}: {s['date']} {s['time']}"
        for i, s in enumerate(slots)
    )

    prompt = f"""
    You are helping book an appointment.

    IMPORTANT:
    - Slot indexes are ZERO-BASED.
    - "first slot" = index 0
    - "second slot" = index 1
    - "third slot" = index 2
    - "fourth slot" = index 3
    - "fifth slot" = index 4
    - "sixth slot" = index 5


    Available slots:
    {slots_text}

    User message:
    "{text}"

    Return ONLY valid JSON in this exact format:
    {{"slot_index": number}}

    If unclear, return:
    {{"slot_index": -1}}
    """

        try:
            response = groq_chat(prompt)

            # 🔍 DEBUG LOG (KEEP THIS FOR NOW)
            print("🧠 LLM RAW RESPONSE:", response)

            # 🔒 ROBUST JSON EXTRACTION
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if not match:
                return -1

            data = json.loads(match.group())
            return int(data.get("slot_index", -1))

        except Exception as e:
            print("❌ LLM SLOT PARSE ERROR:", e)
            return -1
