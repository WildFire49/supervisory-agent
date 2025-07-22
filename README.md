# Supervisory Agent & MCP Server

This project implements a sophisticated supervisory agent that uses LangGraph to manage and execute complex, dynamic workflows. It communicates with a dedicated MCP (Model-Context-Protocol) server to leverage external tools and also integrates with other standalone services.

## Project Structure

- **`app/`**: Main application directory for the Supervisory Agent.
  - `main.py`: FastAPI entry point with the `/chat` endpoint.
  - `agents/`:
    - `supervisor.py`: The main LangGraph-based supervisory agent.
    - `mcp_client.py`: Client for the MCP server, built using the official `mcp-client` library.
  - `clients/`:
    - `external_services.py`: A dedicated client for non-MCP services.
  - `core/`:
    - `config.py`: Manages environment variables and settings.
  - `workflows/`: JSON definitions for conversational workflows.
- **`mcp_server.py`**: A standalone FastAPI and FastMCP server that exposes tools.
- **`requirements.txt`**: Python dependencies.
- **`.env`**: File for storing environment variables.
- **`README.md`**: This file.

## How It Works: Data Flow

The system has two main applications: the **Supervisory Agent** and the **MCP Server**.

1.  **User Request**: A user sends a message (e.g., "What's the weather in London?") to the Supervisory Agent's `/chat` endpoint.

2.  **Supervisor Agent (`supervisor.py`)**: The agent's router analyzes the user's intent and decides which tool to use. It knows about internal functions, tools from the MCP server, and external services.

3.  **Client Routing**:

    - If the required tool is on the MCP Server (like `get_weather`), the supervisor calls the `MCPClient`.
    - If the tool is an external service (like `dashboard_agent`), it calls the `ExternalServicesClient`.

4.  **MCP Client & Server**:

    - The `MCPClient` sends a request to the `mcp_server.py`.
    - The server authenticates the request, executes the `get_weather` function (which in turn calls the OpenWeather API), and returns the result.

5.  **Final Response**: The result travels back through the client to the supervisor, which formats a final answer and sends it to the user.

## Setup and Running the Project

### 1. Environment Setup

- **Install Dependencies**:
  ```bash
  pip install -r requirements.txt
  ```
- **Create `.env` file**: Copy the required variables from `app/core/config.py` into a `.env` file and provide the necessary values (e.g., API keys).

### 2. Running the Servers

The agent and server must run in separate terminals.

- **Terminal 1: Start the MCP Server**:

  ```bash
  python mcp_server.py
  ```

  This will run on `http://localhost:8001` by default.

- **Terminal 2: Start the Supervisory Agent**:
  ```bash
  uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
  The agent will be available at `http://localhost:8000`.

### 3. Test the Setup

Send a request to the agent's chat endpoint:

```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"user_id": "test-user", "message": "What is the weather in London?"}'
```
