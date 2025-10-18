# agent.py Explanation - CopilotKit + LangGraph

This document explains how the integration between CopilotKit (frontend) and LangGraph (backend) works in the `agent.py` file.

## 📦 Imports and Dependencies

### Basic Imports

```python
import os
from typing import Any, Literal
```

- `os`: Access to environment variables
- `typing`: Type hints for better code quality

### CopilotKit

```python
from copilotkit import CopilotKitState
from copilotkit.langchain import copilotkit_customize_config, copilotkit_emit_state
```

- **CopilotKitState**: Base state that includes:
  - Conversation messages
  - Frontend context (`useCopilotReadable`)
  - Frontend actions (`useCopilotAction`)
- **copilotkit_customize_config**: Configures what to send to the frontend in real-time
- **copilotkit_emit_state**: Sends state updates to the frontend

### LangChain

```python
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
```

- **SystemMessage**: System message to instruct the LLM's behavior
- **RunnableConfig**: Agent execution configuration
- **ChatOpenAI**: Client to communicate with GPT-4

### LangGraph

```python
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
```

- **StateGraph**: Orchestrates the agent's flow in a state graph
- **ToolNode**: Specialized node to execute tools
- **Command**: Controls transitions between graph nodes

---

## 🏗️ State Structure

```python
class AgentState(CopilotKitState):
    pass
```

`AgentState` inherits everything from `CopilotKitState`, which automatically includes:

- **messages**: Conversation history
- **copilotkit.context**: Data from `useCopilotReadable` (e.g., current color)
- **copilotkit.actions**: Tools from `useCopilotAction` (e.g., setSquareColor)

```python
tools: list[Any] = []
```

List of backend-defined tools (empty in our case - we only use frontend tools).

---

## 🧠 Main Function: chat_node

This function runs **on every message sent by the user**.

### 1. CopilotKit Configuration (lines 22-31)

```python
config = copilotkit_customize_config(
    config,
    emit_intermediate_state=[
        {
            "state_key": "messages",
            "tool": "all",
            "tool_argument": "all",
        }
    ],
)
```

**What it does:**

- Configures to send **intermediate states** to the frontend
- Allows the frontend to see progress in real-time
- Sends all messages, tools, and arguments during execution

### 2. Extracting Frontend Data (lines 33-37)

```python
copilotkit_state = state.get("copilotkit", {})
frontend_tools = copilotkit_state.get("actions", [])  # useCopilotAction
frontend_data = copilotkit_state.get("context", [])   # useCopilotReadable

all_tools = tools + frontend_tools
```

**What it does:**

- **frontend_tools**: Extracts "actions" defined with `useCopilotAction` in the frontend
  - Example: `setSquareColor` to change the square's color
- **frontend_data**: Extracts "context" defined with `useCopilotReadable`
  - Example: current square color
- **all_tools**: Combines backend + frontend tools

**Data flow:**

```
Frontend (React)                    Backend (Python)
─────────────────                   ────────────────
useCopilotAction({                 frontend_tools = [
  name: "setSquareColor"      →      { name: "setSquareColor", ... }
})                                 ]

useCopilotReadable({               frontend_data = [
  description: "Current color" →     { description: "...", value: "red" }
  value: color                     ]
})
```

### 3. GPT-4 Model Configuration (lines 39-42)

```python
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
)
```

**Parameters:**

- **model**: GPT-4o (optimized version of GPT-4)
- **temperature**: 0.7 (balance between creativity and consistency)
  - 0.0 = Very deterministic
  - 1.0 = Very creative/random
  - 0.7 = Good balance

### 4. 🎯 CRITICAL PART: System Message Construction (lines 44-67)

This is the **solution to the stale state bug**!

#### Extracting Current State (lines 47-57)

```python
current_state = ""
if frontend_data:
    for data in frontend_data:
        value = data.get("value") if isinstance(data, dict) else getattr(data, "value", None)
        desc = (
            data.get("description")
            if isinstance(data, dict)
            else getattr(data, "description", "")
        )
        if value:
            current_state += f"{desc}: {value}\n"
```

**What it does:**

- Iterates over all data from `useCopilotReadable`
- Extracts current value (e.g., "red")
- Extracts description (e.g., "The current color of the square")
- Supports both dict and object formats
- Builds string: `"The current color of the square: red\n"`

#### Strong LLM Instruction (lines 59-65)

```python
if current_state:
    system_content += (
        f"CRITICAL INSTRUCTION: The CURRENT REAL-TIME state is:\n{current_state}\n"
        "You MUST use ONLY this current state when answering questions about the interface. "
        "IGNORE any previous color values mentioned earlier in the conversation. "
        "The state shown above is the ONLY truth. Always answer based on this current state."
    )
```

**Why is this necessary?**

Without this strong instruction, the LLM trusts its **conversation memory**:

```
Problematic scenario (WITHOUT the instruction):
1. LLM changes color to green → Memory: "I changed it to green"
2. User clicks Red button → React state: "red"
3. User asks "what's the color?" → LLM answers "green" ❌ (uses memory)
```

With the strong instruction:

```
Correct scenario (WITH the instruction):
1. LLM changes color to green → Memory: "I changed it to green"
2. User clicks Red button → React state: "red"
3. System Message: "IGNORE previous values, use red"
4. User asks "what's the color?" → LLM answers "red" ✅ (uses current state)
```

**Example of final System Message:**

```
You are a helpful assistant.

CRITICAL INSTRUCTION: The CURRENT REAL-TIME state is:
The current color of the square: red

You MUST use ONLY this current state when answering questions about the interface.
IGNORE any previous color values mentioned earlier in the conversation.
The state shown above is the ONLY truth. Always answer based on this current state.
```

### 5. Model Invocation (lines 69-74)

```python
if all_tools:
    model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)
else:
    model_with_tools = model

response = await model_with_tools.ainvoke([system_message, *state["messages"]], config)
```

**What it does:**

1. Binds tools (actions) to the GPT-4 model
2. `parallel_tool_calls=False`: Executes one tool at a time (not in parallel)
3. Sends to GPT-4:
   - **system_message**: Instructions + current state
   - **state["messages"]**: Complete conversation history
4. Awaits GPT-4 response

**Structure of messages sent:**

```python
[
    SystemMessage("You are a helpful assistant... CURRENT STATE: red"),
    HumanMessage("Change to green"),
    AIMessage("I'll change it to green"),
    # ... tool is executed ...
    HumanMessage("What is the color?"),  # ← current question
]
```

### 6. Finalization (lines 76-78)

```python
await copilotkit_emit_state(config, state)

return Command(goto="__end__", update={"messages": response})
```

**What it does:**

- **copilotkit_emit_state**: Sends updated state to the frontend
- **Command**: Instructs the graph to:
  - `goto="__end__"`: Finish execution
  - `update={"messages": response}`: Add LLM response to history

---

## 🔄 LangGraph Workflow Configuration (lines 81-88)

```python
workflow = StateGraph(AgentState)
workflow.add_node("chat_node", chat_node)

if tools:
    workflow.add_node("tool_node", ToolNode(tools=tools))
    workflow.add_edge("tool_node", "chat_node")

workflow.set_entry_point("chat_node")
```

**Graph structure:**

If there are no backend tools:

```
[START] → [chat_node] → [END]
```

If there are backend tools:

```
[START] → [chat_node] → [tool_node] → [chat_node] → [END]
                ↑______________|
```

**Our case (no backend tools):**

- Only `chat_node`
- Simple flow: receives message → processes → returns response

---

## 💾 Compilation with Memory (lines 90-101)

```python
is_langgraph_api = os.environ.get("LANGGRAPH_API_DIR") is not None
langgraph_api_env = os.environ.get("LANGGRAPH_API", None)
if langgraph_api_env is not None:
    is_langgraph_api = langgraph_api_env.lower() == "true"

if is_langgraph_api:
    graph = workflow.compile()
else:
    from langgraph.checkpoint.memory import MemorySaver
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
```

**What it does:**

- Detects if running in LangGraph Cloud API mode
- **MemorySaver**: Saves conversation history in RAM
  - Maintains context between messages
  - **Required** for CopilotKit to work
  - Without it: `ValueError: No checkpointer set`

**Why doesn't memory cause problems?**

- Memory stores conversation history
- But the "IGNORE previous values" instruction in the system message overrides it
- The LLM prioritizes the current system message over memory

---

## 🎯 Complete Flow of a Message

### Example: User asks "What is the color?"

```
1. Frontend (React)
   └─→ useCopilotReadable detects color = "red"
   └─→ Sends to backend: { context: [{ value: "red", ... }] }

2. Backend (Python - chat_node)
   └─→ Receives state with context
   └─→ Extracts: current_state = "The current color of the square: red"
   └─→ Creates system message with CRITICAL INSTRUCTION
   └─→ Sends to GPT-4: [system_message, history, "What is the color?"]

3. GPT-4
   └─→ Reads system message: "use ONLY current state... red"
   └─→ Ignores memory (which may say "green")
   └─→ Responds: "The current color is red"

4. Backend
   └─→ Receives GPT-4 response
   └─→ Adds to history
   └─→ Sends to frontend

5. Frontend
   └─→ Displays response in chat: "The current color is red" ✅
```

---

## 🔑 Key Concepts

### 1. **Frontend/Backend Separation**

- **Frontend**: UI, React state, tool definitions
- **Backend**: LLM, business logic, orchestration

### 2. **Bidirectional Flow**

```
Frontend → Backend: Context (state) + Actions (tools)
Backend → Frontend: Responses + State updates
```

### 3. **Prompt Engineering**

The bug fix **wasn't code**, it was **clear instructions** to the LLM:

- "CRITICAL INSTRUCTION"
- "You MUST use ONLY"
- "IGNORE any previous"
- "The state shown above is the ONLY truth"

### 4. **Checkpointing (Memory)**

- Required to maintain conversation context
- Automatically managed by LangGraph
- Doesn't interfere with real-time state due to strong instructions

---

## 📝 Debugging Checklist

If the LLM isn't using current state:

1. ✅ Check if `useCopilotReadable` is being called
2. ✅ Check if `frontend_data` is reaching the backend (add print)
3. ✅ Check if `current_state` is being extracted correctly
4. ✅ Check if system message contains "CRITICAL INSTRUCTION"
5. ✅ Strengthen system message instructions if needed

---

## 🚀 Possible Improvements

### 1. **System Message Caching**

```python
# Avoid rebuilding every time if state hasn't changed
if current_state == previous_state:
    use_cached_system_message()
```

### 2. **State Validation**

```python
if not frontend_data:
    logger.warning("No frontend data received!")
```

### 3. **Stronger Typing**

```python
from typing import TypedDict

class FrontendData(TypedDict):
    description: str
    value: str
```

### 4. **Structured Logging**

```python
import logging

logger.info("Processing state", extra={
    "current_state": current_state,
    "num_tools": len(all_tools)
})
```

---

## 📚 References

- [CopilotKit Docs](https://docs.copilotkit.ai/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangChain Docs](https://python.langchain.com/)
- [OpenAI API Docs](https://platform.openai.com/docs/)

---

**Last updated:** 2025-10-18
