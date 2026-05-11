# AI Document Chatbot

An AI-powered document chatbot for PDF and TXT files. The backend uses FastAPI, LangChain, local document embeddings, and Claude through the Anthropic API.

## Features

- Upload PDF and TXT documents
- Ask questions about uploaded document content
- Conversation memory for follow-up questions
- Optional database context support
- Persistent document text cache
- Angular frontend with chat history
- Claude API integration through `ANTHROPIC_API_KEY`

## Architecture

```text
Angular frontend (4200)
        |
        v
FastAPI backend (8000)
        |
        +-- Document processing and search
        +-- Conversation memory
        +-- LangChain prompt pipeline
        +-- Claude via Anthropic API
```

## Prerequisites

1. Python 3.8+
2. Node.js 18+
3. Anthropic API key

No local LLM runner is required.

## Backend Configuration

Create `backend/.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:4200

CHUNK_SIZE=1000
CHUNK_OVERLAP=200
DATA_DIR=./data
```

`ANTHROPIC_MODEL` is optional. If omitted, the backend defaults to `claude-haiku-4-5-20251001`.

## Quick Start

Install backend dependencies:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Install frontend dependencies:

```powershell
cd frontend
npm install
```

Start both services:

```powershell
.\start.ps1
```

Manual start:

```powershell
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
cd frontend
ng serve
```

Open the app at `http://localhost:4200`.

## Verification

```powershell
python backend\test_setup.py
```

You can also check:

- Backend health/docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:4200`

## API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/upload` | POST | Upload PDF/TXT file |
| `/ask` | POST | Ask a question |
| `/documents/status` | GET | View uploaded document status |
| `/documents/debug` | GET | Debug document index/cache |
| `/memory` | GET | View conversation memory |
| `/clear-memory` | POST | Clear conversation memory |
| `/database-test` | GET | Test database connectivity |
| `/database-context` | GET | View database context |
| `/docs` | GET | Swagger API docs |

## Troubleshooting

**Anthropic API key missing**

- Add `ANTHROPIC_API_KEY` to `backend/.env`
- Restart the backend after changing `.env`

**Claude request fails**

- Confirm your API key is valid
- Confirm your account has access to the configured model
- Try `ANTHROPIC_MODEL=claude-haiku-4-5-20251001`

**Cannot connect to backend**

- Ensure FastAPI is running on port `8000`
- Confirm the frontend is using `http://127.0.0.1:8000` or `http://localhost:8000`
- Check Windows Firewall if needed

**Frontend build errors**

```powershell
cd frontend
npm install
npm run build
```

## Technologies

Backend:

- FastAPI
- LangChain
- langchain-anthropic
- PyMuPDF / pypdf
- sentence-transformers
- pyodbc

Frontend:

- Angular
- TypeScript
- CSS

## License

MIT
