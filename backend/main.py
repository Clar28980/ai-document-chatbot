from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
import os
import pickle
from datetime import datetime
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOllama
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Document Chatbot API", version="2.0.0")

# Configuration from environment variables
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

# Enable CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for documents metadata
documents_store = {}
vector_db = None
current_session_id = None

class QuestionRequest(BaseModel):
    question: str

class DocumentInfo(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    chunks: int

class ChatMessage(BaseModel):
    role: str
    text: str
    timestamp: Optional[str] = None

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    global vector_db, documents_store, current_session_id
    
    # Validate file extension
    allowed_extensions = ('.pdf', '.txt')
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are allowed")
    
    # Generate unique session ID
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_session_id = session_id
    file_path = f"temp_{file.filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if file.filename.lower().endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')
        docs = loader.load()
        
        if not docs:
            raise HTTPException(status_code=400, detail="Could not extract text from document")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = text_splitter.split_documents(docs)
        
        # Store document metadata
        documents_store[session_id] = {
            "id": session_id,
            "filename": file.filename,
            "uploaded_at": datetime.now().isoformat(),
            "chunks": len(chunks)
        }
        
        # Create embeddings and vector store
        embeddings = OllamaEmbeddings(model=OLLAMA_MODEL)
        vector_db = FAISS.from_documents(chunks, embeddings)
        
        # Save vector store to disk
        vector_db_path = os.path.join(DATA_DIR, f"{session_id}_vectordb.pkl")
        with open(vector_db_path, "wb") as f:
            pickle.dump(vector_db, f)
        
        # Save documents metadata
        save_documents_metadata()
        
        return {
            "message": f"Document '{file.filename}' uploaded successfully! {len(chunks)} chunks created.",
            "document": documents_store[session_id]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# Helper functions for persistence
def save_documents_metadata():
    metadata_path = os.path.join(DATA_DIR, "documents_metadata.pkl")
    with open(metadata_path, "wb") as f:
        pickle.dump(documents_store, f)

def load_documents_metadata():
    global documents_store
    metadata_path = os.path.join(DATA_DIR, "documents_metadata.pkl")
    if os.path.exists(metadata_path):
        with open(metadata_path, "rb") as f:
            documents_store = pickle.load(f)

# Load metadata on startup
load_documents_metadata()


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all uploaded documents"""
    return list(documents_store.values())


@app.post("/documents/{doc_id}/load")
async def load_document(doc_id: str):
    """Load a previously uploaded document"""
    global vector_db, current_session_id
    
    if doc_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    vector_db_path = os.path.join(DATA_DIR, f"{doc_id}_vectordb.pkl")
    if not os.path.exists(vector_db_path):
        raise HTTPException(status_code=404, detail="Vector database not found")
    
    with open(vector_db_path, "rb") as f:
        vector_db = pickle.load(f)
    
    current_session_id = doc_id
    
    return {
        "message": f"Document '{documents_store[doc_id]['filename']}' loaded successfully",
        "document": documents_store[doc_id]
    }


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its vector database"""
    global vector_db, current_session_id
    
    if doc_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Remove vector database file
    vector_db_path = os.path.join(DATA_DIR, f"{doc_id}_vectordb.pkl")
    if os.path.exists(vector_db_path):
        os.remove(vector_db_path)
    
    # Remove from memory
    del documents_store[doc_id]
    save_documents_metadata()
    
    # Clear current vector_db if it was the deleted document
    if current_session_id == doc_id:
        vector_db = None
        current_session_id = None
    
    return {"message": "Document deleted successfully"}

@app.post("/ask")
async def ask_question(req: QuestionRequest):
    global vector_db
    if vector_db is None:
        return {"answer": "Please upload a document first using the sidebar."}
    
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        llm = ChatOllama(model=OLLAMA_MODEL)
        
        prompt = ChatPromptTemplate.from_template(
            """You are a helpful AI assistant. Answer the user's question based ONLY on the provided context from the uploaded document.
            If the answer is not in the context, say "I cannot find the answer in the uploaded document."
            
            Context:
            {context}
            
            Question: {input}
            
            Provide a clear and concise answer."""
        )
        
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = vector_db.as_retriever(search_kwargs={"k": 4})
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        response = retrieval_chain.invoke({"input": req.question})
        return {"answer": response["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    current_doc = documents_store.get(current_session_id, None)
    return {
        "status": "healthy",
        "model": OLLAMA_MODEL,
        "document_loaded": vector_db is not None,
        "current_document": current_doc,
        "total_documents": len(documents_store)
    }


@app.get("/current-document")
async def get_current_document():
    """Get currently loaded document info"""
    if current_session_id and current_session_id in documents_store:
        return documents_store[current_session_id]
    return {"message": "No document currently loaded"}