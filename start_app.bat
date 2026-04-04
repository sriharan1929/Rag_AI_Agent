@echo off
title ZIP-RAG Launcher
echo ============================================
echo  ZIP-RAG Project with Ollama AI (Free)
echo ============================================
echo.

cd /d "%~dp0"

if not exist "backend\venv" (
    echo [ERROR] Backend not setup. Please run 'setup.bat' first.
    pause
    exit /b
)

if not exist "frontend\node_modules" (
    echo [ERROR] Frontend not setup. Please run 'setup.bat' first.
    pause
    exit /b
)

echo [1/3] Starting Ollama AI server...
start "Ollama" cmd /c "ollama serve"
timeout /t 5 /nobreak >nul

echo [2/3] Starting Backend on http://localhost:8000 ...
start "ZIP-RAG Backend" "%~dp0start_backend.bat"
timeout /t 5 /nobreak >nul

echo [3/3] Starting Frontend on http://localhost:3000 ...
start "ZIP-RAG Frontend" "%~dp0start_frontend.bat"

echo.
echo Done! Browser will open at http://localhost:3000
pause
