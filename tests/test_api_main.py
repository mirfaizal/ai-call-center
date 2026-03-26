import pytest
import os
import tempfile
import json
from unittest.mock import patch

# Configure env vars before importing api_main
tmp_db_fd, tmp_db_path = tempfile.mkstemp(suffix=".db")
os.environ["CALLS_DB_PATH"] = tmp_db_path

tmp_media_dir = tempfile.mkdtemp()
os.environ["MEDIA_PATH"] = tmp_media_dir

from fastapi.testclient import TestClient
from api_main import app, _get_conn
from agents.routing_agent import PipelineResult
from agents.intake_agent import CallRecord
from agents.summarization_agent import CallSummary
from agents.quality_score_agent import QualityScores

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    with _get_conn() as conn:
        conn.execute("DELETE FROM calls")
        conn.commit()

def test_health_check_empty():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["calls_stored"] == 0

@patch("api_main.RoutingAgent.run")
def test_analyze_text(mock_run):
    mock_run.return_value = PipelineResult(
        call_id="test_id",
        call_record=CallRecord(input_type="transcript", raw_transcript="test text", metadata={"agent": "Bob"}),
        summary=CallSummary(summary="test summary", customer_sentiment="positive", resolution_status="resolved", success=True),
        quality_scores=QualityScores(overall_score=8.5, success=True),
        final_transcript="test text",
        success=True
    )
    
    resp = client.post("/api/analyze/text", json={"transcript_text": "hello", "call_id": "test_id"})
    assert resp.status_code == 200
    
    # Check calls list
    calls = client.get("/api/calls").json()
    assert len(calls) == 1
    assert calls[0]["call_id"] == "test_id"
    assert calls[0]["overall_score"] == 8.5
    
    # Check single call
    single = client.get("/api/calls/test_id").json()
    assert single["call_id"] == "test_id"
    assert single["quality_scores"]["overall_score"] == 8.5

def test_analyze_text_empty():
    resp = client.post("/api/analyze/text", json={"transcript_text": "   "})
    assert resp.status_code == 400

@patch("api_main.RoutingAgent.run")
def test_analyze_file(mock_run):
    mock_record = CallRecord(input_type="audio")
    mock_record.metadata = None  # To hit the `metadata is None` branch
    
    mock_run.return_value = PipelineResult(
        call_id="audio_test",
        call_record=mock_record,
        success=True,
        final_transcript="audio mocked",
        summary=CallSummary(summary="sum"),
        quality_scores=QualityScores(overall_score=9)
    )
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"dummy audio text")
        f.flush()
        
        with open(f.name, "rb") as audio:
            resp = client.post(
                "/api/analyze/file",
                files={"file": ("test.mp3", audio, "audio/mpeg")},
                data={"call_id": "audio_test"}
            )
            
    assert resp.status_code == 200

    # Check that media file was saved
    media_path = os.path.join(tmp_media_dir, "audio_test.mp3")
    assert os.path.exists(media_path)
    
    # Also test get media endpoint
    media_resp = client.get("/api/media/audio_test.mp3")
    assert media_resp.status_code == 200
    assert media_resp.content == b"dummy audio text"

@patch("api_main.RoutingAgent.run")
@patch("os.unlink")
def test_analyze_file_unlink_error(mock_unlink, mock_run):
    mock_run.return_value = PipelineResult(call_id="test", success=True)
    mock_unlink.side_effect = OSError("unlink error")
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"dummy")
        f.flush()
        with open(f.name, "rb") as txt:
            resp = client.post("/api/analyze/file", files={"file": ("t.txt", txt, "text/plain")})
    assert resp.status_code == 200

def test_get_call_not_found():
    resp = client.get("/api/calls/nonexistent")
    assert resp.status_code == 404

def test_delete_call_not_found():
    resp = client.delete("/api/calls/nonexistent")
    assert resp.status_code == 404

@patch("api_main.RoutingAgent.run")
def test_delete_call_success(mock_run):
    mock_run.return_value = PipelineResult(
        call_id="del_test",
        call_record=CallRecord(input_type="transcript"),
        success=True
    )
    client.post("/api/analyze/text", json={"transcript_text": "hello", "call_id": "del_test"})
    
    resp = client.delete("/api/calls/del_test")
    assert resp.status_code == 200
    
    resp_check = client.get("/api/calls/del_test")
    assert resp_check.status_code == 404

def test_get_media_not_found():
    resp = client.get("/api/media/missing.mp3")
    assert resp.status_code == 404
