"""
Transcription Agent

Converts audio files to text using the OpenAI Whisper API.
Falls back gracefully when the API key is not available.
"""

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    """Result of transcribing an audio file."""

    call_id: str = Field(default="unknown")
    transcript: str = Field(default="")
    language: str = Field(default="en")
    success: bool = Field(default=True)
    error: str = Field(default="")


class TranscriptionAgent:
    """
    Transcribes audio files to text using the OpenAI Whisper API.

    If no API key is present the agent returns a clear error rather than
    raising an unhandled exception, enabling graceful degradation in the
    routing layer.
    """

    SUPPORTED_FORMATS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}

    def __init__(self, api_key: str | None = None, model: str = "whisper-1"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    def transcribe(self, audio_path: str, call_id: str = "unknown") -> TranscriptionResult:
        """
        Transcribe an audio file and return a TranscriptionResult.

        Args:
            audio_path: Absolute or relative path to the audio file.
            call_id:    Identifier used to tag the result.
        """
        path = Path(audio_path)

        if not path.exists():
            return TranscriptionResult(
                call_id=call_id,
                success=False,
                error=f"Audio file not found: {audio_path}",
            )

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return TranscriptionResult(
                call_id=call_id,
                success=False,
                error=(
                    f"Unsupported format '{path.suffix}'. "
                    f"Supported: {', '.join(sorted(self.SUPPORTED_FORMATS))}"
                ),
            )

        if not self.api_key:
            return TranscriptionResult(
                call_id=call_id,
                success=False,
                error=(
                    "OpenAI API key not configured. "
                    "Set the OPENAI_API_KEY environment variable."
                ),
            )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="verbose_json",
                )
            return TranscriptionResult(
                call_id=call_id,
                transcript=response.text,
                language=getattr(response, "language", "en"),
                success=True,
            )
        except Exception as exc:  # noqa: BLE001
            return TranscriptionResult(
                call_id=call_id,
                success=False,
                error=f"Transcription failed: {exc}",
            )
