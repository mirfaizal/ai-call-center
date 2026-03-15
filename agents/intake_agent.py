"""
Call Intake Agent

Validates incoming call data (audio files or transcript text/JSON),
extracts metadata, and produces a standardised CallRecord for downstream
agents.
"""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from utils.validation import (
    extract_call_metadata,
    load_transcript_file,
    sanitize_text,
    validate_audio_file,
    validate_transcript_json,
    validate_transcript_text,
)


class CallRecord(BaseModel):
    """Standardised representation of an ingested call."""

    call_id: str = Field(default="unknown", description="Unique identifier for the call")
    input_type: str = Field(description="'audio' or 'transcript'")
    raw_transcript: str = Field(default="", description="Raw transcript text (empty for audio)")
    audio_path: str = Field(default="", description="Path to audio file (empty for transcripts)")
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_valid: bool = Field(default=True)
    validation_errors: list[str] = Field(default_factory=list)


class IntakeAgent:
    """
    Validates and normalises call inputs before passing them to downstream
    agents.

    Supported inputs:
    - Audio file path (.mp3, .wav, .m4a, .ogg, .flac, .webm, .mp4)
    - Path to a .txt or .json transcript file
    - Raw transcript string
    - Parsed transcript dict (JSON schema)
    """

    def process(self, input_data: Any, call_id: str | None = None) -> CallRecord:
        """
        Route the input to the appropriate handler and return a CallRecord.

        Args:
            input_data: One of – file path (str/Path), raw transcript str,
                        or parsed transcript dict.
            call_id:    Optional call identifier; auto-derived when possible.
        """
        if isinstance(input_data, Path):
            input_data = str(input_data)

        if isinstance(input_data, dict):
            return self._handle_dict(input_data, call_id)

        if isinstance(input_data, str):
            path = Path(input_data)
            if path.exists():
                suffix = path.suffix.lower()
                if suffix in {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}:
                    return self._handle_audio(input_data, call_id)
                if suffix in {".txt", ".json"}:
                    return self._handle_transcript_file(input_data, call_id)

            # Treat as raw transcript text
            return self._handle_raw_text(input_data, call_id)

        return CallRecord(
            call_id=call_id or "unknown",
            input_type="unknown",
            is_valid=False,
            validation_errors=[f"Unsupported input type: {type(input_data).__name__}"],
        )

    # ------------------------------------------------------------------
    # Private handlers
    # ------------------------------------------------------------------

    def _handle_audio(self, file_path: str, call_id: str | None) -> CallRecord:
        result = validate_audio_file(file_path)
        if not result["valid"]:
            return CallRecord(
                call_id=call_id or Path(file_path).stem,
                input_type="audio",
                audio_path=file_path,
                is_valid=False,
                validation_errors=[result["error"]],
            )
        return CallRecord(
            call_id=call_id or Path(file_path).stem,
            input_type="audio",
            audio_path=file_path,
            metadata={"size_mb": result["size_mb"], "format": result["format"]},
        )

    def _handle_transcript_file(self, file_path: str, call_id: str | None) -> CallRecord:
        result = load_transcript_file(file_path)
        if not result["valid"]:
            return CallRecord(
                call_id=call_id or Path(file_path).stem,
                input_type="transcript",
                is_valid=False,
                validation_errors=[result["error"]],
            )
        transcript = sanitize_text(result["transcript"])
        inferred_metadata = extract_call_metadata(transcript)
        metadata = {**inferred_metadata, **result.get("metadata", {})}
        return CallRecord(
            call_id=call_id or result.get("call_id") or Path(file_path).stem,
            input_type="transcript",
            raw_transcript=transcript,
            metadata=metadata,
        )

    def _handle_raw_text(self, text: str, call_id: str | None) -> CallRecord:
        result = validate_transcript_text(text)
        if not result["valid"]:
            return CallRecord(
                call_id=call_id or "unknown",
                input_type="transcript",
                is_valid=False,
                validation_errors=[result["error"]],
            )
        transcript = sanitize_text(text)
        metadata = extract_call_metadata(transcript)
        return CallRecord(
            call_id=call_id or metadata.get("call_id", "unknown"),
            input_type="transcript",
            raw_transcript=transcript,
            metadata=metadata,
        )

    def _handle_dict(self, data: dict, call_id: str | None) -> CallRecord:
        result = validate_transcript_json(data)
        if not result["valid"]:
            return CallRecord(
                call_id=call_id or "unknown",
                input_type="transcript",
                is_valid=False,
                validation_errors=[result["error"]],
            )
        transcript = sanitize_text(result["transcript"])
        inferred_metadata = extract_call_metadata(transcript)
        metadata = {**inferred_metadata, **result.get("metadata", {})}
        return CallRecord(
            call_id=call_id or result.get("call_id") or "unknown",
            input_type="transcript",
            raw_transcript=transcript,
            metadata=metadata,
        )
