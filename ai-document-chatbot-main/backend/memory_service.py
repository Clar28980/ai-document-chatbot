CONVERSATION_MEMORY = []
MAX_MEMORY_MESSAGES = 6


def get_memory_context():
    if not CONVERSATION_MEMORY:
        return "No previous conversation."

    memory_lines = []

    for item in CONVERSATION_MEMORY[-MAX_MEMORY_MESSAGES:]:
        memory_lines.append(f"User: {item['user']}")
        memory_lines.append(f"Clarence AI: {item['assistant']}")

    return "\n".join(memory_lines)


def save_to_memory(user_question: str, assistant_answer: str):
    CONVERSATION_MEMORY.append({
        "user": user_question,
        "assistant": assistant_answer
    })

    if len(CONVERSATION_MEMORY) > MAX_MEMORY_MESSAGES:
        CONVERSATION_MEMORY.pop(0)


def clear_memory():
    CONVERSATION_MEMORY.clear()


def get_memory_items():
    return CONVERSATION_MEMORY


def get_memory_count():
    return len(CONVERSATION_MEMORY)


def is_follow_up_question(question: str):
    q = question.lower().strip()

    follow_up_phrases = [
        "why",
        "why?",
        "why that",
        "why that?",
        "why this",
        "why this?",
        "which one",
        "which one?",
        "what service",
        "what service?",
        "what exact service",
        "what exact service?",
        "give the exact service",
        "give the exact service?",
        "give me the exact service",
        "give me the exact service?",
        "explain more",
        "explain more?",
        "explain that",
        "explain that?",
        "tell me more",
        "tell me more?",
        "how about that",
        "how about that?"
    ]

    return q in follow_up_phrases