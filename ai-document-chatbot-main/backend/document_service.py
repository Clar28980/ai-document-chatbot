import os
import json
import re
from typing import List, Dict, Any, Optional
from fastapi import UploadFile

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
KEYWORDS_FILE = os.path.join(UPLOAD_DIR, "document_keywords.json")

EMBEDDING_MODEL = "local-keyword-reader"
SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv"]

os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_json(path: str, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


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
        print(f"pypdf failed: {e}")
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
        print(f"PyMuPDF failed: {e}")
        return ""


def extract_text_from_pdf(file_path: str) -> str:
    text = extract_text_from_pdf_with_pypdf(file_path)

    if text and len(text) >= 30:
        print(f"PDF read using pypdf: {os.path.basename(file_path)}")
        return text

    text = extract_text_from_pdf_with_pymupdf(file_path)

    if text and len(text) >= 30:
        print(f"PDF read using PyMuPDF: {os.path.basename(file_path)}")
        return text

    return ""


def extract_text_from_text_file(file_path: str) -> str:
    encodings = ["utf-8", "utf-8-sig", "latin-1"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return clean_text(file.read())
        except UnicodeDecodeError:
            continue

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
        "him", "she", "he", "they", "them"
    }

    return [
        word for word in words
        if word not in stopwords and len(word) > 1
    ]


def extract_keywords(text: str, max_keywords: int = 120) -> List[str]:
    words = tokenize(text)
    frequency = {}

    for word in words:
        frequency[word] = frequency.get(word, 0) + 1

    sorted_words = sorted(
        frequency.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [word for word, count in sorted_words[:max_keywords]]


def rebuild_all_uploaded_documents_index() -> Dict[str, Any]:
    document_cache = {}
    keyword_cache = {}

    total_files_found = 0
    successfully_read = 0
    failed_files = []

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

            keyword_cache[filename] = extract_keywords(text)
            successfully_read += 1

        except Exception as e:
            failed_files.append({
                "filename": filename,
                "reason": str(e)
            })

    save_json(CACHE_FILE, document_cache)
    save_json(KEYWORDS_FILE, keyword_cache)

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


def find_matching_document_by_keywords(question: str) -> Optional[Dict[str, Any]]:
    keyword_cache = load_json(KEYWORDS_FILE, {})

    if not keyword_cache:
        rebuild_all_uploaded_documents_index()
        keyword_cache = load_json(KEYWORDS_FILE, {})

    if not keyword_cache:
        return None

    question_words = set(tokenize(question))
    matches = []

    for filename, keywords in keyword_cache.items():
        keyword_set = set(str(keyword).lower() for keyword in keywords)
        matched_words = question_words.intersection(keyword_set)

        if matched_words:
            matches.append({
                "filename": filename,
                "score": len(matched_words),
                "matched_words": list(matched_words)
            })

    if not matches:
        return None

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[0]


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


def search_uploaded_documents(question: str, top_k: int = 5) -> str:
    cache = load_json(CACHE_FILE, {})

    if not cache:
        rebuild_all_uploaded_documents_index()
        cache = load_json(CACHE_FILE, {})

    if not cache:
        return ""

    matched_document = find_matching_document_by_keywords(question)

    if matched_document:
        return get_document_context_by_filename(matched_document["filename"])

    question_tokens = tokenize(question)

    if not question_tokens:
        return ""

    results = []

    for filename, data in cache.items():
        for chunk in data.get("chunks", []):
            chunk_lower = chunk.lower()
            filename_lower = filename.lower()

            score = 0

            for token in question_tokens:
                if token in chunk_lower:
                    score += 5

                if token in filename_lower:
                    score += 8

            if score > 0:
                results.append({
                    "filename": filename,
                    "score": score,
                    "chunk": chunk
                })

    results.sort(key=lambda item: item["score"], reverse=True)

    if not results:
        return ""

    context_parts = []

    for item in results[:top_k]:
        context_parts.append(
            f"Source file: {item['filename']}\n{item['chunk']}"
        )

    return "\n\n---\n\n".join(context_parts)


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