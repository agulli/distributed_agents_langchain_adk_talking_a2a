# currency_agent_langchain.py
import os
import httpx
import json
from typing import Any, Dict, List, AsyncGenerator
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

# Ensure the GOOGLE_API_KEY is available in your environment
# from dotenv import load_dotenv
# load_dotenv()

@tool
def get_exchange_rate(
    currency_from: str, currency_to: str, currency_date: str = "latest"
) -> dict:
    """Use this to get the current exchange rate between two currencies."""
    try:
        response = httpx.get(
            f"https://api.frankfurter.app/{currency_date}",
            params={"from": currency_from, "to": currency_to},
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        return {"error": f"API request failed: {e}"}

class CurrencyAgent:
    """A LangGraph-powered agent for currency conversion."""
    SUPPORTED_CONTENT_TYPES = ["text/plain"]

    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
        self.tools = [get_exchange_rate]
        # The agent graph is the executable component [cite: 1997]
        self.graph = create_react_agent(self.model, tools=self.tools)

    def invoke(self, query: str, session_id: str) -> dict[str, Any]:
        """Handles a single, non-streaming request."""
        inputs = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": session_id}}
        
        response_generator = self.graph.stream(inputs, config)
        
        final_response = {}
        for chunk in response_generator:
            message = chunk["messages"][-1]
            if isinstance(message, AIMessage) and not message.tool_calls:
                 final_response = {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": message.content
                 }
        return final_response

    async def stream(self, query: str, session_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """Handles a streaming request, yielding intermediate steps."""
        inputs = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": session_id}}

        async for chunk in self.graph.astream(inputs, config):
            message = chunk["messages"][-1]
            
            if isinstance(message, AIMessage):
                if message.tool_calls:
                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": f"Checking exchange rates for {message.tool_calls[0]['args']}...",
                    }
                else:
                    yield {
                        "is_task_complete": True,
                        "require_user_input": False,
                        "content": message.content,
                    }
            elif isinstance(message, ToolMessage):
                 yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing the exchange rates...",
                 }