import pytest
import json
from pathlib import Path
from utils.validation import (
    extract_json_from_markdown,
    is_supported_audio_format,
    is_supported_transcript_format,
    validate_audio_file,
    validate_transcript_text,
    validate_transcript_json,
    load_transcript_file,
    sanitize_text,
    extract_call_metadata
)

def test_extract_json_from_markdown():
    markdown = "```json\n{\"key\": \"value\"}\n```"
    assert extract_json_from_markdown(markdown) == {"key": "value"}
    
    raw = '{"key": "value"}'
    assert extract_json_from_markdown(raw) == {"key": "value"}
    
    markdown2 = "```\n{\"key\": \"value\"}\n```"
    assert extract_json_from_markdown(markdown2) == {"key": "value"}
    
def test_is_supported_formats():
    assert is_supported_audio_format("test.mp3")
    assert not is_supported_audio_format("test.txt")
    assert is_supported_transcript_format("test.json")
    assert not is_supported_transcript_format("test.mp3")

def test_validate_audio_file(tmp_path):
    # Invalid file
    assert not validate_audio_file("nonexistent.mp3")["valid"]
    
    # Unsupported format
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("text")
    assert not validate_audio_file(str(txt_file))["valid"]
    
    # Valid
    mp3_file = tmp_path / "test.mp3"
    mp3_file.write_bytes(b"dummy")
    res = validate_audio_file(str(mp3_file))
    assert res["valid"]
    assert res["format"] == ".mp3"

def test_validate_transcript_text():
    assert not validate_transcript_text("")["valid"]
    assert not validate_transcript_text("   ")["valid"]
    assert validate_transcript_text("hello")["valid"]
    
    # Too long
    long_text = "a" * 50001
    assert not validate_transcript_text(long_text)["valid"]

def test_validate_transcript_json():
    assert not validate_transcript_json([])["valid"]
    assert not validate_transcript_json({})["valid"]
    
    valid_json = {"transcript": "hello", "call_id": "123"}
    res = validate_transcript_json(valid_json)
    assert res["valid"]
    assert res["transcript"] == "hello"
    assert res["call_id"] == "123"

    long_json = {"transcript": "a" * 50001}
    assert not validate_transcript_json(long_json)["valid"]

def test_load_transcript_file(tmp_path):
    assert not load_transcript_file("missing.txt")["valid"]
    
    unsupported = tmp_path / "test.mp3"
    unsupported.write_text("test")
    assert not load_transcript_file(str(unsupported))["valid"]
    
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("hello txt")
    res = load_transcript_file(str(txt_file))
    assert res["valid"]
    assert res["transcript"] == "hello txt"
    
    json_file = tmp_path / "test.json"
    json_file.write_text('{"transcript": "hello json"}')
    res2 = load_transcript_file(str(json_file))
    assert res2["valid"]
    assert res2["transcript"] == "hello json"
    
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad json")
    assert not load_transcript_file(str(bad_json))["valid"]
    
    # OSError on read_text
    from unittest.mock import patch
    with patch("pathlib.Path.read_text", side_effect=OSError("Permission denied")):
        res_os = load_transcript_file(str(txt_file))
        assert not res_os["valid"]
        assert "Could not read file" in res_os["error"]

def test_sanitize_text():
    raw = "Hello\x00 World  \n\n\nTest"
    assert sanitize_text(raw) == "Hello World \n\nTest"

def test_extract_call_metadata():
    text = "Call ID: 12345\nDate: 2024-01-15\nAgent: Bob\nCustomer: Alice\nDuration: 1:23"
    meta = extract_call_metadata(text)
    assert meta["call_id"] == "12345"
    assert meta["date"] == "2024-01-15"
    assert meta["agent"] == "Bob"
    assert meta["customer"] == "Alice"
    assert meta["duration"] == "1:23"
