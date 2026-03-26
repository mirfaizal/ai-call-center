import pytest
from pathlib import Path
from agents.intake_agent import IntakeAgent, CallRecord

@pytest.fixture
def agent():
    return IntakeAgent()

def test_process_dict(agent):
    data = {"transcript": "Hello world", "metadata": {"foo": "bar"}}
    result = agent.process(data, call_id="test1")
    assert result.is_valid
    assert result.call_id == "test1"
    assert result.input_type == "transcript"
    assert result.raw_transcript == "Hello world"

def test_process_invalid_dict(agent):
    data = {"wrong_key": "val"}
    result = agent.process(data)
    assert not result.is_valid
    assert "transcript" in result.validation_errors[0].lower() or "field" in result.validation_errors[0].lower()

def test_process_raw_text(agent):
    text = "Call ID: test2\nHello world"
    result = agent.process(text)
    assert result.is_valid
    assert result.call_id == "test2"
    assert result.raw_transcript == "Call ID: test2\nHello world"

def test_process_invalid_text(agent):
    result = agent.process("   ")
    assert not result.is_valid

def test_process_audio_file(tmp_path, agent):
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"dummy audio content")
    
    result = agent.process(str(audio_file))
    assert result.is_valid
    assert result.input_type == "audio"
    assert result.audio_path == str(audio_file)

def test_process_invalid_audio_file(tmp_path, agent):
    audio_file = tmp_path / "test.mp3"
    # Don't create the file so it fails exists check, wait, if it doesn't exist, intake agent falls back to handle_raw_text
    # "is_valid" will be False because "test.mp3" is not a valid text? No, it's just a short string. It WILL be valid raw text!
    # Let's create a huge audio file size to fail validation
    audio_file.write_bytes(b"0" * (26 * 1024 * 1024)) # 26MB
    
    result = agent.process(str(audio_file))
    assert not result.is_valid
    assert "limit" in " ".join(result.validation_errors).lower() or "MB" in " ".join(result.validation_errors).lower()
    
def test_process_transcript_file(tmp_path, agent):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Hello file")
    
    result = agent.process(str(txt_file))
    assert result.is_valid
    assert result.input_type == "transcript"
    assert result.raw_transcript == "Hello file"

def test_process_invalid_transcript_file(tmp_path, agent):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("   ")
    
    result = agent.process(str(txt_file))
    assert not result.is_valid

def test_process_transcript_file_json(tmp_path, agent):
    json_file = tmp_path / "test.json"
    json_file.write_text('{"transcript": "json file text"}')
    
    result = agent.process(str(json_file))
    assert result.is_valid
    assert result.input_type == "transcript"
    assert result.raw_transcript == "json file text"

def test_process_invalid_type(agent):
    result = agent.process(123)
    assert not result.is_valid
    assert result.input_type == "unknown"

def test_process_path(tmp_path, agent):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Path object")
    result = agent.process(txt_file)
    assert result.is_valid
    assert result.raw_transcript == "Path object"
