# MindBridge — Mental Health Support Chatbot

A mental wellbeing support chatbot with a FastAPI backend (Gemini API, RAG, guardrails) and a React + Vite frontend.

> **Important**: This is a wellbeing support tool, not a substitute for professional mental health care. In an emergency, contact local emergency services or the helplines listed below.

---

## Architecture

```
User message (text or voice)
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
Concern Classifier (keyword + Gemini fallback)
    |  stress / anxiety / relationship / none
    v
Therapist Suggestion (from curated JSON)
    |  3 MindPeers therapist links per category
    v
Response -> Frontend -> Chat UI + Therapist Cards
```

---

## Features

### Voice Input (Web Speech API)

Users can speak their messages instead of typing — especially useful for expressing difficult emotions.

- **Real-time transcription**: The input field updates live as the user speaks, showing both interim (unconfirmed) and final text
- **Continuous mode**: Keeps listening across natural pauses in speech
- **Auto-stop**: Silences for 3 seconds triggers automatic stop; hard cutoff at 60 seconds to prevent runaway sessions
- **Graceful degradation**: The mic button is hidden entirely in unsupported browsers (Firefox, Safari); works in Chrome and Edge
- **Error handling**: Friendly messages for denied microphone permissions, missing devices, and network errors; auto-dismiss after 3 seconds
- **Append mode**: Voice input appends to any existing text in the input field, so users can combine typing and speaking

### Therapist Suggestions

The chatbot intelligently identifies the user's concern category and suggests relevant MindPeers therapists.

- **Two-stage classification**: Fast keyword matching first, then Gemini LLM fallback for ambiguous messages
- **Three concern categories**: Stress, Anxiety, and Relationship — each with 3 curated therapists
- **Smart throttling**: Suggestions appear only once per session to avoid being pushy (`should_suggest_therapists` / `mark_therapist_suggested`)
- **Clickable therapist cards**: Each suggestion links directly to the therapist's profile on `dashboard.mindpeers.co` (opens in a new tab)
- **Randomised CTAs**: The call-to-action text varies across 5 friendly variants to feel natural
- **Feature flag**: Can be toggled on/off via the `ENABLE_THERAPIST_SUGGESTIONS` environment variable
- **Backend-driven**: All classification and suggestion logic runs server-side; the frontend simply renders what it receives

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11+ |
| LLM | Google Gemini API (`gemini-2.5-flash`) |
| Embeddings | Gemini `gemini-embedding-001` |
| Vector Store | ChromaDB (local, file-based) |
| Frontend | React + Vite |
| Styling | Plain CSS with CSS custom properties |
| Voice Input | Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) |
| Sessions | In-memory (keyed by `session_id`) |
| Deployment | Vercel (serverless Python + static frontend) |

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
| `EMBEDDING_MODEL` | No | `gemini-embedding-001` | Embedding model |
| `CHROMA_PERSIST_DIR` | No | `/tmp/chroma_data` | ChromaDB storage path |
| `LOG_LEVEL` | No | `info` | Logging level |
| `MAX_SESSION_HISTORY` | No | `20` | Max conversation turns per session |
| `CORS_ORIGINS` | No | `localhost:5173,...` | Comma-separated allowed CORS origins |
| `RAG_TOP_K` | No | `5` | Number of RAG chunks to retrieve per query |
| `ENABLE_THERAPIST_SUGGESTIONS` | No | `true` | Toggle therapist suggestions on/off |

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

### Concern Classifier
- Classifies in-scope messages into: **stress**, **anxiety**, **relationship**, or **none**
- Same two-stage pattern: keyword matching → Gemini LLM fallback
- Only runs for non-crisis, in-scope messages (after crisis detection and topic classification)
- Powers the therapist suggestion feature

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

## Deployment

The project is configured for **Vercel** deployment:
- `vercel.json` handles build commands, API rewrites, and static asset caching
- Frontend builds to `frontend/dist` and is served as static files
- Backend API routes are served via Vercel's serverless Python runtime (`api/index.py`)

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
│   │   ├── data/
│   │   │   └── therapists.json          # Curated therapist data per category
│   │   ├── guardrails/
│   │   │   ├── crisis_detector.py
│   │   │   ├── crisis_patterns.json
│   │   │   ├── topic_classifier.py
│   │   │   ├── concern_classifier.py    # NEW — concern classification + therapist lookup
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
│   │   │   ├── InputBar/                # Voice input (mic button + Web Speech API)
│   │   │   ├── CrisisBanner/
│   │   │   ├── Header/
│   │   │   └── TherapistSuggestion/     # NEW — therapist recommendation cards
│   │   ├── hooks/
│   │   │   ├── useChat.js
│   │   │   └── useSpeechRecognition.js  # NEW — Web Speech API hook
│   │   ├── services/api.js
│   │   ├── styles/theme.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── .env.example
├── api/
│   └── index.py                         # Vercel serverless entry point
├── vercel.json
└── README.md
```
