import re
from typing import Dict, Any

from logger_config import setup_logger

logger = setup_logger(__name__)


BLOCKED_MESSAGE = "Sorry, I cannot answer that request."
INVALID_MESSAGE = "Please enter a valid question."


BLOCKED_PATTERNS = [
    r"\bkill\b",
    r"\bmurder\b",
    r"\bstab\b",
    r"\bshoot\b",
    r"\bbomb\b",
    r"\bpoison\b",
    r"\btorture\b",
    r"\bassassinate\b",
    r"\bharm someone\b",
    r"\bhurt someone\b",
    r"\bmake a weapon\b",
    r"\bcreate a weapon\b",
    r"\bbuild a weapon\b",
    r"\bbuild a bomb\b",
    r"\bself harm\b",
    r"\bself-harm\b",
    r"\bsuicide\b",
]


ALLOWED_SAFETY_PHRASES = [
    "violence prevention",
    "report violence",
    "safety plan",
    "emergency help",
    "how to stay safe",
    "avoid violence",
    "prevent violence",
]


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)

    return text


def is_empty_or_invalid(question: str) -> bool:
    text = normalize_text(question)

    if not text:
        return True

    if len(text) < 2:
        return True

    return False


def is_allowed_safety_question(question: str) -> bool:
    text = normalize_text(question)

    for phrase in ALLOWED_SAFETY_PHRASES:
        if phrase in text:
            return True

    return False


def has_blocked_content(question: str) -> bool:
    text = normalize_text(question)

    if is_allowed_safety_question(text):
        return False

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text):
            return True

    return False


def precheck_question(question: str) -> Dict[str, Any]:
    """
    This checks the user's question before sending it to:
    1. uploaded documents
    2. database
    3. chatbot / LLM
    """

    if is_empty_or_invalid(question):
        logger.warning("Precheck failed: empty or invalid question")
        return {
            "allowed": False,
            "reason": "empty_or_invalid",
            "message": INVALID_MESSAGE
        }

    if has_blocked_content(question):
        logger.warning("Precheck failed: unsafe question blocked")
        return {
            "allowed": False,
            "reason": "unsafe_content",
            "message": BLOCKED_MESSAGE
        }

    logger.info("Precheck passed")
    return {
        "allowed": True,
        "reason": "safe",
        "message": "Question passed precheck."
    }