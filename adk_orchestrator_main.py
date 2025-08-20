# adk_orchestrator_main.py
import asyncio
from dotenv import load_dotenv
load_dotenv()
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Import the A2A client tool
from a2a_client_tool import invoke_currency_specialist

# --- Define Internal Tools and Sub-Agents ---
def say_hello() -> str:
    """Provides a friendly greeting."""
    return "Hello there! How can I help you today?"

greeting_agent = Agent(
    name="greeting_agent",
    model="gemini-2.0-flash",
    description="Handles simple greetings and hellos.",
    instruction="You are a friendly greeter. Use the say_hello tool.",
    tools=[say_hello],
)

# --- Define the Main Orchestrator Agent ---
orchestrator_agent = Agent(
    name="adk_orchestrator",
    model="gemini-2.0-flash",
    description="The main coordinator. Handles greetings internally and delegates currency questions externally.",
    instruction="You are the main orchestrator agent. Your primary role is to understand user intent. "
                "- If the user asks a currency-related question (e.g., 'how much is', 'convert', 'exchange rate'), "
                "  you MUST use the 'invoke_currency_specialist' tool to get the answer. Pass the user's full currency question to it. "
                "- If the user gives a simple greeting like 'hi' or 'hello', delegate to the 'greeting_agent'. "
                "- For all other topics, state that you can only handle currency questions and greetings.",
    tools=[invoke_currency_specialist], # External communication tool
    sub_agents=[greeting_agent],       # Internal delegation
)

# --- ADK Runner and Interaction Logic ---
async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the ADK agent and prints the final response."""
    print(f"\n>>> User Query: {query}")
    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response."
    
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # --- CHANGE: Corrected the typo from is__final_response to is_final_response ---
        if event.is_final_response() and event.content and event.content.parts:
            final_response_text = event.content.parts[0].text
            break
            
    print(f"<<< Agent Response: {final_response_text}")


async def main():
    """Sets up the ADK runner and runs a conversation."""
    session_service = InMemorySessionService()
    APP_NAME = "cooperative_agents_app"
    
    runner = Runner(
        agent=orchestrator_agent, 
        session_service=session_service,
        app_name=APP_NAME
    )
    
    USER_ID = "user_123"
    SESSION_ID = "session_abc"
    
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

    print("🤖 ADK Orchestrator is ready. Interacting...\n")
    
    await call_agent_async("Hello", runner, USER_ID, SESSION_ID)
    await call_agent_async("How much is 100 USD in CAD?", runner, USER_ID, SESSION_ID)
    await call_agent_async("What's the weather like?", runner, USER_ID, SESSION_ID)


if __name__ == "__main__":
    asyncio.run(main())