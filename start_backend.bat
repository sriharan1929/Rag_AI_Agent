@echo off
title ZIP-RAG Backend
echo Starting ZIP-RAG Backend...
cd /d "%~dp0backend"
call venv\Scripts\activate
echo Loading ML models (this may take 30-60 seconds)...
uvicorn main:app --reload --port 8000
pause
