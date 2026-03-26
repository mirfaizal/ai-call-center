import pytest
import os
from unittest.mock import patch, MagicMock
from agents.summarization_agent import SummarizationAgent

def test_summarize_empty_transcript():
    agent = SummarizationAgent(api_key="fake")
    res = agent.summarize("")
    assert not res.success
    assert "empty" in res.error.lower()

@patch.dict(os.environ, clear=True)
def test_summarize_no_api_key():
    agent = SummarizationAgent(api_key="")
    res = agent.summarize("test")
    assert not res.success
    assert "not configured" in res.error.lower()

@patch("utils.mcp_router.MCPRouter.invoke")
def test_summarize_mcp_returns_none(mock_invoke):
    mock_invoke.return_value = None
    agent = SummarizationAgent(api_key="fake")
    res = agent.summarize("test transcript")
    assert not res.success
    assert "failed" in res.error.lower()

@patch("utils.mcp_router.MCPRouter.invoke")
def test_summarize_success(mock_invoke):
    mock_invoke.return_value = '{"summary": "test", "key_points": ["a"], "customer_sentiment": "positive", "resolution_status": "resolved"}'
    agent = SummarizationAgent(api_key="fake")
    res = agent.summarize("test transcript")
    assert res.success
    assert res.summary == "test"
    assert "a" in res.key_points

@patch("utils.mcp_router.MCPRouter.invoke")
def test_summarize_parsing_error(mock_invoke):
    mock_invoke.return_value = 'invalid json'
    agent = SummarizationAgent(api_key="fake")
    res = agent.summarize("test transcript")
    assert not res.success
    assert "failed to parse" in res.error.lower()
