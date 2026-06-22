# MindBridge — Mental Health Support Chatbot

A production-quality mental wellbeing support chatbot with a FastAPI backend (Gemini API, RAG, guardrails) and a React + Vite frontend.

> **Important**: This is a wellbeing support tool, not a substitute for professional mental health care. In an emergency, contact local emergency services or the helplines listed below.

---

## Architecture

```
User message
    |
    v
React Frontend (Vite)
    |  POST /api/chat { message, session_id }
    v
FastAPI Backend
    |
    v
+-- GUARDRAILS (pre-LLM) --------------------------+
|  1. Crisis Detector (deterministic, keyword-based)|
|     -> Hardcoded helpline response, skips LLM     |
|  2. Topic Classifier (keyword + Gemini fallback)  |
|     -> Polite redirect for off-topic messages      |
+---------------------------------------------------+
    |  (on-topic, non-crisis)
    v
RAG Retrieval (ChromaDB + Gemini embeddings)
    |  top-k vetted wellbeing content chunks
    v
Gemini API call (system prompt + context + history)
    |
    v
Output Moderation (strip diagnosis/medication language)
    |
    v
Response -> Frontend -> Chat UI
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11+ |
| LLM | Google Gemini API (`gemini-2.5-flash`) |
| Embeddings | Gemini `text-embedding-004` |
| Vector Store | ChromaDB (local, file-based) |
| Frontend | React + Vite |
| Styling | Plain CSS with CSS custom properties |
| Sessions | In-memory (keyed by `session_id`) |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

The RAG index is built automatically on first startup from the knowledge base files in `backend/app/rag/knowledge_base/`.

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server (proxies /api to backend on :8000)
npm run dev
```

The app will be available at `http://localhost:5173`.

### Environment Variables

#### Backend (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Chat model |
| `EMBEDDING_MODEL` | No | `text-embedding-004` | Embedding model |
| `CHROMA_PERSIST_DIR` | No | `./chroma_data` | ChromaDB storage path |
| `LOG_LEVEL` | No | `info` | Logging level |

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

Tests cover:
- **Crisis detector**: Positive cases (suicide/self-harm language) and negative cases (figurative expressions, general stress)
- **Topic classifier**: In-scope, off-topic, and ambiguous message classification
- **Chat flow**: End-to-end pipeline with mocked Gemini calls

---

## Guardrails

### Crisis Detector
- Deterministic regex/keyword matching against a curated pattern file (`app/guardrails/crisis_patterns.json`)
- Bypasses the LLM entirely — returns hardcoded helpline response
- Works even if the Gemini API is down
- Privacy-conscious logging: timestamps and session IDs only, no raw message content

### Topic Classifier
- Two-stage: fast keyword check, then Gemini fallback for ambiguous cases
- Permissive with borderline cases (work stress, venting, relationship issues)
- Off-topic messages get a short, non-preachy redirect

### Output Moderation
- Post-generation scan for diagnostic language and medication references
- Strips or softens unsafe content before sending to the user

### Crisis Helplines (India-focused)
- **Tele MANAS** (Govt. of India, 24/7, multilingual): 14416 or 1-800-891-4416
- **KIRAN** (Govt. of India, 24/7): 1800-599-0019
- **Vandrevala Foundation** (24/7): 1860-266-2345 / 1800-233-3330 / +91 9999 666 555

---

## RAG Knowledge Base

The `backend/app/rag/knowledge_base/` directory contains curated wellbeing content:
- Grounding techniques
- Breathing exercises
- CBT-style reframing basics
- Sleep hygiene tips
- Finding a therapist in India
- Coping with stress
- Managing loneliness
- Self-care and daily wellbeing

To rebuild the RAG index, delete the `chroma_data/` directory and restart the backend.

---

## Privacy Note

This v1 implementation uses an in-memory session store. Conversation history is **not** persisted to disk and is lost on server restart. No raw message content is logged in crisis detection events.

For production deployment, implement a clear data retention policy and consider encryption for any stored conversation data.

---

## Project Structure

```
chatBOT/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes/
│   │   │   ├── chat.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── logging_config.py
│   │   ├── guardrails/
│   │   │   ├── crisis_detector.py
│   │   │   ├── crisis_patterns.json
│   │   │   ├── topic_classifier.py
│   │   │   ├── output_moderation.py
│   │   │   └── system_prompt.py
│   │   ├── rag/
│   │   │   ├── knowledge_base/ (*.md)
│   │   │   ├── embeddings.py
│   │   │   ├── vector_store.py
│   │   │   └── retriever.py
│   │   ├── services/
│   │   │   ├── gemini_client.py
│   │   │   └── chat_service.py
│   │   ├── models/schemas.py
│   │   └── utils/session_store.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingHero/
│   │   │   ├── GradientWave/
│   │   │   ├── ChatWindow/
│   │   │   ├── MessageBubble/
│   │   │   ├── InputBar/
│   │   │   ├── CrisisBanner/
│   │   │   └── Header/
│   │   ├── hooks/useChat.js
│   │   ├── services/api.js
│   │   ├── styles/theme.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── .env.example
└── README.md
```
