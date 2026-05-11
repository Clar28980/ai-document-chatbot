from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from logger_config import setup_logger
from chatbot_service import answer_question, LLM_MODEL

from database import (
    get_ndis_services,
    get_recent_bookings,
    get_service_count,
    get_active_service_count,
    get_booking_count,
    get_booking_summary,
    build_database_context,
    answer_direct_database_question
)

from document_service import (
    process_uploaded_document,
    search_uploaded_documents,
    get_all_uploaded_document_context,
    get_uploaded_files_status,
    rebuild_all_uploaded_documents_index,
    get_documents_debug,
    EMBEDDING_MODEL
)

from memory_service import (
    save_to_memory,
    clear_memory,
    get_memory_items,
    get_memory_count,
    get_memory_context,
    is_follow_up_question
)

from precheck_service import precheck_question


logger = setup_logger(__name__)

app = FastAPI(title="Clarence AI Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_rebuild_documents():
    try:
        result = rebuild_all_uploaded_documents_index()
        logger.info("AUTO DOCUMENT REBUILD ON STARTUP")
        logger.info("Total files found: %s", result.get("total_files_found"))
        logger.info("Successfully read: %s", result.get("successfully_read"))
        logger.info("Cached files: %s", result.get("cached_files"))
        logger.info("Failed files: %s", result.get("failed_files"))

    except Exception as e:
        logger.error("AUTO DOCUMENT REBUILD FAILED: %s", e)


@app.get("/")
def home():
    return {
        "success": True,
        "message": "Clarence AI FastAPI backend is running.",
        "llm_model": LLM_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "memory_items": get_memory_count()
    }


@app.post("/clear-memory")
def clear_conversation_memory():
    clear_memory()

    return {
        "success": True,
        "message": "Conversation memory cleared."
    }


@app.get("/memory")
def view_memory():
    return {
        "success": True,
        "memory": get_memory_items()
    }


@app.get("/database-test")
def database_test():
    try:
        services = get_ndis_services()
        bookings = get_booking_summary()
        recent_bookings = get_recent_bookings()

        return {
            "success": True,
            "service_count": get_service_count(),
            "active_service_count": get_active_service_count(),
            "booking_count": get_booking_count(),
            "services": services,
            "booking_summary": bookings,
            "recent_bookings": recent_bookings
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Database error: {str(e)}"
        }


@app.get("/database/services")
def database_services():
    try:
        services = get_ndis_services(limit=100)

        return {
            "success": True,
            "count": len(services),
            "services": services
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Services database error: {str(e)}"
        }


@app.get("/database/bookings")
def database_bookings():
    try:
        summary = get_booking_summary()
        recent_bookings = get_recent_bookings(limit=100)

        return {
            "success": True,
            "count": get_booking_count(),
            "booking_summary": summary,
            "recent_bookings": recent_bookings
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Bookings database error: {str(e)}"
        }


@app.get("/database-context")
def database_context():
    try:
        return {
            "success": True,
            "context": build_database_context()
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Database context error: {str(e)}"
        }


@app.get("/documents/status")
def documents_status():
    try:
        return {
            "success": True,
            "status": get_uploaded_files_status()
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Documents status error: {str(e)}"
        }


@app.get("/documents/debug")
def documents_debug():
    try:
        return {
            "success": True,
            "files": get_documents_debug()
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Documents debug error: {str(e)}"
        }


@app.post("/documents/rebuild")
def rebuild_documents():
    try:
        result = rebuild_all_uploaded_documents_index()

        return {
            "success": True,
            "message": "All uploaded documents were re-read and re-indexed.",
            "result": result
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Documents rebuild error: {str(e)}"
        }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        result = await process_uploaded_document(file)

        return {
            "success": True,
            "message": result.get(
                "message",
                "Document uploaded successfully. All uploaded documents were re-read."
            ),
            "filename": result.get("filename"),
            "total_files_found": result.get("total_files_found"),
            "successfully_read": result.get("successfully_read"),
            "failed_files": result.get("failed_files"),
            "cached_files": result.get("cached_files")
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Upload error: {str(e)}"
        }


def ensure_documents_indexed():
    try:
        status = get_uploaded_files_status()

        if status.get("total_cached_files", 0) == 0:
            rebuild_all_uploaded_documents_index()

    except Exception:
        rebuild_all_uploaded_documents_index()


def build_search_question(clean_question: str) -> str:
    """
    If the user asks follow-up like 'what are her skills?',
    add memory context so document search knows who 'her' means.
    """
    if is_follow_up_question(clean_question):
        logger.info("Follow-up question detected. Adding memory context to document search.")
        return get_memory_context() + "\nCurrent question: " + clean_question

    return clean_question


def get_safe_document_context(search_question: str) -> str:
    """
    Try normal document search first.
    If it is weak/empty, use the full uploaded document as fallback.
    """
    document_context = search_uploaded_documents(search_question)

    if not document_context or len(document_context.strip()) < 100:
        logger.info("Using full document fallback")
        document_context = get_all_uploaded_document_context()

    return document_context


@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    question_type: str = Form("auto")
):
    try:
        clean_question = question.strip()
        clean_type = question_type.strip().lower()

        precheck = precheck_question(clean_question)

        if not precheck["allowed"]:
            return {
                "success": False,
                "answer": precheck["message"],
                "source": "precheck",
                "reason": precheck["reason"]
            }

        ensure_documents_indexed()

        search_question = build_search_question(clean_question)

        if clean_type == "document":
            document_context = get_safe_document_context(search_question)

            answer = answer_question(
                question=clean_question,
                document_context=document_context,
                database_context="",
                source_mode="document",
                use_memory=True
            )

        elif clean_type == "database":
            direct_database_answer = answer_direct_database_question(clean_question)

            if direct_database_answer:
                save_to_memory(clean_question, direct_database_answer)

                return {
                    "success": True,
                    "answer": direct_database_answer,
                    "source": "database"
                }

            database_context = build_database_context(clean_question)

            answer = answer_question(
                question=clean_question,
                document_context="",
                database_context=database_context,
                source_mode="database",
                use_memory=True
            )

        else:
            direct_database_answer = answer_direct_database_question(clean_question)

            if direct_database_answer:
                save_to_memory(clean_question, direct_database_answer)

                return {
                    "success": True,
                    "answer": direct_database_answer,
                    "source": "database"
                }

            document_context = get_safe_document_context(search_question)
            database_context = build_database_context(clean_question)

            answer = answer_question(
                question=clean_question,
                document_context=document_context,
                database_context=database_context,
                source_mode="auto",
                use_memory=True
            )

        save_to_memory(clean_question, answer)

        return {
            "success": True,
            "answer": answer,
            "source": clean_type
        }

    except Exception as e:
        logger.error("Ask error: %s", e)
        return {
            "success": False,
            "answer": f"Ask error: {str(e)}"
        }
