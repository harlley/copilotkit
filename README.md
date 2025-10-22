# CopilotKit + LangGraph Integration Study Project

A didactic project demonstrating how to integrate **CopilotKit** (React) with **LangGraph** (Python) to build an AI-powered interface that reads and controls UI state in real-time.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Concepts](#key-concepts)
- [Setup](#setup)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Code Walkthrough](#code-walkthrough)
- [References](#references)

## Overview

This project demonstrates a simple but powerful use case: **an AI agent that can read and change a square's color** through natural language conversation.

**What makes this interesting:**

1. **Bidirectional sync**: Frontend state (React) ↔️ Backend AI (Python)
2. **Real-time updates**: AI always knows the current UI state, even if changed manually
3. **Tool calling**: AI can execute actions in the UI through natural language
4. **State synchronization challenge**: Solved through prompt engineering

### Demo Features

- Change square color via chat (English or other languages)
- Ask about current color - AI always knows the real state
- Manual controls (buttons) - AI stays synchronized
- Multilingual support with automatic translation to HTML color names

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React) - Port 5173               │
│  ┌────────────────────────────────────────────────────┐ │
│  │  useCopilotReadable  ──→  Sends current state      │ │
│  │  - Current color: "blue"                           │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │  useCopilotAction    ──→  Defines tools            │ │
│  │  - setSquareColor(color)                           │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/SSE
                  ↓
┌─────────────────────────────────────────────────────────┐
│           BFF (Express.js) - Port 4000                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │  CopilotRuntime                                    │ │
│  │  - Proxies requests to Python backend              │ │
│  │  - Handles CopilotKit protocol                     │ │
│  │  - Manages tool execution flow                     │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/SSE
                  ↓
┌─────────────────────────────────────────────────────────┐
│          Backend (FastAPI/Python) - Port 8000           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  LangGraph Agent (chat_node)                       │ │
│  │  1. Receives context (current state)               │ │
│  │  2. Receives actions (available tools)             │ │
│  │  3. Builds system message with CURRENT STATE       │ │
│  │  4. Invokes GPT-4o with tools                      │ │
│  │  5. Returns response or tool call                  │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### The BFF Layer (Backend For Frontend)

This project uses a BFF pattern with an Express.js proxy layer:

```typescript
// client/server/index.ts — BFF (Express)
import {
  CopilotRuntime,
  copilotRuntimeNodeHttpEndpoint,
  ExperimentalEmptyAdapter,
  LangGraphHttpAgent,
} from "@copilotkit/runtime";
import express from "express";

const app = express();
const serviceAdapter = new ExperimentalEmptyAdapter();

app.use("/api/copilotkit", (req, res, next) => {
  const runtime = new CopilotRuntime({
    agents: {
      agent: new LangGraphHttpAgent({
        url: "http://localhost:8000/api/copilotkit", // Python backend
      }),
    },
  });

  const handler = copilotRuntimeNodeHttpEndpoint({
    endpoint: "/api/copilotkit",
    runtime,
    serviceAdapter,
  });

  return handler(req, res, next);
});

const PORT = Number(process.env.BFF_PORT || 4000);
app.listen(PORT, () => {
  console.log(`BFF listening on http://localhost:${PORT}/api/copilotkit`);
});
```

**Architecture with BFF:**

```
React Frontend (5173)
    ↓
Express BFF (4000)
    ↓
Python Backend (8000)
```

What the BFF does:

- Acts as a proxy between frontend and Python backend
- Handles CopilotKit Runtime logic (message formatting, tool execution)
- Converts between browser-friendly and LangGraph formats
- Simplifies frontend code — no need to handle LangGraph details directly

Why use a BFF:

- Separation of concerns: frontend does not depend on LangGraph internals
- Type safety: TypeScript on both frontend and BFF
- Flexibility: can add middleware, logging, authentication, etc.
- CORS handling: avoids cross-origin issues by proxying requests

## Key Concepts

### 1. **Frontend to Backend Flow**

**Frontend (React):**

```typescript
// Send current state to AI
useCopilotReadable({
  description: "The current color of the square",
  value: color, // "blue"
});

// Define actions AI can call
useCopilotAction({
  name: "setSquareColor",
  description: "Set the color of the square",
  parameters: [{ name: "color", type: "string" }],
  handler: async ({ color }) => setColor(color),
});
```

**Backend (Python):**

```python
# Receives automatically from CopilotKit
frontend_data = state["copilotkit"]["context"]     # Current state
frontend_tools = state["copilotkit"]["actions"]    # Available actions
```

### 2. **Tool Execution Flow**

CopilotKit automatically handles tool execution:

```
User: "Change to green"
    ↓
Backend: AI decides to call setSquareColor("green")
    ↓
CopilotKit: Intercepts tool call, executes in frontend
    ↓
Frontend: setColor("green") runs
    ↓
Backend: Receives tool result, AI confirms to user
    ↓
AI: "I've set the color to green"
```

## Setup

### Prerequisites

- **Option 1: Docker** (Recommended for quick start)
  - Docker and Docker Compose
  - OpenAI API key

- **Option 2: Local Development**
  - Node.js 18+
  - Python 3.11+
  - OpenAI API key
  - (Optional) LangSmith API key for debugging

### Quick Start with Docker

The easiest way to run all three services (Frontend, BFF, Backend) is using Docker:

1. **Clone the repository**

```bash
git clone <repository-url>
cd copilotkit
```

2. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Build and run with Docker**

```bash
# Build the Docker image
make docker-build

# Run the container
make docker-run
```

4. **Access the application**

Open http://localhost:5173 in your browser.

**Docker ports:**
- Frontend: http://localhost:5173
- BFF API: http://localhost:4000/api/copilotkit
- Backend API: http://localhost:8000/api/copilotkit
- Backend Health: http://localhost:8000/health

**Useful commands:**

```bash
# View logs
docker logs -f copilotkit-demo

# Stop the container
make docker-stop

# Rebuild after changes
make docker-build && make docker-run
```

### Local Development Setup

For local development with auto-reload:

1. **Clone the repository**

```bash
git clone <repository-url>
cd copilotkit
```

2. **Install all dependencies**

```bash
make install
```

This will:
- Install Node.js dependencies for frontend and BFF
- Install Python dependencies using `uv`

3. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

Or create `server/.env` with:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for debugging)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=copilotkit-square
```

4. **Run all services**

```bash
make start
```

This starts:
- Python Backend (FastAPI) on port 8000
- BFF (Express) on port 4000
- Frontend (Vite) on port 5173

Open http://localhost:5173

### Alternative Running Methods

**Option A — Root Makefile (recommended)**

```bash
make start  # Starts all 3 services from root
```

**Option B — Separate terminals**

Terminal 1 - Backend (Python):
```bash
cd server
make start   # or: uv run python server.py
```

Terminal 2 - Frontend + BFF:
```bash
cd client
npm run dev:both   # starts BFF and Vite together
```

**Option C — Individual services**

```bash
# Backend
cd server && make start

# BFF
cd client && npm run bff

# Frontend
cd client && npm run dev
```

### Ports and Environment Variables

**Service Ports:**

| Service | Port | Override Variable |
|---------|------|-------------------|
| Frontend (Vite) | 5173 | N/A |
| BFF (Express) | 4000 | `BFF_PORT` |
| Backend (FastAPI) | 8000 | `PORT` |

**Environment Variables:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | - | OpenAI API key for GPT-4 access |
| `BFF_PORT` | No | 4000 | Express server port |
| `PORT` | No | 8000 | FastAPI server port |
| `LANGCHAIN_TRACING_V2` | No | false | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | No | - | LangSmith API key (for debugging) |
| `LANGCHAIN_PROJECT` | No | - | LangSmith project name |

**Notes:**

- For local development: Place variables in `server/.env` or export them in your shell
- For Docker: Place all variables in root `.env` file (used by Docker)
- `OPENAI_API_KEY` is required for the application to work
- LangSmith variables are optional and used for debugging/monitoring

## Project Structure

```
copilotkit/
├── client/                    # React frontend
│   ├── src/
│   │   ├── App.tsx           # Main component with CopilotKit hooks
│   │   └── App.module.css    # Styles with CSS variables
│   ├── server/
│   │   └── index.ts          # BFF (Backend For Frontend) - Express proxy
│   ├── package.json          # Node.js dependencies
│   └── Makefile              # Build scripts for client
│
├── server/                    # Python backend
│   ├── server.py             # FastAPI server exposing LangGraph
│   ├── agent.py              # LangGraph agent implementation
│   ├── pyproject.toml        # Python dependencies
│   ├── .env                  # Environment variables (create from .env.example)
│   ├── .env.example          # Example environment variables
│   └── Makefile              # Build scripts for server
│
├── Dockerfile                 # Multi-service Docker image
├── docker-entrypoint.sh       # Docker startup script for all services
├── .dockerignore              # Docker build exclusions
├── Makefile                   # Root Makefile - run all services
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## How It Works

### Complete Message Flow

Let's trace what happens when a user asks: **"What is the square color?"**

#### 1. Frontend (React)

```typescript
// Current React state
const [color, setColor] = useState("red");

// Automatically sends to backend
useCopilotReadable({
  description: "The current color of the square",
  value: color, // ← "red"
});
```

CopilotKit sends to backend:

```json
{
  "copilotkit": {
    "context": [
      {
        "description": "The current color of the square",
        "value": "red"
      }
    ]
  }
}
```

#### 2. Backend Receives (`agent.py`)

```python
# Extract frontend data
frontend_data = state["copilotkit"]["context"]

# Build current state string
current_state = "The current color of the square: red\n"

# Create system message
system_message = SystemMessage(content=f"""
===== CURRENT STATE (ALWAYS USE THIS) =====
{current_state}
============================================

CRITICAL: Use ONLY this current state value.
Ignore any different colors mentioned in chat history.
""")
```

#### 3. Send to GPT-4

```python
messages_to_send = [
  system_message,              # Instructions + current state
  *state["messages"],          # Conversation history
  state_reminder               # Current state reminder (injected at end)
]

response = await model.ainvoke(messages_to_send)
```

GPT-4 receives:

```
[SystemMessage] CURRENT STATE: red ...
[HumanMessage] "Change to green"
[AIMessage] "I've set it to green"
[HumanMessage] "What is the square color?"  ← Current question
[SystemMessage] [REAL-TIME UPDATE] Current: red  ← Override!
```

#### 4. GPT-4 Response

Despite having said "green" in memory, GPT-4 sees:

- Strong instruction: "Use ONLY current state"
- Current state: "red"
- Recent reminder: "red"

Response: **"The current color of the square is red"** ✅

#### 5. Backend Returns to Frontend

```python
return Command(goto="__end__", update={"messages": response})
```

#### 6. Frontend Displays

CopilotSidebar shows: "The current color of the square is red"

## Code Walkthrough

### Frontend: `client/src/App.tsx`

#### 1. State Management

```typescript
function Chat() {
  const [color, setColor] = useState("blue");

  // ... rest of component
}
```

#### 2. Readable State (Sends to AI)

```typescript
useCopilotReadable({
  description: "The current color of the square",
  value: color, // AI always gets the current value
});
```

**Key point:** This runs on every render, so AI always sees the latest state.

#### 3. Action Definition (Tool for AI)

```typescript
useCopilotAction({
  name: "setSquareColor",
  description: "Set the color of the square",
  parameters: [
    {
      name: "color",
      type: "string",
      description: "The new color for the square",
    },
  ],
  handler: async ({ color }) => {
    setColor(color); // Actually changes the state
  },
});
```

**Key point:** CopilotKit automatically:

- Sends this tool definition to the backend
- Executes the handler when AI calls it
- Syncs the result back

#### 4. UI Rendering

```typescript
return (
  <>
    <CopilotSidebar
      defaultOpen
      instructions="You help users change and read the color..."
      suggestions={[
        {
          title: "Change square color",
          message: "Choose a new random background color.",
        },
        {
          title: "What is the square color?",
          message: "What is the square color?",
        },
      ]}
    />

    <div className={styles.container}>
      <Square color={color} />

      <div className={styles.buttonContainer}>
        <button onClick={() => setColor("red")}>Red</button>
        <button onClick={() => setColor("blue")}>Blue</button>
        <button onClick={() => setColor("green")}>Green</button>
      </div>
    </div>
  </>
);
```

### Backend: `server/agent.py`

#### 1. State Definition

```python
from copilotkit import CopilotKitState

class AgentState(CopilotKitState):
    pass  # Inherits: messages, copilotkit.context, copilotkit.actions
```

#### 2. Extract Frontend Data

```python
async def chat_node(state: AgentState, config: RunnableConfig):
    # Get data sent from frontend
    copilotkit_state = state.get("copilotkit", {})
    frontend_tools = copilotkit_state.get("actions", [])    # Tools
    frontend_data = copilotkit_state.get("context", [])     # Current state

    all_tools = tools + frontend_tools
```

#### 3. Build Current State String

```python
    # Extract current values from frontend
    current_state = ""
    for data in frontend_data:
        value = data.get("value") if isinstance(data, dict) else getattr(data, "value", None)
        desc = data.get("description") if isinstance(data, dict) else getattr(data, "description", "")
        if value:
            current_state += f"{desc}: {value}\n"
```

#### 4. Create System Message with Current State

```python
    system_message = SystemMessage(content=f"""You help users change and read the color of a square.

===== CURRENT STATE (ALWAYS USE THIS) =====
{current_state}
============================================

CRITICAL: The value above is the ONLY source of truth.
Ignore any different colors mentioned in chat history.

RULES:
1. When asked about the color: Answer ONLY using the CURRENT STATE above
2. When asked to choose/change a color: Use setSquareColor tool ONCE, then confirm
3. After you already responded to a request, do NOT repeat the action
4. IMPORTANT: Always use English HTML color names (e.g., "red", "blue", "green")
   even if the user requests the color in another language (e.g., "azul" → "blue")""")
```

#### 5. Inject Current State at End (Maximum Priority)

```python
    # Add state reminder at the end for highest priority
    state_reminder = SystemMessage(
        content=f"[REAL-TIME UPDATE] {current_state}This is the ACTUAL current state RIGHT NOW. Use this value, not what you said before."
    )

    messages_to_send = [
        SystemMessage(content=modified_system_content),
        *state["messages"],
        state_reminder  # ← Injected at the end!
    ]
```

**Why inject twice (start + end)?**

- LLMs give more weight to recent messages
- System message at start = general instructions
- System message at end = "this is the truth RIGHT NOW"

#### 6. Configure Model and Invoke

```python
    model = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
    )

    # Bind frontend tools to the model
    if all_tools:
        model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)
    else:
        model_with_tools = model

    # Call GPT-4
    response = await model_with_tools.ainvoke(messages_to_send, config)
```

#### 8. Return Response

```python
    await copilotkit_emit_state(config, state)  # Sync to frontend

    return Command(goto="__end__", update={"messages": response})
```

## 🐛 Debugging

### Enable LangSmith Tracing

Add to `server/.env`:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=copilotkit-square
```

Visit https://smith.langchain.com to see:

- Every message sent to/from GPT-4
- Tool calls and responses
- Timing and token usage
- Exact state at each step

## 📚 References

- [CopilotKit Documentation](https://docs.copilotkit.ai/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [LangSmith for Debugging](https://smith.langchain.com/)

## 📄 License

This is a study project for educational purposes.

---

**Last updated:** 2025-10-18

Built with ❤️ to understand CopilotKit Open Source SDK + LangGraph integration
