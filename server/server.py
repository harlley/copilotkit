import os

import uvicorn
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from dotenv import load_dotenv
from fastapi import FastAPI

from agent import graph

load_dotenv()  # Must be called after imports but before using env vars

app = FastAPI()

add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="agent",
        description="A helpful assistant that can change colors and get weather information.",
        graph=graph,
    ),
    path="/api/copilotkit",
)


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", 8000))
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
