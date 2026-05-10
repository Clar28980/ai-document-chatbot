import os
import re
from dotenv import load_dotenv

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from memory_service import get_memory_context, is_follow_up_question
from logger_config import setup_logger


load_dotenv()

logger = setup_logger(__name__)

LLM_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

FALLBACK_ANSWER = "I could not find that information."

if not ANTHROPIC_API_KEY:
    logger.error("ANTHROPIC_API_KEY is missing. Check your backend/.env file.")


llm = ChatAnthropic(
    model=LLM_MODEL,
    temperature=0,
    max_tokens=350,
    anthropic_api_key=ANTHROPIC_API_KEY
)


def clean_answer(answer) -> str:
    if not answer:
        return FALLBACK_ANSWER

    if hasattr(answer, "content"):
        answer = answer.content
    else:
        answer = str(answer)

    answer = answer.strip()

    prefixes = [
        "Answer:",
        "Final answer:",
        "Clarence AI:",
        "AI:",
        "Bot:"
    ]

    for prefix in prefixes:
        if answer.startswith(prefix):
            answer = answer.replace(prefix, "", 1).strip()

    intro_patterns = [
        r"^\s*based on the cv,?\s*",
        r"^\s*according to the cv,?\s*",
        r"^\s*from the cv,?\s*",
        r"^\s*based on the document,?\s*",
        r"^\s*according to the document,?\s*",
        r"^\s*from the document,?\s*",
        r"^\s*based on the context,?\s*",
        r"^\s*according to the context,?\s*",
        r"^\s*from the context,?\s*",
        r"^\s*based on the provided context,?\s*",
        r"^\s*according to the provided context,?\s*",
    ]

    for pattern in intro_patterns:
        answer = re.sub(
            pattern,
            "",
            answer,
            flags=re.IGNORECASE
        ).strip()

    bad_phrases = [
        "provided document",
        "provided context",
        "document context",
        "database context",
    ]

    for phrase in bad_phrases:
        answer = answer.replace(phrase, "").strip()
        answer = answer.replace(phrase.capitalize(), "").strip()
        answer = answer.replace(phrase.title(), "").strip()

    answer = answer.replace("..", ".")
    answer = answer.replace(" ,", ",")
    answer = answer.replace(" .", ".")
    answer = answer.strip(" ,.-")

    return answer if answer else FALLBACK_ANSWER


def is_fallback_answer(answer: str) -> bool:
    if not answer:
        return True

    text = answer.lower().strip()

    fallback_phrases = [
        "i could not find that information",
        "could not find that information",
        "i don't know",
        "i do not know",
        "not found",
        "no information",
        "not available",
        "there is no information",
    ]

    return any(phrase in text for phrase in fallback_phrases)


def ask_llm(
    question: str,
    context: str,
    source_name: str,
    memory_context: str
) -> str:
    prompt = ChatPromptTemplate.from_template(
        """
You are Clarence AI.

Answer ONLY using the given {source_name} context.

STRICT RULES:
- Use ONLY the context below.
- Do NOT use outside knowledge.
- Do NOT guess.
- Do NOT invent information.
- Do NOT add information that is not written in the context.
- You may use the previous conversation ONLY to understand follow-up words like "he", "she", "her", "his", "that person", or "that".
- Do NOT answer from previous conversation unless the information is also found in the context.
- If the answer is not found in the context, say exactly:
I could not find that information.
- Do NOT start with "Based on the CV".
- Do NOT start with "According to the CV".
- Do NOT start with "Based on the document".
- Do NOT mention CV, document, provided context, or database context.
- Answer naturally and directly.

Previous conversation:
{memory_context}

Context:
{context}

Question:
{question}

Answer:
"""
    )

    chain = prompt | llm

    response = chain.invoke({
        "source_name": source_name,
        "memory_context": memory_context,
        "context": context,
        "question": question
    })

    return clean_answer(response)


def answer_question(
    question: str,
    document_context: str = "",
    database_context: str = "",
    source_mode: str = "auto",
    use_memory: bool = True
) -> str:
    question = question.strip()

    if not question:
        return "Please enter a question."

    document_context = document_context.strip() if document_context else ""
    database_context = database_context.strip() if database_context else ""
    source_mode = source_mode.strip().lower()

    if use_memory and is_follow_up_question(question):
        memory_context = get_memory_context()
    else:
        memory_context = "No previous conversation."

    try:
        if source_mode == "document":
            logger.info("Source mode: document")

            if not document_context:
                return FALLBACK_ANSWER

            answer = ask_llm(
                question=question,
                context=document_context,
                source_name="document",
                memory_context=memory_context
            )

            return FALLBACK_ANSWER if is_fallback_answer(answer) else answer

        if source_mode == "database":
            logger.info("Source mode: database")

            if not database_context:
                return FALLBACK_ANSWER

            answer = ask_llm(
                question=question,
                context=database_context,
                source_name="database",
                memory_context=memory_context
            )

            return FALLBACK_ANSWER if is_fallback_answer(answer) else answer

        logger.info("Source mode: auto")

        if document_context:
            logger.info("Trying document first")

            document_answer = ask_llm(
                question=question,
                context=document_context,
                source_name="document",
                memory_context=memory_context
            )

            if not is_fallback_answer(document_answer):
                logger.info("Answer found in document")
                return document_answer

            logger.info("Answer not found in document")

        if database_context:
            logger.info("Trying database second")

            database_answer = ask_llm(
                question=question,
                context=database_context,
                source_name="database",
                memory_context=memory_context
            )

            if not is_fallback_answer(database_answer):
                logger.info("Answer found in database")
                return database_answer

            logger.info("Answer not found in database")

        return FALLBACK_ANSWER

    except Exception as e:
        logger.error("Anthropic LLM error: %s", e)
        return f"Sorry, I had a problem generating the answer. Error: {str(e)}"