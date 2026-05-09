from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from memory_service import get_memory_context, is_follow_up_question


LLM_MODEL = "llama3.2:1b"
FALLBACK_ANSWER = "I could not find that information."

llm = OllamaLLM(
    model=LLM_MODEL,
    temperature=0.0,
    num_predict=350
)


def clean_answer(answer: str) -> str:
    if not answer:
        return FALLBACK_ANSWER

    answer = answer.strip()

    prefixes = ["Answer:", "Final answer:", "Clarence AI:", "AI:", "Bot:"]
    for prefix in prefixes:
        if answer.startswith(prefix):
            answer = answer.replace(prefix, "", 1).strip()

    bad_phrases = [
        "in the provided document",
        "based on the provided document",
        "according to the provided document",
        "in the provided context",
        "based on the provided context",
        "according to the provided context",
        "from the provided context",
        "in the document context",
        "based on the document context",
        "according to the document context",
        "I could not find that information in the uploaded document or database.",
        "I could not find that information in the uploaded document or database",
    ]

    for phrase in bad_phrases:
        answer = answer.replace(phrase, "").strip()
        answer = answer.replace(phrase.capitalize(), "").strip()

    answer = answer.replace("..", ".").replace(" ,", ",").replace(" .", ".")
    answer = answer.strip(" ,.-")

    return answer if answer else FALLBACK_ANSWER


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

    if source_mode == "document":
        database_context = ""
        use_memory = False

    if source_mode == "database":
        document_context = ""
        use_memory = False

    if not document_context and not database_context:
        return FALLBACK_ANSWER

    if use_memory and is_follow_up_question(question):
        memory_context = get_memory_context()
    else:
        memory_context = "No previous conversation."

    prompt = ChatPromptTemplate.from_template(
        """
You are Clarence AI.

Answer ONLY using the given context.

Rules:
- Do not use outside knowledge.
- Do not invent information.
- Do not invent jobs, titles, skills, education, or experience.
- If source mode is document, use only Document Context.
- If source mode is database, use only Database Context.
- Never say "provided document", "provided context", or "document context".
- Answer naturally.
- If the answer is not found, say exactly: I could not find that information.

Source mode:
{source_mode}

Previous conversation:
{memory_context}

Document Context:
{document_context}

Database Context:
{database_context}

Question:
{question}

Answer:
"""
    )

    chain = prompt | llm

    try:
        answer = chain.invoke({
            "source_mode": source_mode,
            "memory_context": memory_context,
            "document_context": document_context if document_context else "No document context.",
            "database_context": database_context if database_context else "No database context.",
            "question": question
        })

        return clean_answer(answer)

    except Exception as e:
        print(f"LLM error: {e}")
        return "Sorry, I had a problem generating the answer."