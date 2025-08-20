# langchain_server_main.py
import click
import uvicorn
from typing import AsyncGenerator
from currency_agent_langchain import CurrencyAgent

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    AgentCard, AgentSkill, AgentCapabilities,
    TaskStatus, TaskState, TaskStatusUpdateEvent, TaskArtifactUpdateEvent
)
from a2a.utils import new_agent_text_message, new_task, new_text_artifact


class CurrencyAgentExecutor(AgentExecutor):
    """Bridges the A2A protocol with the CurrencyAgent's logic."""
    def __init__(self):
        self.agent = CurrencyAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task

        if not task:
            task = new_task(context.message)
            event_queue.enqueue_event(task)

        # Use the agent's streaming capabilities
        async for event in self.agent.stream(query, task.contextId):
            if event["is_task_complete"]:
                event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        append=False,
                        contextId=task.contextId,
                        taskId=task.id,
                        lastChunk=True,
                        artifact=new_text_artifact(
                            name="final_result",
                            description="Final result of the currency conversion.",
                            text=event["content"],
                        ),
                    )
                )
                event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(state=TaskState.completed),
                        final=True,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )
            else:
                 event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        status=TaskStatus(
                            state=TaskState.working,
                            message=new_agent_text_message(event["content"], task.contextId, task.id),
                        ),
                        final=False,
                        contextId=task.contextId,
                        taskId=task.id,
                    )
                )

    # --- ADDED THIS METHOD ---
    # The AgentExecutor base class requires the 'cancel' method to be implemented.
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handles requests to cancel ongoing tasks."""
        # As per the tutorials, if cancellation isn't supported, raise an exception.
        raise Exception("Cancel is not supported by this agent.")
    # -------------------------


def get_agent_card(host: str, port: int) -> AgentCard:
    """Returns the Agent Card for the Currency Agent."""
    skill = AgentSkill(
        id="convert_currency",
        name="Currency Exchange Rates Tool",
        description="Helps with exchange values between various currencies.",
        tags=["currency conversion", "currency exchange"],
        examples=["What is the exchange rate between USD and GBP?"],
    )
    capabilities = AgentCapabilities(streaming=True, pushNotifications=False)
    return AgentCard(
        name="Currency Specialist Agent (LangChain)",
        description="Helps with real-time exchange rates for currencies.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=CurrencyAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=CurrencyAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10000)
def main(host: str, port: int):
    """Starts the A2A server for the LangChain Currency Agent."""
    request_handler = DefaultRequestHandler(
        agent_executor=CurrencyAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server_app = A2AStarletteApplication(
        agent_card=get_agent_card(host, port), 
        http_handler=request_handler
    )
    print(f"🚀 Starting LangChain A2A Specialist Agent at http://{host}:{port}")
    print(f"📄 Agent Card available at http://{host}:{port}/.well-known/agent.json")
    uvicorn.run(server_app.build(), host=host, port=port)

if __name__ == "__main__":
    main()