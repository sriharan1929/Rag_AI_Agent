@echo off
title ZIP-RAG Setup
echo ============================================
echo  ZIP-RAG Project Setup
echo ============================================

echo [1/2] Installing Frontend dependencies...
cd frontend
call npm install
cd ..

echo [2/2] Setting up Backend environment...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing Python requirements...
pip install -r requirements.txt
cd ..

echo.
echo ============================================
echo  Setup Complete! 
echo  Use start_app.bat to launch the project.
echo ============================================
pause
