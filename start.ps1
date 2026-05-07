# AI Document Chatbot Startup Script (PowerShell)
# This script starts both backend and frontend

param(
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\start.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipBackend   Skip starting the backend server"
    Write-Host "  -SkipFrontend  Skip starting the frontend server"
    Write-Host "  -Help          Show this help message"
    Write-Host ""
    Write-Host "Prerequisites:"
    Write-Host "  1. Ollama must be installed and running: https://ollama.com"
    Write-Host "  2. Run: ollama pull llama3"
    Write-Host "  3. Python virtual environment should be created"
    Write-Host "  4. Node.js dependencies should be installed"
    exit 0
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Document Chatbot Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command($Command) {
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-Command "ollama")) {
    Write-Host "WARNING: Ollama not found. Please install from https://ollama.com" -ForegroundColor Red
} else {
    $ollamaCheck = ollama list 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Ollama is not running. Start it with: ollama serve" -ForegroundColor Red
    } else {
        Write-Host "Ollama is running" -ForegroundColor Green
    }
}

# Start Backend
if (-not $SkipBackend) {
    Write-Host ""
    Write-Host "Starting Backend Server..." -ForegroundColor Green
    Write-Host "----------------------------------------" -ForegroundColor Green
    
    $backendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD\backend
        if (Test-Path ".\venv\Scripts\activate") {
            .\venv\Scripts\activate
        }
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
    }
    
    Write-Host "Backend starting at http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
}

# Start Frontend
if (-not $SkipFrontend) {
    Write-Host ""
    Write-Host "Starting Frontend Server..." -ForegroundColor Green
    Write-Host "----------------------------------------" -ForegroundColor Green
    
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD\frontend
        ng serve
    }
    
    Write-Host "Frontend starting at http://localhost:4200" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services are starting up!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Keep the script running
while ($true) {
    Start-Sleep -Seconds 1
    
    if (-not $SkipBackend -and $backendJob.State -eq "Failed") {
        Receive-Job $backendJob
        Write-Host "Backend job failed!" -ForegroundColor Red
    }
    
    if (-not $SkipFrontend -and $frontendJob.State -eq "Failed") {
        Receive-Job $frontendJob
        Write-Host "Frontend job failed!" -ForegroundColor Red
    }
}
