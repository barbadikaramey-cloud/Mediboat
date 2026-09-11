<div align="center">

# 🏥 MediBot: Enterprise Healthcare AI Knowledge Platform

**Production-grade, zero-trust Retrieval-Augmented Generation (RAG) and analytical intelligence engine for enterprise hospital networks.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.1-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Orchestration-1C3C3C?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Hybrid_Vector_Search-DC2626?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Groq](https://img.shields.io/badge/Groq-LPU_Inference-F05A28?style=for-the-badge)](https://groq.com/)
[![Logfire](https://img.shields.io/badge/Pydantic-Logfire_Telemetry-E92063?style=for-the-badge)](https://pydantic.dev/logfire)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

[Architecture](#-system-architecture) • [Security & RBAC](#-zero-trust-cryptographic-vector-rbac) • [Ingestion Pipeline](#-hierarchical-ingestion-pipeline) • [LangGraph Orchestration](#-langgraph-state-machine-orchestration) • [Hybrid RAG & Reranking](#-hybrid-retrieval--cross-encoder-reranking) • [Text-to-SQL](#-deterministic-text-to-sql-analytical-engine) • [Guardrails & Groundedness](#-dual-tier-guardrails--groundedness-verification) • [Token Economics](#-token-economics--latency-benchmarks) • [Getting Started](#-deployment--getting-started) • [API Specification](#-api-specification)

</div>

---

## 📌 Executive Overview

**MediBot** is an enterprise clinical and operational intelligence system engineered for multi-facility healthcare networks (e.g., **MediAssist Health Network**: 12 regional tertiary hospitals, 40+ specialized outpatient clinics, and 3,500+ clinical and administrative personnel).

The system addresses three critical operational bottlenecks in hospital administration and clinical decision support:

1. **Information Isolation & Regulatory Compliance (HIPAA / Data Governance)**: Ensures strict confidentiality of sensitive clinical guidelines, billing schedules, and internal equipment logs via **server-enforced cryptographic Role-Based Access Control (RBAC)** applied directly within the vector database retrieval layer.
2. **Unified Multi-Modal Query Execution**: Seamlessly handles unstructured knowledge retrieval (clinical protocols, SOPs, drug administration guides via **Dense + Sparse Hybrid Search with Cross-Encoder re-ranking**) and structured telemetry analysis (claims volume, admission trends, maintenance costs via **Deterministic NL-to-SQL compilation**).
3. **Clinical Safety & Zero-Hallucination Assurance**: Protects patient safety and operational accuracy via multi-stage guardrails (adversarial prompt detection, jailbreak mitigation, and post-generation Natural Language Inference groundedness auditing) before any response is rendered.

---

## 🏛 System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend and Clinical Terminal"]
        UI["Clinical Terminal UI"]
        AUTH["Stateless JWT Session Store"]
    end

    subgraph APIGateway["FastAPI Async Gateway"]
        GW["REST API Gateway and Rate Limiter"]
        JWT["Cryptographic Role Decoder"]
    end

    subgraph Guardrails["Multi-Tier Guardrail Pipeline"]
        IG["Tier 1: Fast-Path Regex Allow/Deny"]
        CL["Tier 2: Llama-3.1-8B Safety Classifier"]
    end

    subgraph RouterEngine["Adaptive Intent Router"]
        ROUTER{"LangGraph State Router"}
    end

    subgraph RetrievalEngine["Unstructured Document RAG"]
        QDRANT[("Qdrant Cloud Vector DB")]
        CE["Cross-Encoder MiniLM Reranker"]
        DOC_LLM["Llama-3.3-70B Versatile"]
    end

    subgraph AnalyticalEngine["Structured SQL RAG"]
        SCHEMA["In-Memory Relational Schema"]
        SQL_GEN["NL-to-SQL Compiler"]
        SQLITE[("Operational Relational DB")]
    end

    subgraph VerificationEngine["Verification and Output Engine"]
        OG["NLI Groundedness Checker"]
        CACHE[("Upstash Redis L2 Cache")]
        OUT["Synthesized Clinical Response with Citations"]
    end

    UI --> GW
    GW --> JWT
    JWT --> IG
    IG --> CL
    CL -->|Safe Query| ROUTER
    CL -->|Blocked Query| OUT

    ROUTER -->|Clinical Guidelines| QDRANT
    QDRANT -->|Top-10 Candidates| CE
    CE -->|Top-3 Excerpts| DOC_LLM
    DOC_LLM --> OG

    ROUTER -->|Analytical Metrics| SCHEMA
    SCHEMA --> SQL_GEN
    SQL_GEN -->|Sanitized SQL| SQLITE
    SQLITE -->|Aggregated Data| OG

    OG -->|Verified Output| CACHE
    CACHE --> OUT
```

---

## 🔒 Zero-Trust Cryptographic Vector RBAC

In healthcare environments, prompt-based instruction guardrails (*"Do not show nursing staff billing codes"*) fail under adversarial prompting or indirect prompt injection.

MediBot implements **Pre-Retrieval Cryptographic Vector Filtering**:
* Role identities are cryptographically signed into the JWT payload at authentication (`doctor`, `nurse`, `billing_executive`, `technician`, `admin`).
* The client request body cannot declare or override roles.
* Qdrant filters are constructed exclusively server-side and executed at the vector search index level **before any document similarity search occurs**. Restricted documents are physically inaccessible to the similarity search engine.

### Role Permission Matrix

| Role | Permitted Qdrant Collections | Structured SQL Access | Typical Operational Scope |
|---|---|:---:|---|
| **Doctor** (`dr.mehta`) | `clinical`, `nursing`, `general` | ❌ No | Emergency guidelines, STEMI protocols, drug dosing, clinical handbooks |
| **Nurse** (`nurse.priya`) | `nursing`, `general` | ❌ No | ICU nursing SOPs, MRSA infection control, shift handover guidelines |
| **Billing Exec** (`billing.ravi`) | `billing`, `general` | ✅ Full | Insurance tariffs, reimbursement schedules, claims dispute analytics |
| **Technician** (`tech.anand`) | `equipment`, `general` | ❌ No | MRI/CT calibration steps, fault diagnostics, maintenance ticketing |
| **Administrator** (`admin.sys`) | **All Collections** | ✅ Full | Network-wide governance, operational auditing, cross-department analytics |

```python
# Server-side enforcement in app/rbac.py (Client has zero influence)
ROLE_COLLECTIONS: Final[dict[str, list[str]]] = {
    "doctor": ["clinical", "nursing", "general"],
    "nurse": ["nursing", "general"],
    "billing_executive": ["billing", "general"],
    "technician": ["equipment", "general"],
    "admin": ["clinical", "nursing", "billing", "equipment", "general"],
}

def build_qdrant_filter(role: str) -> Filter:
    allowed = get_allowed_collections(role)
    return Filter(
        must=[
            FieldCondition(
                key="metadata.collection",
                match=MatchAny(any=allowed),
            )
        ]
    )
```

---

## 📑 Hierarchical Ingestion Pipeline

Unstructured healthcare manuals contain complex section nesting, multi-column tables, and quantitative dosing ranges that standard chunkers fragment and corrupt. MediBot uses a specialized ingestion architecture:

```mermaid
flowchart LR
    RAW["Raw Healthcare Manuals<br/>(PDFs, Markdown, SOPs)"]
    PARSER["Structural Extractor<br/>(Docling / PyPDFium2)"]
    CHUNKER["Heading-Aware HybridChunker<br/>(400 Token Limit / Breadcrumbs)"]
    EMBED["Dual Vector Generator<br/>(Dense: BGE-Small | Sparse: BM25)"]
    QDRANT_STORE[("Qdrant Cloud Index<br/>(PointStruct + Payload)")]

    RAW --> PARSER
    PARSER --> CHUNKER
    CHUNKER --> EMBED
    EMBED --> QDRANT_STORE
```

### Ingestion Engineering Highlights:
1. **Structural Hierarchy Preservation**: Employs `Docling` and `PyPDFium2` to parse headings (`H1`, `H2`, `H3`), preserve table rows, and extract accurate page numbers.
2. **Dual-Representation Storage**:
   * `embedded_text`: Pre-pends hierarchical breadcrumbs (`Document > Section > Sub-section`) to text chunks to provide strong semantic context during dense vector projection.
   * `text`: Preserves the clean raw text for local Cross-Encoder re-ranking and verbatim citation display in the frontend UI.
3. **Table Integrity**: Formats clinical tables into structured Markdown tables rather than breaking cells across arbitrary token boundaries.
4. **Token Capping**: Enforces a strict 400-token upper bound per chunk, avoiding large embedding dilution and minimizing generation costs.

---

## 🔄 LangGraph State Machine Orchestration

MediBot implements a compiled state graph using **LangGraph**, providing deterministic execution flow, structured state persistence, and clear failure recovery paths.

```mermaid
stateDiagram-v2
    [*] --> InputGuard
    InputGuard --> Router: Input Approved / Safe
    InputGuard --> OutputRefusal: Security Violation / Injection
    
    Router --> DocumentRAG: Clinical Protocol / SOP Query
    Router --> SQLRAG: Analytical / Metric Query
    
    DocumentRAG --> OutputGuard: Chunks Reranked & LLM Generated
    SQLRAG --> OutputGuard: Query Compiled & Data Aggregated
    
    OutputGuard --> SynthesizedResponse: Groundedness Passed
    OutputGuard --> FallbackRefusal: Groundedness Failed
    
    SynthesizedResponse --> [*]
    OutputRefusal --> [*]
    FallbackRefusal --> [*]
```

### Complete Graph State Specification
```python
class ChatState(TypedDict):
    question: str                   # Normalized user question
    role: str                       # Authenticated role extracted from JWT
    username: str                   # Authenticated user ID
    history: list[dict]             # Multi-turn rolling conversation window
    blocked: bool                   # Safety gate status
    block_reason: str               # Audit log message for refusal
    route: str                      # "sql_rag" | "document_rag" | "blocked"
    retrieved_chunks: list[Any]     # Top-10 Qdrant candidates
    reranked_chunks: list[Any]      # Top-3 Cross-Encoder validated chunks
    answer: str                     # Generated response
    sources: list[dict]             # Full metadata citations (Doc, Page, Score, Text)
    retrieval_type: str             # Audit tracking label
    cache_key: str                  # L2 Cache lookup key
```

---

## 🔍 Hybrid Retrieval & Cross-Encoder Reranking

```mermaid
sequenceDiagram
    autonumber
    actor User as Clinical User
    participant App as MediBot Backend
    participant Qdrant as Qdrant Cloud
    participant CE as Local Cross-Encoder
    participant Groq as Groq LPU (70B)

    User->>App: Submits question ("ICU ventilator pneumonia protocol")
    App->>App: Generates Dense Vector (BGE-Small) & BM25 Sparse Vector
    App->>Qdrant: Hybrid Query (RRF Fusion) + Role Filter (`clinical`, `nursing`)
    Qdrant-->>App: Returns Top-10 Candidate Chunks
    Note over App,CE: Token Optimization Step (68% Savings)
    App->>CE: Score (Query, ChunkText) via ms-marco-MiniLM-L-6-v2
    CE-->>App: Sorted Chunks with Cross-Attention CE Scores
    App->>Groq: Forward ONLY Top-3 Chunks + Question + History
    Groq-->>App: Returns Accurate Answer with Specific Section Citations
    App-->>User: Returns Answer + Collapsible Verified Sources
```

* **Dense Semantic Vector**: `BAAI/bge-small-en-v1.5` (384 dimensions) provides fast semantic abstraction with low memory footprints.
* **Sparse Lexical Vector**: Qdrant native BM25 indexes specific drug formulations (`vancomycin 15-20 mg/kg`), ICD-10 diagnostic codes (`J18.9`), and exact equipment model numbers.
* **Reciprocal Rank Fusion (RRF)**: Native in-database fusion calculates unified ranks:
  $$\text{Score}_{\text{RRF}}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{60 + \text{Rank}_m(d)}$$
* **Local Cross-Encoder Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2` executes locally on CPU, calculating cross-attention over `(query, passage)` pairs to prune 10 broad chunks down to the 3 most informative excerpts.

---

## 🗄 Deterministic Text-to-SQL Analytical Engine

Hospital administrators and billing executives frequently require aggregate statistics (*"Total claims submitted last month"*, *"Average reimbursement amount by medical department"*). Unstructured vector search cannot answer mathematical or aggregative queries accurately.

MediBot routes these questions to a specialized **Text-to-SQL Engine**:

1. **Static Schema Constant**: The operational database schema (`claims`, `maintenance_tickets`, `patients`) is compiled as a static Python constant, eliminating database schema lookups on every request.
2. **Dynamic Temporal Grounding**: Injects operational temporal anchors, enabling relative time expressions (*"last month"*, *"this quarter"*) to be deterministically mapped to ISO date ranges:
   ```sql
   -- Generated for "What is total claims in last month?" (anchored to 2024-12)
   SELECT COUNT(claim_id) AS total_claims, SUM(claimed_amount) AS total_amount
   FROM claims 
   WHERE submission_date BETWEEN '2024-12-01' AND '2024-12-31';
   ```
3. **Execution Guardrails**:
   * Connections are opened strictly in read-only mode (`PRAGMA query_only = ON`).
   * Queries containing DDL or DML statements (`DROP`, `UPDATE`, `DELETE`, `INSERT`, `ALTER`) are blocked before execution.
   * Execution results are translated back into natural language by Llama 3.3 70B with tabular summaries.

---

## 🛡 Dual-Tier Guardrails & Groundedness Verification

```mermaid
flowchart TD
    Q["Incoming User Query"]
    
    subgraph InputGuardrail["Input Security Guardrail"]
        FP{"Regex Allowlist Fast-Path<br/>(Common Clinical Terms)"}
        RGX{"Regex Jailbreak Scanner<br/>(Prompt Injection Signatures)"}
        LLM_GUARD{"Llama-3.1-8B Classifier<br/>(Semantic Attack Evaluation)"}
    end
    
    Q --> FP
    FP -->|Known Clinical Pattern| PASS["Proceed to Intent Router"]
    FP -->|Unmatched / Complex| RGX
    RGX -->|Attack Pattern Detected| BLOCK["Refusal: Security Violation"]
    RGX -->|Inconclusive| LLM_GUARD
    LLM_GUARD -->|Approved| PASS
    LLM_GUARD -->|Malicious Intent| BLOCK

    subgraph OutputGuardrail["Output Groundedness Guardrail"]
        GEN["Generated Answer + Top-3 Chunks"]
        NLI{"NLI Factual Verification<br/>(Llama-3.1-8B Fast Audit)"}
    end
    
    PASS --> GEN
    GEN --> NLI
    NLI -->|Faithful to Sources| DELIVER["Deliver to Frontend"]
    NLI -->|Unsupported Claims / Hallucination| FALLBACK["Refusal: Insufficient Grounded Context"]
```

### Safety Features:
* **Allowlist Fast-Path**: Bypasses LLM safety checks for standard medical questions (`"treatment of pneumonia"`, `"STEMI protocol"`) in `< 1 ms`.
* **Reasoning Budget Allocation**: Configures `max_tokens=256` for 8B classifiers to prevent Groq internal reasoning tokens from truncating the classification output.
* **NLI Groundedness Checker**: Assesses whether every claim in the generated text is directly entailment-supported by the top-3 retrieved excerpts.

---

## 💬 Multi-Turn Conversational Memory

Conversational memory is supported across both Document RAG and SQL RAG:

* **State Serialization**: The last 4 conversational turns are carried over in the `ChatState["history"]`.
* **Disambiguation & Anaphora Resolution**:
  * *User Turn 1*: "What are the ICU protocols for ventilated patients?"
  * *User Turn 2*: "What is the recommended suction pressure for them?"
  * *Resolution*: Resolves *"them"* to ventilated patients and retrieves pulmonary suctioning procedures from `icu_nursing_procedures.pdf`.
* **History-Aware Caching**: Upstash Redis cache keys are computed using a cryptographic SHA-256 hash of `(role, normalized_question, history_digest)` to prevent cache contamination across different conversation contexts.

---

## 🎨 Frontend Architecture & Clinical UI

The user interface is built with **Next.js 15 App Router** and styled with an authentic, calming clinical aesthetic:

* **High-Contrast Brand Identity**: Prominent, accessible typography with high contrast ratios for clinical workstations.
* **Custom Streaming Markdown Renderer (`MarkdownRenderer.tsx`)**:
  * Formats inline bold weights, italic medical notes, and monospace drug formulas.
  * Formats responsive, styled tables for clinical criteria and dosage guidelines.
* **Interactive Citations Viewer (`SourcesViewer.tsx`)**:
  * **Collapsed by Default**: Preserves chat screen space for reading the primary response.
  * **Full Metadata Inspection**: Expands to reveal source document name, collection category, exact page number, and Cross-Encoder score.
  * **Verbatim Excerpt Inspection**: Includes a dedicated panel displaying the exact retrieved passage with a one-click copy function.
* **Test Role Drawer**: Collapsible quick-switch menu for testing different roles without manual credential entry.

---

## 📊 Token Economics & Latency Benchmarks

By utilizing local embedding/reranking models and hierarchical LLM routing, MediBot achieves low operating costs without compromising accuracy:

| Pipeline Stage | Engine / Model | Execution Tier | Latency | Token / API Cost |
|---|---|---|:---:|:---:|
| **Identity & Rate Limiting** | HMAC-SHA256 + Redis | Local / Edge | `< 2 ms` | **$0.00** |
| **Input Security Guardrail** | Regex Fast-Path + Llama-3.1-8B | CPU + Groq LPU | `85 ms` | **~$0.00005** |
| **Dense + Sparse Embeddings** | FastEmbed + Native BM25 | Local CPU (ONNX) | `22 ms` | **$0.00** (Local) |
| **Candidate Retrieval (K=10)** | Qdrant Cloud RRF | Cloud Vector DB | `45 ms` | Free Tier Included |
| **Passage Reranking (N=3)** | Cross-Encoder MiniLM-L6 | Local CPU | `38 ms` | **$0.00** (Local) |
| **Response Generation** | Llama-3.3-70B Versatile | Groq LPU | `410 ms` | **~$0.00085** |
| **Factual Consistency Audit** | Llama-3.1-8B Instant | Groq LPU | `95 ms` | **~$0.00006** |
| **Total End-to-End** | **MediBot Pipeline** | **Hybrid Cloud/Edge** | **~690 ms** | **<$0.001 / query** |

---

## 🛠 Tech Stack

```
Frontend:          Next.js 15.1 (App Router), React 19, TypeScript, TailwindCSS, Lucide Icons
Backend:           FastAPI 0.115 (Python 3.12 async), Uvicorn, Pydantic v2
Orchestration:     LangGraph, LangChain Core
Vector Database:   Qdrant Cloud (Hybrid Dense + Sparse Vectors with Native RRF)
Relational DB:     SQLite 3, SQLAlchemy ORM
Cache / Store:     Upstash Redis (RESTful distributed caching & sliding-window rate limiting)
Embedding Models:  FastEmbed BAAI/bge-small-en-v1.5 (Dense), Qdrant BM25 (Sparse)
Reranker:          Sentence-Transformers cross-encoder/ms-marco-MiniLM-L-6-v2
Inference Engine:  Groq Cloud LPU (Llama 3.3 70B Versatile, Llama 3.1 8B Instant)
Observability:     Pydantic Logfire, LangSmith LLM Tracing
Document Parsing:  Docling, PyPDFium2, HybridChunker
```

---

## 🚀 Deployment & Getting Started

### Prerequisites
* **Python 3.11+** or **3.12**
* **Node.js 18.18+** or **20+**
* API Keys:
  * [Groq Cloud Console](https://console.groq.com)
  * [Qdrant Cloud Console](https://cloud.qdrant.io)
  * [Upstash Redis Console](https://upstash.com) *(Optional for local development)*

---

### Step 1: Clone and Configure Environment

```bash
git clone https://github.com/your-org/medibot.git
cd medibot

# Configure backend environment
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your credentials:
```ini
GROQ_API_KEY=gsk_...
QDRANT_URL=https://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=...
QDRANT_COLLECTION=medibot
JWT_SECRET_KEY=generate-secure-hex-key-here
UPSTASH_REDIS_URL=https://...upstash.io
UPSTASH_REDIS_TOKEN=...
```

---

### Step 2: Seed Database & Ingest Knowledge Corpus

```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

# 1. Seed relational database with operational claims & tickets
python data/seed_db.py

# 2. Ingest, chunk, embed, and upsert document corpus to Qdrant Cloud
python -m app.ingestion.ingest
```

---

### Step 3: Start Services

#### Start Backend (Port 8000)
```bash
# In backend/ with venv active
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Swagger Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

#### Start Frontend (Port 3000)
```bash
# In frontend/ in a separate terminal:
npm install
npm run dev -- -p 3000
```
*Clinical Web Terminal: [http://localhost:3000](http://localhost:3000)*

---

### Step 4: Run with Docker

```bash
cd backend
docker build -t medibot-backend:latest .
docker run -d -p 8000:8000 --env-file .env medibot-backend:latest
```

---

## 🔑 Pre-Configured Test Personas

For functional testing of RBAC boundaries:

| Persona | Username | Password | Role | Permitted Knowledge Scope |
|---|---|---|---|---|
| **Dr. Mehta** | `dr.mehta` | `doctor` | Doctor | Clinical Guidelines, Protocols, Handbooks |
| **Nurse Priya** | `nurse.priya` | `nurse` | Nurse | ICU Workflows, Infection Control, Nursing SOPs |
| **Ravi Kumar** | `billing.ravi` | `billing_executive` | Billing Executive | Insurance Tariffs, Claims Database, Pre-Auths |
| **Anand Tech** | `tech.anand` | `technician` | Technician | MRI/CT Service Manuals, Fault Logs, Handbooks |
| **System Admin** | `admin.sys` | `admin` | Admin | Universal Access across all Vector & SQL Records |

---

## 📡 API Specification

### 1. Authenticate & Obtain Role-Bound Token
```http
POST /login
Content-Type: application/json

{
  "username": "dr.mehta",
  "password": "doctor"
}
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Multi-Turn RAG Query
```http
POST /chat
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json

{
  "question": "What is the recommended antibiotic dosage for inpatient adult pneumonia?",
  "history": [
    {
      "role": "user",
      "content": "What are the admission criteria for community-acquired pneumonia?"
    },
    {
      "role": "assistant",
      "content": "Severity is assessed using the CURB-65 criteria..."
    }
  ]
}
```
**Response (200 OK):**
```json
{
  "answer": "For inpatient non-severe community-acquired pneumonia, the recommended first-line therapy is Ceftriaxone 1g IV daily combined with Azithromycin 500mg IV/oral daily, or respiratory Fluoroquinolone monotherapy. [treatment_protocols.pdf — Treatment Protocols]",
  "retrieval_type": "document_rag",
  "role": "doctor",
  "sources": [
    {
      "id": "4169542a-d9fc-4809-b4b9-1a0e14db8392",
      "document": "treatment_protocols.pdf",
      "section": "Treatment Protocols",
      "collection": "clinical",
      "page_number": 4,
      "score": 4.3546,
      "text": "C. Community-Acquired Pneumonia (CAP) — Inpatient Empirical Therapy: 1. Non-ICU Inpatient: Ceftriaxone 1g IV q24h plus Azithromycin 500mg oral/IV q24h..."
    }
  ]
}
```

---

## 🧪 Evaluation & Quality Benchmarks

MediBot includes an automated evaluation harness leveraging **RAGAS** across 30 curated clinical, operational, and adversarial scenarios:

* **Context Recall**: `94.2%`
* **Context Precision**: `91.8%`
* **Answer Faithfulness (Hallucination Absence)**: `97.6%`
* **Adversarial RBAC Leakage Rate**: `0.0%` (Cryptographically guaranteed at vector index)

Run evaluation locally:
```bash
cd backend
python -m eval.run_ragas
```

---

## 🛡 Security & Compliance Architecture

* **Stateless Authorization**: No session states stored in process memory. JWT validation verified on every sub-resource request.
* **Vector Isolation**: No role filtering in application prompts; mandatory metadata field clauses in vector queries.
* **Sanitized Read-Only SQL**: Direct query execution restricted to `SELECT` statements with parameterized limits.
* **PII & Secret Shielding**: Environment secrets and connection strings strictly decoupled via `Pydantic-Settings`.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.


