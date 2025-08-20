# a2a_client_tool.py
import httpx
import asyncio
from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, SendMessageSuccessResponse, Task

LANGCHAIN_AGENT_URL = "http://localhost:10000"

async def invoke_currency_specialist(query: str) -> str:
    """
    Invokes the external LangChain currency agent via the A2A protocol to answer currency conversion questions.
    Args:
        query (str): The specific currency question to ask the specialist agent.
    Returns:
        str: The answer from the specialist agent.
    """
    print(f"--- Tool: Invoking A2A Specialist with query: {query} ---")
    try:
        async with httpx.AsyncClient(timeout=60.0) as httpx_client:
            # Discover and connect to the agent via its Agent Card [cite: 5236]
            client = await A2AClient.get_client_from_agent_card_url(httpx_client, LANGCHAIN_AGENT_URL)
            
            payload = {"message": {"role": "user", "parts": [{"kind": "text", "text": query}]}}
            request = SendMessageRequest(params=MessageSendParams(**payload))
            
            # Send the message using the A2A protocol [cite: 7550]
            response = await client.send_message(request)
            
            if isinstance(response.root, SendMessageSuccessResponse) and isinstance(response.root.result, Task):
                task_result = response.root.result
                if task_result.artifacts and task_result.artifacts[0].root.text:
                    return task_result.artifacts[0].root.text
                elif task_result.status.message and task_result.status.message.parts[0].root.text:
                    return task_result.status.message.parts[0].root.text

            return f"Error: Could not get a valid response from the specialist agent. Response: {response}"

    except httpx.ConnectError:
        return "Error: Could not connect to the LangChain specialist agent. Is the server running?"
    except Exception as e:
        return f"An unexpected error occurred: {e}"