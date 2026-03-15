"""
Quality Scoring Agent

Evaluates call quality using structured rubrics with LLM function calling.
Scores are produced as Pydantic models covering empathy, professionalism,
resolution, communication clarity, and overall satisfaction.
"""

import json
import os
from typing import Any

from pydantic import BaseModel, Field


class QualityScores(BaseModel):
    """Numeric and categorical quality scores for a single call."""

    call_id: str = Field(default="unknown")

    # Rubric dimensions – each 1-10
    empathy_score: int = Field(default=0, ge=0, le=10, description="Agent empathy (1-10)")
    professionalism_score: int = Field(
        default=0, ge=0, le=10, description="Agent professionalism (1-10)"
    )
    resolution_score: int = Field(
        default=0, ge=0, le=10, description="Issue resolution effectiveness (1-10)"
    )
    communication_score: int = Field(
        default=0, ge=0, le=10, description="Communication clarity (1-10)"
    )
    overall_score: float = Field(default=0.0, description="Weighted overall score (1-10)")

    # Qualitative feedback
    strengths: list[str] = Field(default_factory=list, description="Notable positive behaviours")
    improvements: list[str] = Field(
        default_factory=list, description="Areas that need improvement"
    )
    compliance_flags: list[str] = Field(
        default_factory=list,
        description="Compliance or policy concerns identified in the call",
    )
    tone_assessment: str = Field(default="neutral", description="Overall tone of the agent")

    success: bool = Field(default=True)
    error: str = Field(default="")


_SCORING_PROMPT_TEMPLATE = """\
You are a senior call center quality assurance analyst. Evaluate the following call transcript using the rubric below.

TRANSCRIPT:
{transcript}

RUBRIC:
- empathy_score (1-10): Does the agent acknowledge the customer's feelings and show genuine care?
- professionalism_score (1-10): Is the agent courteous, composed, and professional throughout?
- resolution_score (1-10): Was the customer's issue fully and effectively resolved?
- communication_score (1-10): Is the agent's language clear, concise, and easy to follow?
- overall_score (1.0-10.0): Weighted average reflecting overall call quality.
- strengths: List up to 3 specific positive behaviours observed.
- improvements: List up to 3 specific areas for improvement.
- compliance_flags: List any compliance or policy concerns (empty list if none).
- tone_assessment: One of "positive", "neutral", "negative", "mixed".

Return your evaluation as a JSON object with exactly these keys. Return only valid JSON.
"""


class QualityScoringAgent:
    """
    Scores call transcripts against a QA rubric using LLM function calling.

    Falls back gracefully when the API key is absent.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        fallback_model: str = "gpt-3.5-turbo",
        temperature: float = 0.1,
        max_tokens: int = 800,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.fallback_model = fallback_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def score(self, transcript: str, call_id: str = "unknown") -> QualityScores:
        """
        Evaluate a transcript and return structured QualityScores.

        Args:
            transcript: Full text of the call transcript.
            call_id:    Identifier used to tag the result.
        """
        if not transcript or not transcript.strip():
            return QualityScores(
                call_id=call_id,
                success=False,
                error="Transcript is empty; cannot score.",
            )

        if not self.api_key:
            return QualityScores(
                call_id=call_id,
                success=False,
                error=(
                    "OpenAI API key not configured. "
                    "Set the OPENAI_API_KEY environment variable."
                ),
            )

        prompt = _SCORING_PROMPT_TEMPLATE.format(transcript=transcript)

        raw = self._call_llm(prompt, self.model)
        if raw is None:
            raw = self._call_llm(prompt, self.fallback_model)
        if raw is None:
            return QualityScores(
                call_id=call_id,
                success=False,
                error="LLM call failed on both primary and fallback models.",
            )

        try:
            data = json.loads(raw)
            return QualityScores(
                call_id=call_id,
                empathy_score=int(data.get("empathy_score", 0)),
                professionalism_score=int(data.get("professionalism_score", 0)),
                resolution_score=int(data.get("resolution_score", 0)),
                communication_score=int(data.get("communication_score", 0)),
                overall_score=float(data.get("overall_score", 0.0)),
                strengths=data.get("strengths", []),
                improvements=data.get("improvements", []),
                compliance_flags=data.get("compliance_flags", []),
                tone_assessment=data.get("tone_assessment", "neutral"),
                success=True,
            )
        except Exception as exc:  # noqa: BLE001
            return QualityScores(
                call_id=call_id,
                success=False,
                error=f"Failed to parse LLM response: {exc}. Raw: {raw[:200]}",
            )

    def _call_llm(self, prompt: str, model: str) -> str | None:
        """Invoke the OpenAI chat API and return the response text, or None on error."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage

            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception:  # noqa: BLE001
            return None
