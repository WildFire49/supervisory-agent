# Supervisory Agent

This project implements a supervisory agent using FastAPI and LangGraph. The agent is designed to handle conversational workflows, interact with a Model Context Protocol (MCP) server, and execute tasks based on user intent.

## Project Structure

- `app/`: Main application directory.
  - `main.py`: FastAPI application with the `/chat` endpoint.
  - `agent/`: Contains the LangGraph agent logic.
  - `config.py`: Application configuration.
  - `schemas.py`: Pydantic schemas for API requests and responses.
  - `mcp/`: Client for interacting with the MCP server.
  - `workflows/`: Definitions for various conversational workflows.
  - `tools/`: Custom tools for the agent.
- `requirements.txt`: Python dependencies.
- `.env`: Environment variables (e.g., API keys).

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Create a `.env` file and add your configuration (see `app/config.py`).

3.  Run the application:
    ```bash
    uvicorn app.main:app --reload
    ```
