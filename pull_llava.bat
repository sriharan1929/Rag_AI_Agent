@echo off
title Ollama LLaVA Downloader
echo ============================================
echo   Downloading LLaVA Vision Model (4GB)
echo ============================================
echo This will take a few minutes depending on your internet speed.
echo.
ollama pull llava
echo.
echo ============================================
echo   Download Complete! 
echo   You can now analyze images in ZIP-RAG.
echo ============================================
pause
