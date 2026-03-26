import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from agents.transcription_agent import TranscriptionAgent

def test_transcribe_audio_not_found():
    agent = TranscriptionAgent(api_key="fake")
    res = agent.transcribe("fake.mp3")
    assert not res.success
    assert "not found" in res.error

def test_transcribe_unsupported_format(tmp_path):
    agent = TranscriptionAgent(api_key="fake")
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello")
    res = agent.transcribe(str(txt_file))
    assert not res.success
    assert "Unsupported format" in res.error

@patch.dict(os.environ, clear=True)
def test_transcribe_no_api_key(tmp_path):
    agent = TranscriptionAgent(api_key="")
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"dummy")
    res = agent.transcribe(str(mp3_file))
    assert not res.success
    assert "API key not configured" in res.error
    
@patch("openai.OpenAI")
def test_transcribe_success(mock_openai_class, tmp_path):
    agent = TranscriptionAgent(api_key="fake")
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"dummy")
    
    # Mocking OpenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked transcript"
    mock_response.language = "en"
    
    mock_client.audio.transcriptions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client
    
    res = agent.transcribe(str(mp3_file))
    assert res.success
    assert res.transcript == "Mocked transcript"
    assert res.language == "en"

@patch("openai.OpenAI")
def test_transcribe_exception(mock_openai_class, tmp_path):
    agent = TranscriptionAgent(api_key="fake")
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"dummy")
    
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.side_effect = Exception("OpenAI Error")
    mock_openai_class.return_value = mock_client
    
    res = agent.transcribe(str(mp3_file))
    assert not res.success
    assert "Transcription failed: OpenAI Error" in res.error
