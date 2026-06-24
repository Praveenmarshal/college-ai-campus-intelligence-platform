# System Diagrams

All diagrams are in [Mermaid](https://mermaid.js.org/) syntax — render natively on
GitHub, or paste into [mermaid.live](https://mermaid.live).

---

## 1. Architecture Diagram

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        UI[React SPA<br/>Vite + Tailwind]
    end

    subgraph API["API Layer — Flask"]
        AUTH[Auth Routes]
        DOC[Document Routes]
        CHAT[Chat Routes]
        ANALYTICS[Analytics Routes]
        ROUTER[Smart Router Routes]
        ML[ML Routes]
        OCR[OCR Routes]
    end

    subgraph Services["Service Layer"]
        RAG[RAG Pipeline]
        AGENTS[9 Specialised Agents]
        QR[Query Router]
        NLQ[NL→Pandas Engine]
        NLM[NL→Mongo Engine]
        PRED[ML Predictor]
        OCRSVC[OCR Processor]
    end

    subgraph Data["Data Layer"]
        MONGO[(MongoDB Atlas)]
        CHROMA[(ChromaDB)]
        FILES[(Local File Storage)]
        MODELS[(Trained ML Models)]
    end

    subgraph AI["AI Layer"]
        OLLAMA[Ollama Runtime]
        QWEN[Qwen 3 8B/14B]
        MINILM[all-MiniLM-L6-v2]
    end

    UI -->|JWT REST| AUTH
    UI --> DOC
    UI --> CHAT
    UI --> ANALYTICS
    UI --> ROUTER
    UI --> ML
    UI --> OCR

    CHAT --> RAG
    ROUTER --> QR --> AGENTS
    DOC --> RAG
    ANALYTICS --> NLQ
    ANALYTICS --> NLM
    ML --> PRED
    OCR --> OCRSVC

    RAG --> CHROMA
    RAG --> MINILM
    RAG --> QWEN
    AGENTS --> MONGO
    AGENTS --> QWEN
    NLQ --> QWEN
    NLM --> QWEN
    NLM --> MONGO
    PRED --> MONGO
    PRED --> MODELS
    OCRSVC --> FILES

    QWEN --- OLLAMA
    MINILM -.embeds.-> CHROMA

    AUTH --> MONGO
    DOC --> MONGO
    DOC --> FILES
```

---

## 2. Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o| STUDENTS : "has profile"
    USERS ||--o| FACULTY : "has profile"
    USERS ||--o{ CHATS : creates
    USERS ||--o{ DOCUMENTS : uploads
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ AUDIT_LOGS : generates

    STUDENTS ||--o{ ATTENDANCE : "has records"
    STUDENTS ||--o| PLACEMENTS : "may have"
    STUDENTS ||--o{ FEES : owes
    STUDENTS ||--o| HOSTEL : "may reside"
    STUDENTS ||--o{ EVENTS : registers

    FACULTY ||--o{ ATTENDANCE : records
    FACULTY }o--o{ EVENTS : organises

    USERS {
        ObjectId _id PK
        string name
        string email UK
        string password_hash
        string role
        bool is_active
        datetime created_at
    }
    STUDENTS {
        ObjectId _id PK
        string student_id UK
        ObjectId user_id FK
        string department
        int batch_year
        float cgpa
    }
    FACULTY {
        ObjectId _id PK
        string faculty_id UK
        ObjectId user_id FK
        string department
        string designation
    }
    ATTENDANCE {
        ObjectId _id PK
        string student_id FK
        string course_id
        datetime date
        string status
    }
    PLACEMENTS {
        ObjectId _id PK
        string student_id FK
        string company_name
        float package_lpa
        string status
    }
    DOCUMENTS {
        ObjectId _id PK
        string filename
        string file_type
        ObjectId uploaded_by FK
        bool is_processed
        int chunk_count
    }
    CHATS {
        ObjectId _id PK
        string session_id UK
        ObjectId user_id FK
        array messages
    }
```

---

## 3. Use Case Diagram

```mermaid
flowchart LR
    Student((Student))
    Faculty((Faculty))
    Admin((Admin))

    subgraph System["AI Campus Intelligence Platform"]
        UC1[Ask AI Assistant]
        UC2[View My Attendance/CGPA]
        UC3[Analyze Resume]
        UC4[View Placements]
        UC5[Search Library]
        UC6[View Class Analytics]
        UC7[Flag At-Risk Students]
        UC8[Upload Documents]
        UC9[Manage Users]
        UC10[View Audit Logs]
        UC11[Train ML Models]
        UC12[Send Notifications]
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5

    Faculty --> UC1
    Faculty --> UC6
    Faculty --> UC7

    Admin --> UC1
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
```

---

## 4. Class Diagram — Agent System (Phase 8)

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +str name
        +str description
        +handle(query, context) dict
        #_response(answer, sources, data) dict
        #_error_response(message) dict
    }

    class DocumentAgent {
        +RAGPipeline pipeline
        +handle(query, context) dict
    }
    class AnalyticsAgent {
        +_guess_collection(query) str
        +handle(query, context) dict
    }
    class PlacementAgent {
        +handle(query, context) dict
    }
    class AcademicAgent {
        +handle(query, context) dict
    }
    class PredictionAgent {
        +handle(query, context) dict
    }
    class LibraryAgent {
        +handle(query, context) dict
    }
    class HostelAgent {
        +handle(query, context) dict
    }
    class EventAgent {
        +handle(query, context) dict
    }
    class ResumeAgent {
        +handle(query, context) dict
    }

    class AgentOrchestrator {
        -dict _agents
        -dict _AGENT_CLASSES
        +get_agent(name) BaseAgent
        +dispatch(name, query, context) dict
        +list_agents() list
    }

    class QueryRouter {
        +classify_keyword(query) tuple
        +classify_llm(query) str
        +classify(query) dict
        +route(query, context) dict
        +route_hybrid(query, context) dict
    }

    BaseAgent <|-- DocumentAgent
    BaseAgent <|-- AnalyticsAgent
    BaseAgent <|-- PlacementAgent
    BaseAgent <|-- AcademicAgent
    BaseAgent <|-- PredictionAgent
    BaseAgent <|-- LibraryAgent
    BaseAgent <|-- HostelAgent
    BaseAgent <|-- EventAgent
    BaseAgent <|-- ResumeAgent

    AgentOrchestrator o-- BaseAgent : manages
    QueryRouter --> AgentOrchestrator : dispatches via
```

---

## 5. Sequence Diagram — RAG Chat Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as Flask /api/chat
    participant Router as QueryRouter
    participant Agent as DocumentAgent
    participant Vec as ChromaDB
    participant LLM as Ollama/Qwen3

    User->>UI: Types question
    UI->>API: POST /api/chat/message {message, session_id}
    API->>API: Persist user message
    API->>Router: route(query)
    Router->>Router: classify_keyword(query)
    alt confidence high
        Router->>Agent: dispatch
    else confidence low
        Router->>LLM: classify intent (LLM fallback)
        LLM-->>Router: agent_name
        Router->>Agent: dispatch
    end
    Agent->>Agent: embed_text(query)
    Agent->>Vec: query(embedding, top_k=5)
    Vec-->>Agent: top-k chunks + scores
    Agent->>LLM: chat(context + query, system_prompt)
    LLM-->>Agent: generated answer
    Agent-->>API: {answer, sources, agent}
    API->>API: Persist assistant message
    API-->>UI: {response, sources, session_id}
    UI-->>User: Renders answer + source chips
```

---

## 6. Sequence Diagram — Document Upload & Indexing

```mermaid
sequenceDiagram
    actor Admin
    participant UI as React UI
    participant API as /api/documents/upload/pdf
    participant Proc as PDFProcessor
    participant Embed as Embedder (MiniLM)
    participant Vec as ChromaDB
    participant DB as MongoDB

    Admin->>UI: Selects PDF, clicks Upload
    UI->>API: multipart/form-data POST
    API->>API: validate_upload() (size, extension)
    API->>DB: DocumentModel.create() [is_processed=false]
    API->>Proc: extract_text() → clean_text() → chunk_text()
    Proc-->>API: list[chunk]
    API->>Embed: embed_chunks(chunks)
    Embed-->>API: ids, embeddings, metadatas
    API->>Vec: add_chunks()
    API->>DB: mark_processed(chunk_count, page_count)
    API-->>UI: 201 {document, chunks_created}
    UI-->>Admin: Success — "Ask questions about this document"
```
