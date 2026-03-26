import pytest
from unittest.mock import patch, MagicMock
from utils.mcp_router import MCPRouter

def test_mcp_router_invoke_success():
    router = MCPRouter(api_key="fake-key")
    
    with patch("langchain_openai.ChatOpenAI.invoke") as mock_invoke:
        mock_response = MagicMock()
        mock_response.content = "mocked response"
        mock_invoke.return_value = mock_response
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "unknown", "content": "fallback"}
        ]
        
        result = router.invoke(messages, model="gpt-4o")
        
        assert result == "mocked response"
        assert mock_invoke.call_count == 1
        
        # Verify call arguments
        # The messages should be converted to SystemMessage, HumanMessage, AIMessage, HumanMessage
        called_args = mock_invoke.call_args[0][0]
        assert len(called_args) == 4
        assert called_args[0].content == "You are a helpful assistant."
        assert called_args[1].content == "Hello!"
        assert called_args[2].content == "Hi there!"
        assert called_args[3].content == "fallback"

def test_mcp_router_invoke_exception():
    router = MCPRouter(api_key="fake-key")
    
    with patch("langchain_openai.ChatOpenAI.invoke", side_effect=Exception("API Error")):
        messages = [{"role": "user", "content": "Hello!"}]
        result = router.invoke(messages, model="gpt-4o")
        assert result is None
