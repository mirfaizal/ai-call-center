import pytest
import os
from unittest.mock import patch
from agents.quality_score_agent import QualityScoringAgent

def test_score_empty_transcript():
    agent = QualityScoringAgent(api_key="fake")
    res = agent.score("")
    assert not res.success
    assert "empty" in res.error.lower()

@patch.dict(os.environ, clear=True)
def test_score_no_api_key():
    agent = QualityScoringAgent(api_key="")
    res = agent.score("test")
    assert not res.success
    assert "not configured" in res.error.lower()

@patch("utils.mcp_router.MCPRouter.invoke")
def test_score_mcp_returns_none(mock_invoke):
    mock_invoke.return_value = None
    agent = QualityScoringAgent(api_key="fake")
    res = agent.score("test transcript")
    assert not res.success
    assert "failed" in res.error.lower()

@patch("utils.mcp_router.MCPRouter.invoke")
def test_score_success(mock_invoke):
    mock_invoke.return_value = '{"empathy_score": 8, "overall_score": 9.5, "strengths": ["good"]}'
    agent = QualityScoringAgent(api_key="fake")
    res = agent.score("test transcript")
    assert res.success
    assert res.empathy_score == 8
    assert res.overall_score == 9.5
    assert "good" in res.strengths

@patch("utils.mcp_router.MCPRouter.invoke")
def test_score_parsing_error(mock_invoke):
    mock_invoke.return_value = 'invalid json'
    agent = QualityScoringAgent(api_key="fake")
    res = agent.score("test transcript")
    assert not res.success
    assert "failed to parse" in res.error.lower()
