# ZIP-RAG v2.0 Diagrams

This document visualizes the system architecture, component structures, and flows of the ZIP-RAG offline application.

## 1. System Architecture Diagram
A high-level view showing the relationships between the frontend user interface, the FastAPI backend services, local data storage, and external systems (like local LLMs and Web Search).

```mermaid
graph TD
    User([User]) -->|Web Browser| Frontend[React 19 Frontend]
    Frontend -->|HTTP / SSE| Backend[FastAPI Backend]
    
    subgraph Storage Layer
        VectorDB[(FAISS Vector DB)]
        DocStore[(Local File System)]
    end
    
    subgraph Internal Services
        OCR(RapidOCR Engine)
        RAG(RAG Pipeline Engine)
    end
    
    subgraph External Interfaces
        Ollama((Ollama Local LLM))
        WebSearch(DuckDuckGo Search)
    end
    
    Backend <-->|Retrieve/Store Vectors| VectorDB
    Backend <-->|Upload/Read Files| DocStore
    Backend <-->|Image Parsing| OCR
    Backend <-->|RAG Query Logic| RAG
    RAG <-->|Prompts/Responses| Ollama
    RAG <-->|Fetch Live Data| WebSearch
```

## 2. Class Diagram
Illustrates the main internal entities in the backend Python application and how they depend on each other.

```mermaid
classDiagram
    class FastAPIApp {
        +router
        +startup_event()
    }
    class DocumentManager {
        +upload_files(files)
        +extract_zip(zip_path)
        +parse_documents()
    }
    class VectorStoreService {
        +add_documents(docs)
        +similarity_search(query)
        +hybrid_search(query)
    }
    class RAGPipeline {
        +execute_query(query, model)
        -multi_query_expansion(query)
        -contextual_compression(docs)
    }
    class LLMService {
        +generate_response(prompt)
        +stream_response(prompt)
    }
    class WebSearchTool {
        +search(query)
    }
    
    FastAPIApp --> DocumentManager : Uses
    FastAPIApp --> RAGPipeline : Initiates
    RAGPipeline --> VectorStoreService : Retrieves Context
    RAGPipeline --> LLMService : Sends Prompts
    RAGPipeline --> WebSearchTool : Augments
    DocumentManager --> VectorStoreService : Populates
```

## 3. Use Case Diagram
Maps out the typical interactions of a User within the ZIP-RAG application.

```mermaid
flowchart LR
    User([User])
    Admin([System Admin])
    
    User --> UC1(Upload Documents / ZIP)
    User --> UC2(Ask Question via Chat)
    User --> UC3(Toggle Web Search Mode)
    User --> UC4(Compare Model Outputs)
    
    Admin --> UC5(Manage Vector DB / Clear Index)
    Admin --> UC6(Download Local Models)
    
    %% Optional styling
    style User fill:#f9f,stroke:#333,stroke-width:2px
    style Admin fill:#bbf,stroke:#333,stroke-width:2px
```

## 4. Sequence Diagram
Demonstrates the chronological sequence of events when a User submits a question using the RAG capability.

```mermaid
sequenceDiagram
    actor User
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant RAG as RAG Pipeline
    participant DB as FAISS Vector DB
    participant LLM as Ollama AI
    
    User->>UI: Submits Query "Explain feature X"
    UI->>API: POST /ask_stream/ {query}
    API->>RAG: process_query(query)
    
    rect rgb(230, 240, 255)
        Note right of RAG: Optional: Intent Expansion
        RAG->>RAG: Multi-Query Expansion
    end
    
    RAG->>DB: Search for context (BM25 + FAISS)
    DB-->>RAG: Return relevant chunks
    
    rect rgb(230, 240, 255)
        Note right of RAG: Optional: Strip noise
        RAG->>RAG: Contextual Compression
    end
    
    RAG->>LLM: Stream completion (Prompt + Context)
    LLM-->>RAG: Stream Tokens
    RAG-->>API: Yield Tokens
    API-->>UI: SSE Data Stream
    UI-->>User: Display Typing Effect
```

## 5. Activity Diagram
Shows the flow of steps during a document upload and ingestion process.

```mermaid
flowchart TD
    Start([Start Upload]) --> CheckType{File Type?}
    
    CheckType -->|ZIP| Extract[Extract Archive]
    CheckType -->|PDF / Image| OCRCheck{Scanned or Image?}
    CheckType -->|Text / Word| TextParse[Parse Text]
    
    Extract --> IterateFiles[Process Each Extracted File]
    IterateFiles --> CheckType
    
    OCRCheck -->|Yes| RunOCR[Run RapidOCR]
    OCRCheck -->|No| TextParse
    
    RunOCR --> TextParse
    
    TextParse --> Chunk[Chunk Text]
    Chunk --> Embed[Generate Embeddings]
    Embed --> Store[(Save to FAISS & Document Store)]
    Store --> Finish([Document Ingested Successfully])
```
