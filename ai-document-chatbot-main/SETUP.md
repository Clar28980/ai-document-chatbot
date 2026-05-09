# Setup Guide

## First-Time Setup

### 1. Install Prerequisites

1. **Python 3.8+** - Download from https://python.org
2. **Node.js 18+** - Download from https://nodejs.org
3. **Ollama** - Download from https://ollama.com

### 2. Setup Ollama

Open a terminal and run:
```bash
ollama pull llama3
```

Keep Ollama running in the background.

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Setup Frontend

```bash
cd frontend

# Install Node.js dependencies
npm install
```

### 5. (Optional) Configure Environment

Copy the example environment file and customize if needed:
```bash
cd backend
copy .env.example .env
```

Default configuration works without changes.

---

## Running the Application

### Option 1: Use the Startup Script (Recommended)

```powershell
.\start.ps1
```

Or with options:
```powershell
.\start.ps1 -SkipFrontend    # Start only backend
.\start.ps1 -SkipBackend     # Start only frontend
.\start.ps1 -Help            # Show help
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
ng serve
```

---

## Verification

After starting, verify everything is working:

1. **Backend Health Check**: http://localhost:8000/health
2. **API Documentation**: http://localhost:8000/docs
3. **Frontend App**: http://localhost:4200

---

## Common Issues

### "ollama not found"
- Make sure Ollama is installed and in your PATH
- Restart your terminal after installation

### "Cannot connect to backend"
- Ensure backend is running on port 8000
- Check Windows Firewall is not blocking the connection

### "Module not found" errors
- Reinstall dependencies: `pip install -r requirements.txt` (backend) or `npm install` (frontend)

### Port already in use
- Change ports in environment configuration
