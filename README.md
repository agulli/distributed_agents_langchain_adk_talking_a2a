# Cooperative Multi-Agent System: ADK, LangChain & A2A Protocol

![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue)
![Frameworks](https://img.shields.io/badge/Frameworks-ADK%20%7C%20LangChain-orange)
![Protocol](https://img.shields.io/badge/Protocol-A2A-brightgreen)

This project demonstrates a multi-agent system where two AI agents, built with different modern frameworks, cooperate to solve user queries. Communication between the agents is handled using the standardized **A2A (Agent-to-Agent) Protocol**.

The system consists of:
1.  An **Orchestrator Agent** built with **Google's Agent Development Kit (ADK)**.
2.  A **Specialist Agent** built with **LangChain** and **LangGraph**.

This repository serves as a practical, working example of agent interoperability.

---

## 🏗️ Architecture

The system is designed with a client-server architecture where the ADK agent acts as the orchestrator and the LangChain agent acts as a specialized, callable tool.



```mermaid
sequenceDiagram
    participant User
    participant ADK Orchestrator
    participant Greeting Sub-Agent
    participant LangChain Specialist (A2A Server)
    participant Frankfurter API

    User->>ADK Orchestrator: "Hello! How much is 100 USD in CAD?"
    
    ADK Orchestrator->>Greeting Sub-Agent: Delegates "Hello!"
    Greeting Sub-Agent-->>ADK Orchestrator: "Hello there! ..."
    
    ADK Orchestrator-->>User: "Hello there! How can I help you today?"

    Note over ADK Orchestrator: Processes next part of query. <br/> Decides to use A2A tool.
    
    ADK Orchestrator->>LangChain Specialist (A2A Server): A2A Request: "How much is 100 USD in CAD?"
    
    LangChain Specialist (A2A Server)->>Frankfurter API: GET exchange rate
    Frankfurter API-->>LangChain Specialist (A2A Server): Exchange rate data
    
    LangChain Specialist (A2A Server)-->>ADK Orchestrator: A2A Response: "100 USD is 137.26 CAD"
    
    ADK Orchestrator-->>User: "According to the latest exchange rates, 100 US Dollar is equal to 137.26 Canadian Dollar."

```
---
## 📂 File Structure

The repository is organized into four key files:

-   `langchain_server_main.py`: The entry point for the LangChain specialist agent. It starts the Uvicorn server and exposes the agent via the A2A protocol.
-   `currency_agent_langchain.py`: Contains the core logic for the currency agent, including the LangChain/LangGraph setup and the tool for fetching exchange rates.
-   `adk_orchestrator_main.py`: The entry point for the ADK orchestrator agent. It defines the agent team and runs the example conversation.
-   `a2a_client_tool.py`: A crucial file that defines the ADK `Tool`. This tool acts as an A2A client, enabling the ADK agent to communicate with the LangChain agent.

---

## 🚀 Getting Started

Follow these steps to get the project running.

### Requirements
* Python 3.12+
* A **Google API Key** for the Gemini model. You can get a key from [Google AI Studio](https://a2aprotocol.ai/docs/guide/google-a2a-python-sdk-tutorial).

### Setup and Installation

**1. Clone the Repository**
```bash
git clone [https://github.com/agulli/distributed_agents_langchain_adk_talking_a2a.git](https://github.com/agulli/distributed_agents_langchain_adk_talking_a2a.git)
cd distributed_agents_langchain_adk_talking_a2a
```

**2. Install Dependencies**
Install all the required Python libraries using `pip`.
```bash
pip install google-adk langchain-google-genai langgraph httpx uvicorn click python-dotenv git+[https://github.com/google/a2a-python.git](https://github.com/google/a2a-python.git)
```

**3. Configure Your API Key**
Create a file named `.env` in the root of the project directory and add your Google API key.

```
# .env
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
```

---

## ⚡ Running the System

You will need to run the two agents in **separate terminal windows**.

### Terminal 1: Start the LangChain Specialist Agent (Server)
This command starts the A2A server. It will wait for requests on port 10000.

```bash
python langchain_server_main.py
```

### Terminal 2: Run the ADK Orchestrator Agent (Client)
This command starts the ADK agent, which will kick off the example conversation.

```bash
python adk_orchestrator_main.py
```

---

## 📋 Example Usage

If everything is set up correctly, you will see the following interaction.

**Terminal 1 (LangChain Server) Output:**
The server starts and waits. When the ADK agent calls it, new logs will appear.
```
🚀 Starting LangChain A2A Specialist Agent at http://localhost:10000
📄 Agent Card available at http://localhost:10000/.well-known/agent.json
INFO:     Started server process [53315]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:10000 (Press CTRL+C to quit)

# --- This appears when the ADK agent makes its call ---
INFO:     ::1:xxxxx - "POST / HTTP/1.1" 200 OK
```

**Terminal 2 (ADK Orchestrator) Output:**
The orchestrator runs the conversation, delegating tasks to its internal sub-agent (for "Hello") and the external A2A agent (for the currency query).
```
🤖 ADK Orchestrator is ready. Interacting...


>>> User Query: Hello
<<< Agent Response: Hello there! How can I help you today?


>>> User Query: How much is 100 USD in CAD?
--- Tool: Invoking A2A Specialist with query: How much is 100 USD in CAD? ---
<<< Agent Response: According to the latest exchange rates, 100 US Dollar is equal to 137.26 Canadian Dollar.


>>> User Query: What's the weather like?
<<< Agent Response: I can only handle currency questions and greetings.
```

---

## 🔧 Troubleshooting

* **API Key Error**: If you see a `ValueError: Missing key inputs argument!`, make sure your `.env` file is in the correct directory and is named correctly.
* **Connection Error**: If the ADK agent reports an error connecting to the specialist, ensure the `langchain_server_main.py` script is running in the other terminal and is not blocked by a firewall.
* **Incorrect Agent Response**: The behavior of LLMs can sometimes be non-deterministic. If the ADK agent doesn't delegate correctly or fails to use the tool's output, try making the `instruction` prompt in `adk_orchestrator_main.py` more specific.