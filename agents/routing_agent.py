"""
Routing Agent

Orchestrates the end-to-end pipeline using LangGraph-style conditional
routing.  Each node in the graph corresponds to one agent.  The routing
agent handles:

  - Directing audio inputs through the transcription node
  - Directing transcript inputs directly to summarisation
  - Retrying or falling back when an upstream node fails
  - Emitting a final PipelineResult that aggregates all outputs

The graph topology is:

    intake → [transcription] → summarization → quality_scoring → end
                  ↑ (audio only)
"""

import logging
import os
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from agents.intake_agent import CallRecord, IntakeAgent
from agents.transcription_agent import TranscriptionAgent, TranscriptionResult
from agents.summarization_agent import CallSummary, SummarizationAgent
from agents.quality_score_agent import QualityScores, QualityScoringAgent

logger = logging.getLogger(__name__)


class PipelineResult(BaseModel):
    """Aggregated output from a full pipeline run."""

    call_id: str = Field(default="unknown")
    call_record: Optional[CallRecord] = Field(default=None)
    transcription: Optional[TranscriptionResult] = Field(default=None)
    summary: Optional[CallSummary] = Field(default=None)
    quality_scores: Optional[QualityScores] = Field(default=None)
    final_transcript: str = Field(default="")
    success: bool = Field(default=True)
    errors: list[str] = Field(default_factory=list)


class RoutingAgent:
    """
    Orchestrates all agents in a sequential, fault-tolerant pipeline.

    The routing logic:
      1. Run the Intake Agent to validate and normalise the input.
      2. If the input is audio, run the Transcription Agent.
      3. If transcription fails, record the error and stop (no transcript
         available for downstream agents).
      4. Run the Summarisation Agent on the transcript.
      5. Run the Quality Scoring Agent on the same transcript.
      6. Return a PipelineResult aggregating all outputs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        summarization_model: str = "gpt-4o",
        scoring_model: str = "gpt-4o",
        fallback_model: str = "gpt-3.5-turbo",
        max_retries: int = 1,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.max_retries = max_retries

        self.intake_agent = IntakeAgent()
        self.transcription_agent = TranscriptionAgent(
            api_key=self.api_key,
        )
        self.summarization_agent = SummarizationAgent(
            api_key=self.api_key,
            model=summarization_model,
            fallback_model=fallback_model,
        )
        self.quality_agent = QualityScoringAgent(
            api_key=self.api_key,
            model=scoring_model,
            fallback_model=fallback_model,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, input_data: Any, call_id: Optional[str] = None) -> PipelineResult:
        """
        Execute the full pipeline for a given input.

        Args:
            input_data: Audio file path, transcript file path, raw text, or dict.
            call_id:    Optional call identifier.

        Returns:
            PipelineResult with all agent outputs.
        """
        errors: list[str] = []

        # ── Step 1: Intake ───────────────────────────────────────────
        call_record = self.intake_agent.process(input_data, call_id=call_id)
        if not call_record.is_valid:
            return PipelineResult(
                call_id=call_record.call_id,
                call_record=call_record,
                success=False,
                errors=call_record.validation_errors,
            )

        # ── Step 2: Transcription (audio inputs only) ────────────────
        transcription: Optional[TranscriptionResult] = None
        if call_record.input_type == "audio":
            transcription = self._run_with_retry(
                lambda: self.transcription_agent.transcribe(
                    call_record.audio_path, call_id=call_record.call_id
                )
            )
            if not transcription.success:
                errors.append(f"Transcription failed: {transcription.error}")
                return PipelineResult(
                    call_id=call_record.call_id,
                    call_record=call_record,
                    transcription=transcription,
                    success=False,
                    errors=errors,
                )

        # ── Step 3: Resolve the working transcript ───────────────────
        if call_record.input_type == "audio" and transcription:
            final_transcript = transcription.transcript
        else:
            final_transcript = call_record.raw_transcript

        if not final_transcript.strip():
            errors.append("No transcript available for analysis.")
            return PipelineResult(
                call_id=call_record.call_id,
                call_record=call_record,
                transcription=transcription,
                success=False,
                errors=errors,
            )

        # ── Step 4: Summarization ────────────────────────────────────
        summary = self._run_with_retry(
            lambda: self.summarization_agent.summarize(
                final_transcript, call_id=call_record.call_id
            )
        )
        if summary is None:
            from agents.summarization_agent import CallSummary
            summary = CallSummary(
                call_id=call_record.call_id,
                success=False,
                error="Summarization failed: all retries raised exceptions",
            )
        if not summary.success:
            errors.append(f"Summarization failed: {summary.error}")

        # ── Step 5: Quality Scoring ──────────────────────────────────
        quality_scores = self._run_with_retry(
            lambda: self.quality_agent.score(
                final_transcript, call_id=call_record.call_id
            )
        )
        if quality_scores is None:
            from agents.quality_score_agent import QualityScores
            quality_scores = QualityScores(
                call_id=call_record.call_id,
                success=False,
                error="Quality scoring failed: all retries raised exceptions",
            )
        if not quality_scores.success:
            errors.append(f"Quality scoring failed: {quality_scores.error}")

        overall_success = len(errors) == 0

        return PipelineResult(
            call_id=call_record.call_id,
            call_record=call_record,
            transcription=transcription,
            summary=summary,
            quality_scores=quality_scores,
            final_transcript=final_transcript,
            success=overall_success,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run_with_retry(self, fn: Any) -> Any:
        """Run fn up to max_retries+1 times, returning the last result."""
        result = None
        for attempt in range(self.max_retries + 1):
            try:
                result = fn()
                if getattr(result, "success", True):
                    return result
            except Exception as exc:  # noqa: BLE001
                logger.warning("Attempt %d failed: %s", attempt + 1, exc)
        return result
