from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import tempfile
import os
import json
import sqlite3
import threading
from datetime import datetime

from agents.routing_agent import RoutingAgent, PipelineResult

app = FastAPI(title="AI Call Center API")

# ── SQLite database ───────────────────────────────────────────────────
_DB_PATH = os.environ.get("CALLS_DB_PATH", "/app/data/calls.db")
_MEDIA_PATH = os.environ.get("MEDIA_PATH", "/app/data/media")
_db_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    os.makedirs(_MEDIA_PATH, exist_ok=True)
    with _db_lock, _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                call_id          TEXT PRIMARY KEY,
                analyzed_at      TEXT NOT NULL,
                metadata         TEXT NOT NULL DEFAULT '{}',
                summary          TEXT,
                quality_scores   TEXT,
                final_transcript TEXT,
                raw_json         TEXT NOT NULL
            )
        """)
        conn.commit()


_init_db()

# Allow requests from the Angular dev server and Docker Nginx frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeTextRequest(BaseModel):
    transcript_text: str
    call_id: Optional[str] = None
    api_key: Optional[str] = None
    model_choice: str = "gpt-4o"


def _store_result(call_id: str, result: PipelineResult) -> None:
    """Persist analysis result in SQLite."""
    row = {
        "call_id": call_id,
        "analyzed_at": datetime.utcnow().isoformat(),
        "metadata": json.dumps(result.call_record.metadata if result.call_record else {}),
        "summary": json.dumps(result.summary.model_dump()) if result.summary else None,
        "quality_scores": json.dumps(result.quality_scores.model_dump()) if result.quality_scores else None,
        "final_transcript": result.final_transcript,
        "raw_json": json.dumps(result.model_dump()),
    }
    with _db_lock, _get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO calls
                (call_id, analyzed_at, metadata, summary, quality_scores, final_transcript, raw_json)
            VALUES
                (:call_id, :analyzed_at, :metadata, :summary, :quality_scores, :final_transcript, :raw_json)
        """, row)
        conn.commit()


@app.post("/api/analyze/text", response_model=PipelineResult)
async def analyze_text(request: AnalyzeTextRequest):
    if not request.transcript_text.strip():
        raise HTTPException(status_code=400, detail="Transcript text cannot be empty.")
        
    api_key = request.api_key or os.environ.get("OPENAI_API_KEY", "")
    
    routing_agent = RoutingAgent(
        api_key=api_key,
        summarization_model=request.model_choice,
        scoring_model=request.model_choice
    )
    
    call_id = request.call_id or "pasted-transcript"
    result: PipelineResult = routing_agent.run(request.transcript_text, call_id=call_id)
    _store_result(call_id, result)
    return result


@app.post("/api/analyze/file", response_model=PipelineResult)
async def analyze_file(
    file: UploadFile = File(...),
    call_id: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    model_choice: str = Form("gpt-4o")
):
    api_key_to_use = api_key or os.environ.get("OPENAI_API_KEY", "")
    
    routing_agent = RoutingAgent(
        api_key=api_key_to_use,
        summarization_model=model_choice,
        scoring_model=model_choice
    )
    
    suffix = os.path.splitext(file.filename)[1]
    file_bytes = await file.read()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
        
    call_id_to_use = call_id or os.path.splitext(file.filename)[0]
    
    try:
        result: PipelineResult = routing_agent.run(tmp_path, call_id=call_id_to_use)
        
        # Save media file persistently if it's an audio/video type
        if suffix.lower() in [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4"]:
            media_path = os.path.join(_MEDIA_PATH, f"{call_id_to_use}{suffix}")
            with open(media_path, "wb") as f:
                f.write(file_bytes)
            if hasattr(result, "call_record") and result.call_record:
                if result.call_record.metadata is None:
                    result.call_record.metadata = {}
                result.call_record.metadata["audio_url"] = f"/api/media/{call_id_to_use}{suffix}"
                
        _store_result(call_id_to_use, result)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
            
    return result


# ── SQLite-backed endpoints ────────────────────────────────────────────

@app.get("/api/media/{filename}")
def get_media(filename: str):
    """Serve saved media files for playback."""
    file_path = os.path.join(_MEDIA_PATH, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Media not found")
    return FileResponse(file_path)

@app.get("/api/calls")
def list_calls() -> JSONResponse:
    """Return a summary list of all analyzed calls, newest first."""
    with _db_lock, _get_conn() as conn:
        rows = conn.execute(
            "SELECT call_id, analyzed_at, metadata, summary, quality_scores FROM calls ORDER BY analyzed_at DESC"
        ).fetchall()

    data = []
    for r in rows:
        summary = json.loads(r["summary"]) if r["summary"] else None
        quality_scores = json.loads(r["quality_scores"]) if r["quality_scores"] else None
        data.append({
            "call_id": r["call_id"],
            "analyzed_at": r["analyzed_at"],
            "metadata": json.loads(r["metadata"]),
            "overall_score": quality_scores["overall_score"] if quality_scores else None,
            "sentiment": summary["customer_sentiment"] if summary else None,
            "resolution_status": summary["resolution_status"] if summary else None,
            "summary_text": summary.get("summary") if summary else None,
            "tags": summary.get("tags", []) if summary else [],
        })
    return JSONResponse(content=data, headers={"Cache-Control": "no-store"})


@app.get("/api/calls/{call_id}")
def get_call(call_id: str) -> JSONResponse:
    """Return the full stored record for a single analyzed call."""
    with _db_lock, _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM calls WHERE call_id = ?", (call_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Call '{call_id}' not found.")
    summary = json.loads(row["summary"]) if row["summary"] else None
    quality_scores = json.loads(row["quality_scores"]) if row["quality_scores"] else None
    return JSONResponse(content={
        "call_id": row["call_id"],
        "analyzed_at": row["analyzed_at"],
        "metadata": json.loads(row["metadata"]),
        "summary": summary,
        "quality_scores": quality_scores,
        "final_transcript": row["final_transcript"],
        "raw_json": json.loads(row["raw_json"]),
    }, headers={"Cache-Control": "no-store"})


@app.delete("/api/calls/{call_id}")
def delete_call(call_id: str) -> Dict[str, str]:
    with _db_lock, _get_conn() as conn:
        cur = conn.execute("DELETE FROM calls WHERE call_id = ?", (call_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Call '{call_id}' not found.")
    return {"deleted": call_id}


@app.get("/api/health")
def health_check():
    with _db_lock, _get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
    return {"status": "healthy", "calls_stored": count}
