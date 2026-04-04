# 📁 ZIP-RAG v2.0: Production-Grade Offline RAG System

A sophisticated **Retrieval-Augmented Generation (RAG)** application for seamless, **100% offline** document analysis. Upload diverse formats—ZIP, PDF, Word, Excel, and even code—and interact via natural language. Powered by local **Ollama AI** with advanced retrieval capabilities.

---

## 🔍 Project Overview

| Layer           | Technology                                                                 |
| --------------- | -------------------------------------------------------------------------- |
| **Frontend**    | React 19, Axios, SSE Streaming, React-Markdown                             |
| **Backend**     | FastAPI (Python 3.10+), Pydantic v2                                        |
| **RAG Engine**  | LangChain, Hybrid Search (BM25 + FAISS), RRF Fusion                        |
| **Advanced**    | Multi-Query Expansion, Contextual Compression, RapidOCR                    |
| **LLM / Vision**| Ollama (`llama3`, `llama3.2-vision`, `mistral`)                            |

ZIP-RAG v2.0 goes beyond simple document search. It uses **Hybrid Retrieval** to combine keyword and semantic matching, **Multi-Query expansion** to broaden search intent, and **Contextual Compression** to deliver only the most relevant snippets to the LLM, ensuring high accuracy and faster responses.

---

## ✨ Features

- **🖼️ Native Vision Support**: Upload images or PDFs with scans. Use `llama3.2-vision` or `moondream` to "see" and analyze visual data.
- **🌐 Web Search Mode**: Toggle "Web Search" to augment your documents with real-time data from DuckDuckGo.
- **🧠 Advanced RAG Pipeline**:
  - **Multi-Query Expansion**: Generates 4+ variations of your question for better retrieval.
  - **Contextual Compression**: Scans retrieved chunks to strip irrelevant noise, saving LLM tokens.
  - **Hybrid Search**: Combines BM25 (keyword) and FAISS (semantic) with Reciprocal Rank Fusion (RRF).
- **📄 Enhanced OCR**: Integrated **RapidOCR** for high-accuracy text extraction from scanned PDFs.
- **⚡ SSE Streaming**: Optimized token-by-token streaming UI for real-time AI responses.
- **📊 Comparative Mode**: Send queries to multiple models simultaneously and compare results side-by-side.
- **💾 Session Management**: Persistent conversation history—save, load, and manage your chat sessions locally.
- **📂 Multi-format / ZIP Extraction**: Automatic recursive extraction of ZIP files with full directory tree visualization.

---

## 🗂️ Project Structure

```text
zip-rag-project/
├── backend/
│   ├── main.py            # FastAPI Entry (v2.0 Logic)
│   ├── multi_query_retriever.py # Intent-aware query expansion
│   ├── contextual_compression.py # Sentence-level compression
│   ├── web_search.py       # DuckDuckGo integration
│   ├── prompts.py          # Persona-tuned instruction router
│   ├── uploads/            # Document storage
│   └── vectorstore/        # Persistent FAISS index
├── frontend/
│   ├── src/
│   │   ├── components/     # UI Components (Chat, Tree, Vision)
│   │   └── App.js          # Main React Application
│   └── package.json
├── docs/
│   ├── PLANNING.md         # Sprint & Development roadmap
│   └── TODO.md             # Completed & Pending tasks
├── setup.bat               # 🛠️ One-click Dependency Installer
├── start_app.bat           # 🚀 Complete App Launcher (Backend + Frontend + Ollama)
└── pull_llava.bat          # 📥 Vision Model Downloader
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** & **Node.js 18+**
- **Ollama**: Download from [ollama.com](https://ollama.com)
- **Models**:
  ```bash
  ollama pull llama3
  ollama pull llama3.2-vision  # Required for Image Analysis
  ```

### 2. Automatic Setup (Windows)
Double-click `setup.bat`. This will:
1. Install Node.js dependencies for the frontend.
2. Create a Python virtual environment and install all backend requirements.

### 3. Launch App
Double-click `start_app.bat`.
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000 (Opens automatically)

---

## 🛠️ Manual Installation

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

---

## 🖥️ API Reference v2.0

| Method | Endpoint             | Description                                          |
| ------ | -------------------- | ---------------------------------------------------- |
| `GET`  | `/`                  | Health check & Ollama detection status               |
| `POST` | `/upload/`           | Multi-file/ZIP upload; returns tree + NDJSON logs    |
| `POST` | `/ask_stream/`       | **Streaming SSE**: Multi-query RAG with token output |
| `GET`  | `/list_files/`       | Retrieve current document structure and summaries     |
| `POST` | `/history/save/`     | Save chat session to local JSON                      |
| `GET`  | `/history/list/`     | List all saved session metadata                      |
| `DELETE`| `/delete/?path=...` | Remove file/folder and auto-rebuild index            |

---

## 🔧 Configuration

| Variable     | Default                   | Purpose                                     |
| ------------ | ------------------------- | ------------------------------------------- |
| `OLLAMA_URL` | `http://127.0.0.1:11434`  | Connection to local Ollama instance        |
| `UPLOAD_DIR` | `uploads/`                | Where raw files are stored                 |
| `VECTOR_DB`  | `vectorstore/`            | FAISS index location                       |
| `MODE`       | `advanced` / `basic`      | Toggle for Multi-query & Compression paths |

---

## 🐛 Troubleshooting

- **No Vision Output**: Ensure you have pulled `llama3.2-vision` or `llava`. Run `pull_llava.bat` to automate this.
- **Slow Indexing**: Large PDF collections or high OCR volumes require substantial CPU/GPU. Ensure `huggingface-hub` is accessible for the initial model download (~90MB).
- **Backend Errors**: Check `requirements.txt` is fully installed. Some OCR components require Visual C++ Redistributable on Windows.

---

## 📄 License
MIT — Open Source. Built for speed, privacy, and precision.