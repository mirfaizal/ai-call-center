"""
Summarization Agent

Uses LangChain + OpenAI GPT to generate structured summaries of call
transcripts, including key points, action items, and sentiment.
"""

import os
from typing import Any

from pydantic import BaseModel, Field
from utils.validation import extract_json_from_markdown


class CallSummary(BaseModel):
    """Structured summary produced for a single call transcript."""

    call_id: str = Field(default="unknown")
    summary: str = Field(default="", description="Concise narrative summary of the call")
    key_points: list[str] = Field(default_factory=list, description="Main discussion points")
    action_items: list[str] = Field(
        default_factory=list, description="Follow-up actions identified in the call"
    )
    customer_sentiment: str = Field(
        default="neutral", description="Overall customer sentiment: positive/neutral/negative"
    )
    resolution_status: str = Field(
        default="unknown", description="resolved / unresolved / escalated / unknown"
    )
    tags: list[str] = Field(default_factory=list, description="Topic/category tags")
    success: bool = Field(default=True)
    error: str = Field(default="")


_SUMMARY_PROMPT_TEMPLATE = """\
You are an expert call center analyst. Analyze the following call transcript and provide a structured summary.

TRANSCRIPT:
{transcript}

Provide your response as a JSON object with exactly these fields:
{{
  "summary": "<2-3 sentence narrative summary>",
  "key_points": ["<point 1>", "<point 2>", ...],
  "action_items": ["<action 1>", "<action 2>", ...],
  "customer_sentiment": "<positive|neutral|negative>",
  "resolution_status": "<resolved|unresolved|escalated|unknown>",
  "tags": ["<tag1>", "<tag2>", ...]
}}

Return only valid JSON. No additional text.
"""


class SummarizationAgent:
    """
    Generates structured call summaries using LangChain and OpenAI GPT.

    Falls back gracefully when the API key is not available, returning an
    error result instead of raising.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        fallback_model: str = "gpt-3.5-turbo",
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.fallback_model = fallback_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def summarize(self, transcript: str, call_id: str = "unknown") -> CallSummary:
        """
        Summarize a transcript and return a CallSummary.

        Args:
            transcript: Full text of the call transcript.
            call_id:    Identifier used to tag the result.
        """
        if not transcript or not transcript.strip():
            return CallSummary(
                call_id=call_id,
                success=False,
                error="Transcript is empty; nothing to summarize.",
            )

        if not self.api_key:
            return CallSummary(
                call_id=call_id,
                success=False,
                error=(
                    "OpenAI API key not configured. "
                    "Set the OPENAI_API_KEY environment variable."
                ),
            )

        prompt = _SUMMARY_PROMPT_TEMPLATE.format(transcript=transcript)

        result = self._call_llm(prompt, self.model)
        if result is None:
            result = self._call_llm(prompt, self.fallback_model)
        if result is None:
            return CallSummary(
                call_id=call_id,
                success=False,
                error="LLM call failed on both primary and fallback models.",
            )

        try:
            import json

            data = extract_json_from_markdown(result)
            return CallSummary(
                call_id=call_id,
                summary=data.get("summary", ""),
                key_points=data.get("key_points", []),
                action_items=data.get("action_items", []),
                customer_sentiment=data.get("customer_sentiment", "neutral"),
                resolution_status=data.get("resolution_status", "unknown"),
                tags=data.get("tags", []),
                success=True,
            )
        except Exception as exc:  # noqa: BLE001
            return CallSummary(
                call_id=call_id,
                success=False,
                error=f"Failed to parse LLM response as JSON: {exc}. Raw: {result[:200]}",
            )

    def _call_llm(self, prompt: str, model: str) -> str | None:
        """Call the OpenAI chat completion API and return the response text, or None on error."""
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
