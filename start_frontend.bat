@echo off
title ZIP-RAG Frontend
echo Starting ZIP-RAG Frontend...
cd /d "%~dp0frontend"
set HOST=0.0.0.0
npm start
pause
