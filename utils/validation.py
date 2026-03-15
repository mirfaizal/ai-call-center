"""
Validation utilities for the AI Call Center system.
Provides schema validation, input sanitization, and format checking.
"""

import re
import json
import os
from pathlib import Path
from typing import Any

SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}
SUPPORTED_TRANSCRIPT_FORMATS = {".json", ".txt"}
MAX_TRANSCRIPT_LENGTH = 50_000
MAX_AUDIO_FILE_SIZE_MB = 25


def is_supported_audio_format(filename: str) -> bool:
    """Return True if the file extension is a supported audio format."""
    return Path(filename).suffix.lower() in SUPPORTED_AUDIO_FORMATS


def is_supported_transcript_format(filename: str) -> bool:
    """Return True if the file extension is a supported transcript format."""
    return Path(filename).suffix.lower() in SUPPORTED_TRANSCRIPT_FORMATS


def validate_audio_file(file_path: str) -> dict[str, Any]:
    """
    Validate an audio file and return metadata.

    Returns a dict with keys: valid (bool), error (str|None), size_mb (float),
    format (str).
    """
    path = Path(file_path)
    if not path.exists():
        return {"valid": False, "error": f"File not found: {file_path}"}

    fmt = path.suffix.lower()
    if fmt not in SUPPORTED_AUDIO_FORMATS:
        return {
            "valid": False,
            "error": (
                f"Unsupported audio format '{fmt}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}"
            ),
        }

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_AUDIO_FILE_SIZE_MB:
        return {
            "valid": False,
            "error": (
                f"File size {size_mb:.1f} MB exceeds the {MAX_AUDIO_FILE_SIZE_MB} MB limit."
            ),
        }

    return {"valid": True, "error": None, "size_mb": round(size_mb, 2), "format": fmt}


def validate_transcript_text(text: str) -> dict[str, Any]:
    """
    Validate raw transcript text.

    Returns a dict with keys: valid (bool), error (str|None), length (int).
    """
    if not text or not text.strip():
        return {"valid": False, "error": "Transcript text is empty."}

    stripped = text.strip()
    if len(stripped) > MAX_TRANSCRIPT_LENGTH:
        return {
            "valid": False,
            "error": (
                f"Transcript length {len(stripped):,} characters exceeds the "
                f"{MAX_TRANSCRIPT_LENGTH:,} character limit."
            ),
        }

    return {"valid": True, "error": None, "length": len(stripped)}


def validate_transcript_json(data: Any) -> dict[str, Any]:
    """
    Validate a transcript supplied as a parsed JSON object.

    Expected schema:
        {
            "call_id": str,          # optional
            "transcript": str,       # required
            "metadata": { ... }      # optional
        }

    Returns a dict with keys: valid (bool), error (str|None), call_id (str|None),
    transcript (str|None), metadata (dict).
    """
    if not isinstance(data, dict):
        return {"valid": False, "error": "JSON transcript must be a JSON object (dict)."}

    transcript_text = data.get("transcript") or data.get("text") or data.get("content")
    if not transcript_text:
        return {
            "valid": False,
            "error": "JSON transcript must contain a 'transcript', 'text', or 'content' field.",
        }

    text_result = validate_transcript_text(str(transcript_text))
    if not text_result["valid"]:
        return text_result

    return {
        "valid": True,
        "error": None,
        "call_id": data.get("call_id"),
        "transcript": str(transcript_text),
        "metadata": data.get("metadata", {}),
    }


def load_transcript_file(file_path: str) -> dict[str, Any]:
    """
    Load and validate a transcript from a .txt or .json file.

    Returns a dict with keys: valid (bool), error (str|None), transcript (str),
    call_id (str|None), metadata (dict).
    """
    path = Path(file_path)
    if not path.exists():
        return {"valid": False, "error": f"File not found: {file_path}"}

    fmt = path.suffix.lower()
    if fmt not in SUPPORTED_TRANSCRIPT_FORMATS:
        return {
            "valid": False,
            "error": (
                f"Unsupported transcript format '{fmt}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_TRANSCRIPT_FORMATS))}"
            ),
        }

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"valid": False, "error": f"Could not read file: {exc}"}

    if fmt == ".json":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return {"valid": False, "error": f"Invalid JSON: {exc}"}
        return validate_transcript_json(data)

    # Plain text
    result = validate_transcript_text(raw)
    if not result["valid"]:
        return result
    return {
        "valid": True,
        "error": None,
        "transcript": raw.strip(),
        "call_id": path.stem,
        "metadata": {},
    }


def sanitize_text(text: str) -> str:
    """Remove control characters and normalize whitespace in transcript text."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_call_metadata(text: str) -> dict[str, Any]:
    """
    Heuristically extract simple metadata from a raw transcript string.

    Looks for common call-center header patterns such as:
        Call ID: ABC-123
        Date: 2024-01-15
        Agent: John Smith
        Customer: Jane Doe
        Duration: 5:32
    """
    metadata: dict[str, Any] = {}

    patterns = {
        "call_id": r"(?:call[_\s]?id)[:\s]+([A-Za-z0-9_\-]+)",
        "date": r"(?:date)[:\s]+([\d]{4}[-/][\d]{2}[-/][\d]{2}|[\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})",
        "agent": r"(?:agent)[:\s]+([\w .'\-]+?)(?:\n|$)",
        "customer": r"(?:customer|caller)[:\s]+([\w .'\-]+?)(?:\n|$)",
        "duration": r"(?:duration)[:\s]+([\d:]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata[key] = match.group(1).strip()

    return metadata
