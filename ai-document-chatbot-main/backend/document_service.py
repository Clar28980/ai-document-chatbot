import os
import json
import re
from typing import List, Dict, Any
from fastapi import UploadFile

from logger_config import setup_logger

logger = setup_logger(__name__)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

CACHE_FILE = os.path.join(UPLOAD_DIR, "document_text_cache.json")

EMBEDDING_MODEL = "local-document-reader"
SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv"]

os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_json(path: str, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error("Failed to load JSON %s: %s", path, e)
        return default


def save_json(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Failed to save JSON %s: %s", path, e)


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_supported_file(filename: str) -> bool:
    filename = filename.lower()
    return any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS)


def extract_text_from_pdf_with_pypdf(file_path: str) -> str:
    if PdfReader is None:
        return ""

    try:
        reader = PdfReader(file_path)
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text() or ""

            if page_text.strip():
                text_parts.append(page_text)

        return clean_text("\n".join(text_parts))

    except Exception as e:
        logger.error("pypdf failed for %s: %s", file_path, e)
        return ""


def extract_text_from_pdf_with_pymupdf(file_path: str) -> str:
    if fitz is None:
        return ""

    try:
        pdf = fitz.open(file_path)
        text_parts = []

        for page in pdf:
            page_text = page.get_text("text") or ""

            if page_text.strip():
                text_parts.append(page_text)

        pdf.close()

        return clean_text("\n".join(text_parts))

    except Exception as e:
        logger.error("PyMuPDF failed for %s: %s", file_path, e)
        return ""


def extract_text_from_pdf(file_path: str) -> str:
    text = extract_text_from_pdf_with_pypdf(file_path)

    if text and len(text) >= 30:
        logger.info("PDF read using pypdf: %s", os.path.basename(file_path))
        return text

    text = extract_text_from_pdf_with_pymupdf(file_path)

    if text and len(text) >= 30:
        logger.info("PDF read using PyMuPDF: %s", os.path.basename(file_path))
        return text

    logger.warning("No readable PDF text found: %s", os.path.basename(file_path))
    return ""


def extract_text_from_text_file(file_path: str) -> str:
    encodings = ["utf-8", "utf-8-sig", "latin-1"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return clean_text(file.read())
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error("Failed reading text file %s: %s", file_path, e)
            return ""

    return ""


def extract_text(file_path: str) -> str:
    lower = file_path.lower()

    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_path)

    if lower.endswith(".txt") or lower.endswith(".md") or lower.endswith(".csv"):
        return extract_text_from_text_file(file_path)

    return ""


def make_chunks(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = clean_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start:start + chunk_size].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())

    stopwords = {
        "the", "and", "or", "is", "are", "was", "were",
        "to", "of", "in", "on", "for", "a", "an",
        "with", "this", "that", "it", "as", "by", "from",
        "what", "who", "how", "many", "tell", "me",
        "about", "please", "can", "you", "i", "have",
        "has", "do", "does", "your", "my", "her", "his",
        "him", "she", "he", "they", "them", "there", "their",
        "define", "meaning", "explain"
    }

    return [
        word for word in words
        if word not in stopwords and len(word) > 1
    ]


def rebuild_all_uploaded_documents_index() -> Dict[str, Any]:
    document_cache = {}

    total_files_found = 0
    successfully_read = 0
    failed_files = []

    logger.info("Rebuilding uploaded documents index")

    for filename in os.listdir(UPLOAD_DIR):
        if filename in ["document_text_cache.json", "document_keywords.json"]:
            continue

        if not is_supported_file(filename):
            continue

        total_files_found += 1
        file_path = os.path.join(UPLOAD_DIR, filename)

        try:
            text = extract_text(file_path)

            if not text or len(text.strip()) < 10:
                failed_files.append({
                    "filename": filename,
                    "reason": "No readable text found."
                })
                logger.warning("No readable text found: %s", filename)
                continue

            chunks = make_chunks(text)

            document_cache[filename] = {
                "filename": filename,
                "path": file_path,
                "text": text,
                "chunks": chunks,
                "text_characters": len(text),
                "chunk_count": len(chunks)
            }

            successfully_read += 1
            logger.info("Indexed document: %s", filename)

        except Exception as e:
            failed_files.append({
                "filename": filename,
                "reason": str(e)
            })
            logger.error("Failed indexing document %s: %s", filename, e)

    save_json(CACHE_FILE, document_cache)

    return {
        "total_files_found": total_files_found,
        "successfully_read": successfully_read,
        "failed_files": failed_files,
        "cached_files": list(document_cache.keys())
    }


async def process_uploaded_document(file: UploadFile) -> Dict[str, Any]:
    filename = file.filename

    if not filename:
        raise ValueError("No filename received.")

    safe_filename = os.path.basename(filename)

    if not is_supported_file(safe_filename):
        raise ValueError("Unsupported file type. Upload PDF, TXT, MD, or CSV only.")

    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    content = await file.read()

    if not content:
        raise ValueError("Uploaded file is empty.")

    with open(file_path, "wb") as output_file:
        output_file.write(content)

    logger.info("Uploaded document saved: %s", safe_filename)

    result = rebuild_all_uploaded_documents_index()

    return {
        "success": True,
        "filename": safe_filename,
        "message": f"{safe_filename} uploaded successfully. All uploaded documents were re-read.",
        "total_files_found": result["total_files_found"],
        "successfully_read": result["successfully_read"],
        "failed_files": result["failed_files"],
        "cached_files": result["cached_files"]
    }


def score_text(question_tokens: List[str], text: str, filename: str = "") -> int:
    text_lower = text.lower()
    filename_lower = filename.lower()

    score = 0

    for token in question_tokens:
        if token in filename_lower:
            score += 10

        if token in text_lower:
            score += 5

        exact_matches = re.findall(rf"\b{re.escape(token)}\b", text_lower)
        score += len(exact_matches) * 2

    return score


def search_uploaded_documents(question: str, top_k: int = 5) -> str:
    cache = load_json(CACHE_FILE, {})

    if not cache:
        rebuild_all_uploaded_documents_index()
        cache = load_json(CACHE_FILE, {})

    if not cache:
        logger.info("No uploaded document cache found")
        return ""

    question_tokens = tokenize(question)

    if not question_tokens:
        logger.info("No useful question tokens found")
        return ""

    results = []

    for filename, data in cache.items():
        chunks = data.get("chunks", [])

        for chunk in chunks:
            score = score_text(question_tokens, chunk, filename)

            if score > 0:
                results.append({
                    "filename": filename,
                    "score": score,
                    "chunk": chunk
                })

    results.sort(key=lambda item: item["score"], reverse=True)

    if not results:
        logger.info("No document match found for question: %s", question)
        return ""

    best_score = results[0]["score"]

    if best_score < 5:
        logger.info("Document match too weak. Score: %s", best_score)
        return ""

    logger.info(
        "Document match found: %s with score %s",
        results[0]["filename"],
        best_score
    )

    context_parts = []

    for item in results[:top_k]:
        context_parts.append(
            f"Source file: {item['filename']}\n{item['chunk']}"
        )

    return "\n\n---\n\n".join(context_parts)


def get_document_context_by_filename(filename: str, max_chars: int = 5000) -> str:
    cache = load_json(CACHE_FILE, {})

    if not cache:
        rebuild_all_uploaded_documents_index()
        cache = load_json(CACHE_FILE, {})

    data = cache.get(filename)

    if not data:
        return ""

    text = data.get("text", "")

    if not text:
        return ""

    return f"Source file: {filename}\n{text[:max_chars]}"


def get_all_uploaded_document_context(max_chars_per_file: int = 5000) -> str:
    cache = load_json(CACHE_FILE, {})

    if not cache:
        rebuild_all_uploaded_documents_index()
        cache = load_json(CACHE_FILE, {})

    if not cache:
        return ""

    parts = []

    for filename, data in cache.items():
        text = data.get("text", "")

        if text:
            parts.append(f"Source file: {filename}\n{text[:max_chars_per_file]}")

    return "\n\n---\n\n".join(parts)


def get_uploaded_files_status() -> Dict[str, Any]:
    cache = load_json(CACHE_FILE, {})

    if not cache:
        rebuild_all_uploaded_documents_index()
        cache = load_json(CACHE_FILE, {})

    files = []

    for filename, data in cache.items():
        files.append({
            "filename": filename,
            "text_characters": data.get("text_characters", 0),
            "chunk_count": data.get("chunk_count", 0)
        })

    return {
        "total_cached_files": len(files),
        "files": files
    }


def get_documents_debug() -> Dict[str, Any]:
    cache = load_json(CACHE_FILE, {})

    if not cache:
        rebuild_all_uploaded_documents_index()
        cache = load_json(CACHE_FILE, {})

    preview = {}

    for filename, data in cache.items():
        text = data.get("text", "")

        preview[filename] = {
            "text_characters": data.get("text_characters", 0),
            "chunk_count": data.get("chunk_count", 0),
            "preview": text[:1500]
        }

    return preview