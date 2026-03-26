---
title: Ai Call Center
emoji: 👀
colorFrom: yellow
colorTo: indigo
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# AI Call Center Analyzer

A modular multi-agent AI system that converts raw call center data (audio recordings or text transcripts) into structured summaries and QA insights.

---

## Features

- **Automated Transcription** – Convert audio files to text using OpenAI Whisper
- **Structured Summaries** – Extract key points, action items, sentiment, and resolution status
- **QA Scoring** – Score empathy, professionalism, communication, and resolution (1-10 rubric)
- **Multi-Agent Pipeline** – Modular agents with graceful fallback/retry logic via LangChain
- **Angular UI & FastAPI Backend** – Upload audio/transcripts and visualize all outputs interactively
- **SQLite Persistence** – Automatically store and retrieve past call analyses and media
- **Docker Support** – One-command deployment with Docker Compose

---

## Architecture

```
ai-call-center/
├── agents/
│   ├── intake_agent.py          # Validates inputs, extracts metadata
│   ├── transcription_agent.py   # Audio → text via OpenAI Whisper
│   ├── summarization_agent.py   # Structured summaries using LangChain
│   ├── quality_score_agent.py   # QA scoring with Pydantic rubric
│   └── routing_agent.py         # Pipeline orchestration & fallback logic
├── api_main.py                  # FastAPI backend and SQLite DB operations
├── ui/                          # Angular frontend web interface
│   ├── src/                     # UI source code
│   └── nginx.conf               # Nginx server configuration for Docker
├── utils/
│   ├── mcp_router.py            # Unified LangChain LLM invocation router
│   └── validation.py            # Shared validation helpers
├── data/
│   ├── sample_transcripts/      # Example call transcripts (JSON & TXT)
│   └── calls.db                 # SQLite database storing analysis history
├── config/
│   └── mcp.yaml                 # Model control plane configuration
├── docker-compose.yml
├── Dockerfile                   # Backend Dockerfile
└── requirements.txt
```

### Agent Pipeline

```
Input (audio/transcript)
        │
        ▼
 ┌─────────────┐
 │ Intake Agent│  ← validates format, extracts metadata
 └──────┬──────┘
        │
        ├── audio? ──▶ ┌──────────────────────┐
        │               │ Transcription Agent  │  ← OpenAI Whisper
        │               └──────────┬───────────┘
        │                          │
        ▼                          ▼
 ┌─────────────────────────────────────────┐
 │          Summarization Agent            │  ← GPT-4o via LangChain router
 └──────────────────────┬──────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────┐
 │         Quality Scoring Agent           │  ← GPT-4o + Pydantic rubric
 └──────────────────────┬──────────────────┘
                        │
                        ▼
                 PipelineResult
```

---

## Quick Start

### Prerequisites

- Basic system requirements (Node.js for local UI dev, Python 3.11+ for local backend dev)
- Docker Desktop (recommended)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Docker (Recommended)

The easiest way to run the entire stack (Frontend + Backend + Database) is via Docker Compose:

```bash
# Clone the repository
git clone https://github.com/mirfaizal/ai-call-center.git
cd ai-call-center

# Build and run using Docker Compose
OPENAI_API_KEY=sk-... docker compose up --build -d
```

- **Frontend UI:** Open **http://localhost:8501** in your browser.
- **Backend API Docs:** Open **http://localhost:8000/docs** in your browser.

### Local setup (Without Docker)

If you prefer to run the services separately on your host machine:

**1. Start the Backend API:**
```bash
# Install backend dependencies
pip install -r requirements.txt

# Set your API key
export OPENAI_API_KEY=sk-...

# Run the FastAPI server
uvicorn api_main:app --reload --port 8000
```

**2. Start the Frontend UI:**
```bash
# Navigate to UI directory
cd ui

# Install Node dependencies
npm install

# Start the Angular development server
ng serve
```
Open **http://localhost:4200** to view the app in local dev mode.

---

## Usage

### UI Dashboard

1. Enter your **OpenAI API key** in the UI settings (or set `OPENAI_API_KEY` env var)
2. Choose a **Primary Model** (default: `gpt-4o`)
3. Upload an audio file/transcript, or paste text directly into the analyzer.
4. Click **Analyze Call** to run the full pipeline.
5. View Transcript, Summary, Quality Scores, Tags, and raw JSON output.
6. The dashboard also stores a history of your past uploaded calls for easy retrieval.

### Python API

You can still use the multi-agent pipeline programmatically:

```python
from agents.routing_agent import RoutingAgent

# Initialize with the LangChain router
agent = RoutingAgent(api_key="sk-...")

# Analyze a transcript file
result = agent.run("data/sample_transcripts/call_001.json")

print(result.summary.summary)
print(result.quality_scores.overall_score)

# Analyze audio
result = agent.run("recording.mp3")
```

### JSON Transcript Format

```json
{
  "call_id": "CALL-001",
  "transcript": "Agent: Hello, how can I help?\nCustomer: I need…",
  "metadata": {
    "date": "2024-01-15",
    "agent": "Jane Smith",
    "customer": "Bob Jones",
    "duration": "5:30"
  }
}
```

---

## Configuration

Edit `config/mcp.yaml` to customise model selection, fallback behaviour, and cost controls:

```yaml
models:
  primary:
    provider: openai
    name: gpt-4o
  fallback:
    provider: openai
    name: gpt-3.5-turbo

routing:
  max_retries: 2
  fallback_on_error: true
```

---

## Sample Data

Three sample transcripts are included in `data/sample_transcripts/`:

| File | Scenario |
|------|----------|
| `call_001.json` | IT Support – VPN connectivity issue (resolved) |
| `call_002.txt` | Billing – Unrecognised charge and refund request |
| `call_003.json` | ISP Support – Slow internet speed (resolved with credit) |

---

## Supported Input Formats

| Type | Extensions |
|------|-----------|
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.webm`, `.mp4` |
| Transcript | `.txt`, `.json`, raw text string |

Audio files must be ≤ 25 MB (OpenAI Whisper limit).

---

## License

MIT