# Setup Guide

## First-Time Setup

### 1. Install Prerequisites

1. Python 3.8+
2. Node.js 18+
3. Anthropic API key

A local LLM runner is not required.

### 2. Configure Claude API Access

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

Keep your real API key private. Do not commit it.

### 3. Setup Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Setup Frontend

```powershell
cd frontend
npm install
```

## Running the Application

### Option 1: Startup Script

```powershell
.\start.ps1
```

Options:

```powershell
.\start.ps1 -SkipFrontend
.\start.ps1 -SkipBackend
.\start.ps1 -Help
```

### Option 2: Manual Start

Backend:

```powershell
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
ng serve
```

## Verification

Run:

```powershell
python backend\test_setup.py
```

Then open:

- Backend docs: `http://localhost:8000/docs`
- Frontend app: `http://localhost:4200`

## Common Issues

### Anthropic API key missing

- Add `ANTHROPIC_API_KEY` to `backend/.env`
- Restart the backend

### Claude model access error

- Confirm your Anthropic account has access to the configured model
- Use `ANTHROPIC_MODEL=claude-haiku-4-5-20251001`

### Cannot connect to backend

- Ensure backend is running on port `8000`
- Check Windows Firewall if needed

### Module not found errors

- Backend: `cd backend && pip install -r requirements.txt`
- Frontend: `cd frontend && npm install`

### Port already in use

- Stop the process using the port, or change the port in your environment configuration
