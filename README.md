# AI Document Chatbot

An AI-powered chatbot that answers questions about your PDF and TXT documents using LLaMA 3 via Ollama (completely local - no API keys needed!).

## Features

- **Multi-Document Support** - Upload and manage multiple documents
- **Persistent Storage** - Documents are saved to disk and persist between restarts
- **Document Management** - Switch between documents, delete old ones
- **Chat Export** - Export your chat history to a text file
- **Real-time Chat** - Modern chat interface with avatars and timestamps
- **File Type Validation** - Supports PDF and TXT files only
- **Local AI** - Uses LLaMA 3 locally via Ollama (no API costs!)
- **Vector Database** - FAISS for fast semantic search
- **Modern UI** - Angular 18 + Tailwind CSS

## Architecture

```
┌─────────────┐      HTTP       ┌─────────────┐
│   Angular   │ ◄──────────────► │   FastAPI   │
│   Frontend  │   (CORS)        │   Backend   │
│  (Port 4200)│                 │  (Port 8000) │
└─────────────┘                 └──────┬──────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
              ┌──────────┐      ┌──────────┐      ┌──────────┐
              │ LangChain│      │  FAISS   │      │  Ollama  │
              │ Pipeline │      │  Vector  │      │ LLaMA 3  │
              │          │      │  Store   │      │ (Local)  │
              └──────────┘      └──────────┘      └──────────┘
                                       │
                                       ▼
                              ┌──────────────┐
                              │  Persistent  │
                              │    Storage   │
                              │  (Pickle)    │
                              └──────────────┘
```

## Prerequisites

1. **Python 3.8+**
2. **Node.js 18+**
3. **Ollama** - Download from https://ollama.com

## Quick Start

### Step 1: Install Ollama and Pull LLaMA 3

```bash
# Install Ollama from https://ollama.com
# Then pull the LLaMA 3 model:
ollama pull llama3
```

### Step 2: Setup and Start

**Using PowerShell Script (Windows):**
```powershell
.\start.ps1 -Help    # View options
.\start.ps1          # Start both backend and frontend
```

**Manual Start:**

Terminal 1 - Backend:
```bash
cd backend
venv\Scripts\activate  # Windows
# OR: source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm install
ng serve
```

### Step 3: Open in Browser

Navigate to: http://localhost:4200

## Usage Guide

### Uploading Documents

1. Click "Choose File" in the sidebar
2. Select a PDF or TXT file
3. Click "Upload & Process"
4. Wait for processing to complete

### Managing Documents

- **Switch Documents**: Click on any document in the sidebar list
- **Delete Document**: Hover over a document and click the trash icon
- **View Active Document**: Current document is shown with a blue indicator

### Chat Features

- **Ask Questions**: Type in the chat box and press Enter or click send
- **Clear Chat**: Click the trash icon in the chat header
- **Export Chat**: Click the download icon to save chat history as a text file
- **Timestamps**: Hover over messages to see timestamps

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload PDF/TXT file |
| `/ask` | POST | Ask a question |
| `/documents` | GET | List all documents |
| `/documents/{id}/load` | POST | Switch to a document |
| `/documents/{id}` | DELETE | Delete a document |
| `/current-document` | GET | Get active document |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger API docs |

## Configuration

Create a `.env` file in the `backend/` directory:

```env
# Ollama Model
OLLAMA_MODEL=llama3

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:4200

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Data Storage
DATA_DIR=./data
```

## Project Structure

```
ai-document-chatbot/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   ├── .gitignore          # Git ignore rules
│   └── data/               # Persistent storage (auto-created)
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── app.component.ts    # Main component
│   │   │   ├── app.component.html  # Chat UI
│   │   │   └── app.component.spec.ts
│   │   └── environments/
│   │       ├── environment.ts      # Dev config
│   │       └── environment.prod.ts # Prod config
│   ├── package.json
│   └── tailwind.config.js
├── start.ps1                # PowerShell startup script
├── SETUP.md                 # Detailed setup guide
└── README.md                # This file
```

## Technologies Used

**Backend:**
- FastAPI - Modern Python web framework
- LangChain - LLM orchestration framework
- FAISS - Vector similarity search
- Ollama - Local LLM runner (LLaMA 3)
- Pydantic - Data validation

**Frontend:**
- Angular 18 - Modern web framework
- Tailwind CSS - Utility-first CSS
- RxJS - Reactive programming
- HttpClient - HTTP requests

## Features in Detail

### Multi-Document Support
- Upload multiple documents
- Each document gets its own vector database
- Switch between documents without re-uploading
- Persistent storage across server restarts

### Chat Management
- Clear chat history anytime
- Export chats to text files
- Timestamps on all messages
- Visual distinction between user and AI messages

### Error Handling
- File type validation (PDF, TXT only)
- Backend connection error messages
- Graceful degradation when Ollama is unavailable
- Detailed error messages in UI

## Troubleshooting

**"Ollama not found"**
- Install Ollama from https://ollama.com
- Ensure it's in your system PATH
- Run `ollama pull llama3`

**"Cannot connect to backend"**
- Ensure backend is running on port 8000
- Check Windows Firewall settings
- Verify `FRONTEND_URL` in `.env` matches your frontend URL

**"Error processing document"**
- Ensure file is not corrupted
- Check file size (large files may take longer)
- Verify PDF is text-based (not scanned images)

**Frontend build errors**
```bash
cd frontend
npm ci  # Clean install dependencies
ng serve --force  # Force rebuild
```

## License

MIT License - Feel free to use for your projects!

---

## For Assignment Submission

This project fulfills all assignment requirements:
- ✅ Loads content from PDF/TXT files
- ✅ Embeds and stores in local vector database (FAISS)
- ✅ Uses LangChain for pipeline orchestration
- ✅ Uses LLaMA 3 locally via Ollama (free, no API key)
- ✅ Angular frontend for UI
- ✅ Answers user questions about uploaded documents
- ✅ **Bonus**: Multi-document support, persistent storage, chat export
