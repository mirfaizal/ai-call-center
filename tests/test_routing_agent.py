import pytest
from unittest.mock import patch, MagicMock
from agents.routing_agent import RoutingAgent, PipelineResult
from agents.transcription_agent import TranscriptionResult
from agents.summarization_agent import CallSummary
from agents.quality_score_agent import QualityScores

def test_run_invalid_intake():
    agent = RoutingAgent(api_key="fake")
    res = agent.run("   ")  # invalid intake
    assert not res.success
    assert len(res.errors) > 0

@patch("agents.transcription_agent.TranscriptionAgent.transcribe")
def test_run_audio_transcription_fails(mock_transcribe, tmp_path):
    mock_transcribe.return_value = TranscriptionResult(success=False, error="Mock error")
    
    agent = RoutingAgent(api_key="fake")
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"dummy")
    
    res = agent.run(str(mp3_file))
    assert not res.success
    assert "Failed" in res.errors[0] or "failed" in res.errors[0]

@patch("agents.transcription_agent.TranscriptionAgent.transcribe")
@patch("agents.summarization_agent.SummarizationAgent.summarize")
@patch("agents.quality_score_agent.QualityScoringAgent.score")
def test_run_audio_transcription_success(mock_score, mock_summarize, mock_transcribe, tmp_path):
    mock_transcribe.return_value = TranscriptionResult(success=True, transcript="transcribed mocked")
    mock_score.return_value = QualityScores(success=True)
    mock_summarize.return_value = CallSummary(success=True)
    
    agent = RoutingAgent(api_key="fake")
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"dummy")
    
    res = agent.run(str(mp3_file))
    assert res.success
    assert res.final_transcript == "transcribed mocked"
    assert len(res.errors) == 0

@patch("agents.transcription_agent.TranscriptionAgent.transcribe")
def test_run_audio_empty_transcript(mock_transcribe, tmp_path):
    mock_transcribe.return_value = TranscriptionResult(success=True, transcript="   ")
    
    agent = RoutingAgent(api_key="fake")
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"dummy")
    
    res = agent.run(str(mp3_file))
    assert not res.success
    assert "No transcript available" in "\n".join(res.errors)

@patch("agents.summarization_agent.SummarizationAgent.summarize")
@patch("agents.quality_score_agent.QualityScoringAgent.score")
def test_run_transcript_success(mock_score, mock_summarize):
    mock_score.return_value = QualityScores(success=True)
    mock_summarize.return_value = CallSummary(success=True)
    
    agent = RoutingAgent(api_key="fake")
    res = agent.run("A valid transcript text")
    assert res.success
    assert len(res.errors) == 0

@patch("agents.summarization_agent.SummarizationAgent.summarize")
@patch("agents.quality_score_agent.QualityScoringAgent.score")
def test_run_transcript_all_retries_fail(mock_score, mock_summarize):
    mock_summarize.side_effect = Exception("Fatal summary error")
    mock_score.side_effect = Exception("Fatal score error")
    
    agent = RoutingAgent(api_key="fake", max_retries=1)
    res = agent.run("A valid transcript text")
    assert not res.success
    assert "exceptions" in str(res.errors).lower() or "failed" in str(res.errors).lower()
