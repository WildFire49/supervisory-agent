# Supervisory Agent & MCP Server

This project implements a sophisticated supervisory agent that uses LangGraph to manage and execute complex, dynamic workflows. It communicates with a dedicated MCP (Model Context Protocol) server to leverage external tools and also integrates with other standalone services. The system is designed for scalability and dynamic adaptation, allowing the agent to discover and use new tools from the MCP server without requiring code changes.

## Core Components and Logic

The system is composed of two main applications: the **Supervisory Agent** and the **MCP Server**.

### 1. Supervisory Agent (`app/`)

The agent is the primary entry point for user requests and is responsible for orchestrating tasks.

#### Key Modules:

-   **`main.py`**: The FastAPI entry point that exposes the `/chat` and `/conversations` endpoints. It handles incoming user requests, manages conversation history, and invokes the supervisory agent.

-   **`agents/supervisor.py`**: This is the brain of the system, built with LangGraph. It defines a stateful graph that routes user queries to the appropriate node for execution.
    -   **AgentState**: A `TypedDict` that maintains the state of the conversation, including user query, chat history, and intermediate results.
    -   **Router Node**: The entry point of the graph. It uses an LLM to analyze the user's intent and decides which tool or workflow to execute. It dynamically constructs a prompt with a list of all available tools (internal, external, and from the MCP server).
    -   **Execution Nodes**: The graph contains specialized nodes for different tasks:
        -   `workflow_execution_node`: Executes predefined, step-by-step conversational workflows.
        -   `mcp_tool_node` & `mcp_tool_direct_node`: Invoke tools on the MCP server via the `MCPClient`.
        -   `dashboard_agent_node`, `credit_analysis_node`, `rule_saver_node`: Call external, non-MCP services via the `ExternalServicesClient`.
        -   `workflow_modification_node`: Modifies existing workflows based on user instructions.
        -   `general_qa_node`: Answers general questions using a RAG (Retrieval-Augmented Generation) pipeline with a ChromaDB vector store.

-   **`agents/mcp_client.py`**: A custom HTTP client that communicates with the MCP server following MCP principles.
    -   **Dynamic Tool Discovery**: On initialization, the client connects to the MCP server's `/openapi.json` endpoint to discover all available tools.
    -   **Schema Parsing**: It parses the OpenAPI schema to understand each tool's path, HTTP method (GET/POST), and parameter requirements (including data types and whether they are required).
    -   **Tool Invocation**: It constructs and sends the correct HTTP request to the MCP server to execute a tool, including handling API key authentication and formatting parameters for either query strings (GET) or a JSON body (POST).
    -   **Caching**: Discovered tools are cached to improve performance, with a mechanism to refresh the cache if needed.

-   **`clients/external_services.py`**: A dedicated client for handling API calls to external, non-MCP services like the dashboard agent, credit analysis, and rule saver. This ensures a clean separation of concerns.

-   **`core/config.py`**: Manages all configuration and secrets (like API keys and service URLs) using `pydantic-settings`. It loads these values from a `.env` file, ensuring that no sensitive information is hardcoded.

-   **`core/database.py`**: Manages the PostgreSQL database connection using SQLAlchemy. It handles the creation and retrieval of conversation history and workflow schemas.

### 2. MCP Server (`mcp_server.py`)

A standalone server that exposes tools over an HTTP API, following MCP principles.

-   **Technology**: Built with `FastAPI` and `FastMCP`.
-   **Tool Exposure**: Any function decorated with `@app.get(...)` or `@app.post(...)` is automatically exposed as an MCP tool.
-   **Dynamic OpenAPI Schema**: The server automatically generates an `/openapi.json` schema that describes all available tools, their endpoints, parameters, and data types. This is the foundation for the client's dynamic discovery process.
-   **Authentication**: It uses FastAPI's dependency injection system to protect endpoints with API key authentication.

## Data Flow and Communication

1.  **Initialization**: When the Supervisory Agent starts, the `MCPClient` connects to the MCP Server, fetches the `/openapi.json` schema, and builds a local cache of available tools.
2.  **User Request**: A user sends a message to the agent's `/chat` endpoint.
3.  **Intent Routing**: The `supervisor` agent's router node analyzes the user's query and the list of available tools (from its internal list, external services, and the MCP client's cache) to decide which action to take.
4.  **Tool Invocation**: 
    - If an MCP tool is chosen, the `MCPClient` constructs the appropriate HTTP request (GET or POST) based on the cached tool definition and sends it to the MCP server.
    - If an external service is chosen, the `ExternalServicesClient` makes the API call.
5.  **Execution & Response**: The MCP Server or external service executes the request and returns a JSON response.
6.  **Final Output**: The result is passed back to the `supervisor` agent, which formats a final response for the user.
