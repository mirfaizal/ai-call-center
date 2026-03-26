import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MCPRouter:
    """
    A unified router for invoking language models via LangChain,
    replacing agent-specific _call_llm methods.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key

    def invoke(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, max_tokens: int = 1000) -> Optional[str]:
        """
        Invoke the LLM with a list of message dicts.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

            llm = ChatOpenAI(
                api_key=self.api_key,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            lc_messages = []
            for m in messages:
                role = m.get("role")
                content = m.get("content")
                if role == "user":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                else:
                    # Default to human message for unknown roles
                    lc_messages.append(HumanMessage(content=content))
                    
            response = llm.invoke(lc_messages)
            return response.content
        except Exception as e:
            logger.error(f"MCPRouter.invoke failed: {e}")
            return None
