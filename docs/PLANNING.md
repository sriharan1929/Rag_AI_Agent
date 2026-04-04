# Multi-Format Data Retrieval & RAG System

## Team Organization and Development Plan

This document outlines the detailed team structure, roles, responsibilities, and sprint plan to develop the offline Retrieval-Augmented Generation (RAG) system in a 1-month timeframe with a 4-person team.

---


## 👥 Core Roles and Responsibilities

### 1. Frontend Developer (UI/UX & Client Logic)

**Focus**: User Interface, User Experience, Client-side logic, and API integration.
**Key Responsibilities**:

- **Project Structure**: Set up the React 19 application, configure CSS/Tailwind (if used), and establish the component hierarchy.
- **Upload Interface**: Develop a robust drag-and-drop file upload zone that handles single files and ZIP archives. Implement progress indicators and error states.
- **File System Visualization**: Build a recursive "File Tree" component that visually represents the extracted contents of uploaded ZIP files or directories.
- **Chat Interface**: Create a fluid chat UI with message bubbles (User vs AI), typing indicators, and auto-scroll functionality.
- **Markdown Rendering**: Integrate and style a markdown parser (e.g., `react-markdown`) to properly render the AI's responses, including headers, lists, code blocks with syntax highlighting, and tables.
- **API Integration**: Utilize Axios or Fetch to connect the frontend to the FastAPI `/upload` and `/ask` endpoints. Manage state (e.g., loading, error, success states) effectively.
- **Responsive Design**: Ensure the application is visually appealing and functional on both desktop and mobile devices.

### 2. Backend API Engineer (FastAPI & Server Logic)

**Focus**: Server architecture, API endpoints, file management, and system orchestration.
**Key Responsibilities**:

- **FastAPI Setup**: Initialize the FastAPI application, configure CORS middleware to allow frontend requests, and set up basic health check endpoints.
- **File Upload Management**: Implement the `/upload` endpoint. Handle multi-part form data, save files securely to a temporary `uploads/` directory, and avoid filename collisions.
- **ZIP Extraction Engine**: Write robust Python scripts to handle ZIP file extraction. It must recursively traverse directories, ignore temporary/hidden files (like `.DS_Store`), and maintain the folder structure for the frontend to visualize.
- **Query Routing**: Build the `/ask` endpoint logic. Determine if a query is file-specific (e.g., "Summarize report.pdf") or a general semantic search request, and route it to the appropriate LangChain chain.
- **System Maintenance**: Create cron-like tasks or background processes to clean up the `uploads/` directory periodically so the server's disk space does not fill up.

### 3. AI & RAG Data Engineer (Pipeline & LLM Integration)

**Focus**: Data ingestion, text splitting, embeddings, vector storage, and Ollama integration.
**Key Responsibilities**:

- **Document Ingestion Layer**: Utilize LangChain and specific loaders (`PyPDFLoader`, `Docx2txtLoader`, `UnstructuredExcelLoader`, `TextLoader`, etc.) to reliably extract plain text from all supported file formats.
- **Text Splitting Strategy**: Implement a `RecursiveCharacterTextSplitter`. Fine-tune the `chunk_size` (e.g., 500-1000) and `chunk_overlap` (e.g., 50-100) specifically optimized for the chosen LLM's context window.
- **Embedding Generation**: Integrate HuggingFace's `all-MiniLM-L6-v2` local embedding model. Ensure it runs efficiently on the CPU/GPU locally without requiring an internet connection.
- **Vector Database**: Set up FAISS to store and retrieve document embeddings. Implement save/load functionality so the index persists between server restarts.
- **LLM Orchestration**: Connect LangChain to the local Ollama instance (running `llama3` or `mistral`). Craft the system prompts to ensure the AI responds accurately, refuses off-topic prompts reasonably, and formats answers well in Markdown.

### 4. Integration Lead / QA / DevOps

**Focus**: System integration, orchestration scripts, quality assurance, and project management.
**Key Responsibilities**:

- **Orchestration Tooling**: Write and maintain the `.bat` (Windows) and `.sh` (Mac/Linux) scripts (`start_app.bat`, `start_frontend.bat`, `start_backend.bat`). These scripts should seamlessly launch Ollama, FastAPI, and React in a single click.
- **System Integration**: Act as the bridge between the Frontend and Backend engineers. Define the exact JSON structures for API requests and responses (e.g., standardizing error message formats).
- **Quality Assurance (QA)**: Write unit tests and end-to-end (E2E) tests. Manually try to break the system (uploading malformed files, uploading massive ZIP files, turning off Wi-Fi mid-query).
- **Environment Management**: Create and maintain the `requirements.txt` (Python) and `package.json` (Node), ensuring all library versions are strictly pinned to prevent "it works on my machine" issues.
- **Documentation**: Keep the `README.md` completely up to date with installation instructions, API documentation, and architecture diagrams.

---

## 📅 1-Month Detailed Development Sprint Plan

### **Week 1: Core Scaffolding & Prototyping**

_(Goal: Independent systems are running, communicating, and basic text can be processed)_

- **Frontend**: Initialize React. Create static, unlinked mockups of the File Upload and Chat screens.
- **Backend**: Initialize FastAPI. Create dummy `/upload` (returns success JSON) and `/ask` (returns a hardcoded "Hello" string) endpoints. Confirm frontend can hit these endpoints without CORS errors.
- **AI Engineer**: Install Ollama locally. Write a standalone Python script that can read a single `.txt` file, embed it, and have Llama 3 answer a question about it.
- **Integration/QA**: Write the initial `start_app.bat` script. Set up GitHub/GitLab repository with branch protection rules.

### **Week 2: Ingestion & Storage Implementation**

_(Goal: Users can upload files, and the system can read and store them in the vector database)_

- **Frontend**: Link the Upload component to the Backend. Add loading bars. Implement the "File Tree" visual component to display successfully uploaded files.
- **Backend**: Implement the real `upload/` logic to save files locally. Write the ZIP extraction tool.
- **AI Engineer**: Implement all specific document loaders (PDF, Word, Excel, CSV, Python, JS). Connect the backend's saved files to the FAISS index creation logic.
- **Integration/QA**: Test uploading a complex ZIP file (containing PDFs, subfolders, and code). Verify that FAISS is successfully saving the embeddings.

### **Week 3: Retrieval, LLM Integration & UI Linking**

_(Goal: Full loop completion. Ask a question, get an AI answer based on uploaded files)_

- **Frontend**: Build out the Chat UI fully. Link it to the `/ask` endpoint. Implement `react-markdown` to render the incoming AI responses beautifully.
- **Backend**: Finalize the `/ask` endpoint routing. Catch errors (like "LLM Timeout" or "Ollama not running") and send clean HTTP status codes to the frontend.
- **AI Engineer**: Refine the retrieval logic (e.g., retrieving the top 'k' most relevant chunks). Craft the strict systemic prompt for Ollama ("You are a helpful assistant. Use _only_ the provided context to answer…").
- **Integration/QA**: Pair with frontend/backend to ensure the loading states (which can take 10-30 seconds for local LLMs) are handled gracefully on the UI without timing out.

### **Week 4: Polish, Edge Cases, and Deployment Prep**

_(Goal: A production-ready, beautiful, robust local application)_

- **Frontend**: Polish CSS. Ensure mobile responsiveness. Add features like "Clear Chat" or "Restart Session" buttons.
- **Backend**: Add background tasks to delete temporary uploaded files after the FAISS index is built. Fine-tune API response times.
- **AI Engineer**: Test edge cases: What if the user asks a question not in the document? What if the document is pure numbers? Tweak text chunk sizes based on real-world testing.
- **Integration/QA**: Conduct a fully offline demo (turn off internet, click `start_app.bat`, upload files, ask questions). Finalize all README/Documentation.

---

## 🚀 Definition of Done (DoD) for the Project

To consider this project successfully completed within the month, the following criteria must be met:

1. **100% Offline Capability**: The system must run flawlessly without any internet connection (after initial setup and model pulling).
2. **Multi-Format Support**: System must accurately read ZIP, PDF, Word, Excel, CSV, and Code files.
3. **One-Click Start**: A user should be able to double-click `start_app.bat` and have the entire system (Frontend, Backend, LLM) launch and open in the browser.
4. **Resiliency**: The application does not crash if a user uploads an unsupported file or if the Ollama server is temporarily busy.
