# AI Call Center Analyzer

A modular multi-agent AI system that converts raw call center data (audio recordings or text
transcripts) into structured summaries and QA insights.

---

## Features

- **Automated Transcription** – Convert audio files to text using OpenAI Whisper
- **Structured Summaries** – Extract key points, action items, sentiment, and resolution status
- **QA Scoring** – Score empathy, professionalism, communication, and resolution (1-10 rubric)
- **Multi-Agent Pipeline** – Modular agents with graceful fallback/retry logic
- **Streamlit UI** – Upload audio/transcripts and visualize all outputs interactively
- **Docker Support** – One-command deployment with Docker Compose

---

## Architecture

```
ai-call_center/
├── agents/
│   ├── intake_agent.py          # Validates inputs, extracts metadata
│   ├── transcription_agent.py   # Audio → text via OpenAI Whisper
│   ├── summarization_agent.py   # LangChain + GPT structured summaries
│   ├── quality_score_agent.py   # QA scoring with Pydantic rubric
│   └── routing_agent.py         # Pipeline orchestration & fallback logic
├── ui/
│   └── streamlit_app.py         # Interactive web interface
├── utils/
│   └── validation.py            # Shared validation helpers
├── data/
│   └── sample_transcripts/      # Example call transcripts (JSON & TXT)
├── config/
│   └── mcp.yaml                 # Model control plane configuration
├── docker-compose.yml
├── Dockerfile
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
 │          Summarization Agent            │  ← GPT-4o via LangChain
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

- Python 3.11+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Local setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/mirfaizal/ai-call_center.git
cd ai-call_center

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
export OPENAI_API_KEY=sk-...

# 4. Launch the UI
streamlit run ui/streamlit_app.py
```

Open **http://localhost:8501** in your browser.

### Docker

```bash
# Build and run
OPENAI_API_KEY=sk-... docker compose up --build
```

Open **http://localhost:8501** in your browser.

---

## Usage

### Streamlit UI

1. Enter your **OpenAI API key** in the sidebar (or set `OPENAI_API_KEY` env var)
2. Choose a **Primary Model** (default: `gpt-4o`)
3. **Upload File** tab: upload an audio file or transcript, or select a sample
4. **Paste Transcript** tab: paste text directly
5. Click **Analyze Call** to run the full pipeline
6. View Transcript, Summary, Quality Scores, Tags, and raw JSON output

### Python API

```python
from agents.routing_agent import RoutingAgent

agent = RoutingAgent(api_key="sk-...")

# Analyze a transcript file
result = agent.run("data/sample_transcripts/call_001.json")

print(result.summary.summary)
print(result.quality_scores.overall_score)

# Analyze raw text
result = agent.run("Agent: Hello…\nCustomer: Hi…")

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