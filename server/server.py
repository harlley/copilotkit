"""
This serves the "agent" agent using CopilotKit's LangGraph integration.
POC version - standalone Python server.
"""

import os
from dotenv import load_dotenv
load_dotenv() # pylint: disable=wrong-import-position

from fastapi import FastAPI
import uvicorn
from copilotkit import LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from agent import graph

app = FastAPI()

# Configure the agent endpoint
add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="agent",
        description="A helpful assistant that can change colors and get weather information.",
        graph=graph,
    ),
    path="/api/copilotkit",
)

# Add health check endpoint
@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}

def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", 8000))  # Porta diferente para o BFF
    print(f"🐍 Python LangGraph agent starting on port {port}")
    print(f"📡 Endpoint: http://localhost:{port}/api/copilotkit")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
