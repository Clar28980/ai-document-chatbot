from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from chatbot_service import answer_question, LLM_MODEL

from database import (
    get_ndis_services,
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
    find_matching_document_by_keywords,
    EMBEDDING_MODEL
)

from memory_service import (
    save_to_memory,
    clear_memory,
    get_memory_items,
    get_memory_count
)


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

        print("======================================")
        print("AUTO DOCUMENT REBUILD ON STARTUP")
        print("Total files found:", result.get("total_files_found"))
        print("Successfully read:", result.get("successfully_read"))
        print("Cached files:", result.get("cached_files"))
        print("Failed files:", result.get("failed_files"))
        print("======================================")

    except Exception as e:
        print("AUTO DOCUMENT REBUILD FAILED:", str(e))


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

        return {
            "success": True,
            "services": services,
            "booking_summary": bookings
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Database error: {str(e)}"
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


def is_database_question(question: str) -> bool:
    q = question.lower()

    database_words = [
        "database",
        "user",
        "users",
        "service",
        "services",
        "category",
        "categories",
        "booking",
        "bookings",
        "support worker",
        "support workers",
        "worker",
        "workers"
    ]

    return any(word in q for word in database_words)


@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    question_type: str = Form("auto")
):
    try:
        clean_question = question.strip()
        clean_type = question_type.strip().lower()

        if not clean_question:
            return {
                "success": False,
                "answer": "Please enter a question."
            }

        ensure_documents_indexed()

        # 1. Database questions should use database only.
        if clean_type == "database" or is_database_question(clean_question):
            direct_database_answer = answer_direct_database_question(clean_question)

            if direct_database_answer:
                save_to_memory(clean_question, direct_database_answer)

                return {
                    "success": True,
                    "answer": direct_database_answer
                }

            database_context = build_database_context()

            answer = answer_question(
                question=clean_question,
                document_context="",
                database_context=database_context,
                source_mode="database",
                use_memory=False
            )

            save_to_memory(clean_question, answer)

            return {
                "success": True,
                "answer": answer
            }

        # 2. Uploaded document questions use document_keywords.json.
        matched_document = find_matching_document_by_keywords(clean_question)

        if clean_type == "document" or matched_document:
            document_context = search_uploaded_documents(clean_question)

            if not document_context:
                document_context = get_all_uploaded_document_context()

            answer = answer_question(
                question=clean_question,
                document_context=document_context,
                database_context="",
                source_mode="document",
                use_memory=False
            )

            save_to_memory(clean_question, answer)

            return {
                "success": True,
                "answer": answer
            }

        # 3. Default: use database context only.
        database_context = build_database_context()

        answer = answer_question(
            question=clean_question,
            document_context="",
            database_context=database_context,
            source_mode="database",
            use_memory=False
        )

        save_to_memory(clean_question, answer)

        return {
            "success": True,
            "answer": answer
        }

    except Exception as e:
        return {
            "success": False,
            "answer": f"Ask error: {str(e)}"
        }