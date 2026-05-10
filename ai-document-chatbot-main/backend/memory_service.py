CONVERSATION_MEMORY = []
MAX_MEMORY_MESSAGES = 8

from logger_config import setup_logger

logger = setup_logger(__name__)


def get_memory_context():
    if not CONVERSATION_MEMORY:
        return "No previous conversation."

    memory_lines = []

    for item in CONVERSATION_MEMORY[-MAX_MEMORY_MESSAGES:]:
        memory_lines.append(f"User: {item['user']}")
        memory_lines.append(f"Clarence AI: {item['assistant']}")

    return "\n".join(memory_lines)


def save_to_memory(user_question: str, assistant_answer: str):
    if not user_question or not assistant_answer:
        return

    CONVERSATION_MEMORY.append({
        "user": user_question,
        "assistant": assistant_answer
    })

    if len(CONVERSATION_MEMORY) > MAX_MEMORY_MESSAGES:
        CONVERSATION_MEMORY.pop(0)

    logger.info("Saved conversation to memory. Total memory: %s", len(CONVERSATION_MEMORY))


def clear_memory():
    CONVERSATION_MEMORY.clear()
    logger.info("Conversation memory cleared")


def get_memory_items():
    return CONVERSATION_MEMORY


def get_memory_count():
    return len(CONVERSATION_MEMORY)


def is_follow_up_question(question: str):
    q = question.lower().strip()

    follow_up_words = [
        "he",
        "she",
        "her",
        "his",
        "him",
        "they",
        "them",
        "their",
        "that",
        "this",
        "those",
        "these",
        "it"
    ]

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
        "how about that?",
        "and what",
        "how about",
        "what about",
        "what are",
        "what is",
        "where did",
        "when did"
    ]

    if q in follow_up_phrases:
        return True

    for phrase in follow_up_phrases:
        if q.startswith(phrase):
            return True

    for word in follow_up_words:
        if f" {word} " in f" {q} ":
            return True

    return False