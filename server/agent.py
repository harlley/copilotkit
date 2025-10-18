import os
from typing import Any, Literal

from copilotkit import CopilotKitState
from copilotkit.langchain import copilotkit_customize_config, copilotkit_emit_state
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command


class AgentState(CopilotKitState):
    pass


tools: list[Any] = []


async def chat_node(state: AgentState, config: RunnableConfig) -> Command[Literal["__end__"]]:
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

    copilotkit_state = state.get("copilotkit", {})
    frontend_tools = copilotkit_state.get("actions", [])
    frontend_data = copilotkit_state.get("context", [])

    all_tools = tools + frontend_tools

    model = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
    )

    # Build current state info
    current_state = ""
    for data in frontend_data:
        value = data.get("value") if isinstance(data, dict) else getattr(data, "value", None)
        desc = data.get("description") if isinstance(data, dict) else getattr(data, "description", "")
        if value:
            current_state += f"{desc}: {value}\n"

    # Build system message with clear instructions
    system_message = SystemMessage(content=f"""You help users change and read the color of a square.

===== CURRENT STATE (ALWAYS USE THIS) =====
{current_state}
============================================

CRITICAL: The value above is the ONLY source of truth. Ignore any different colors mentioned in chat history.

RULES:
1. When asked about the color: Answer ONLY using the CURRENT STATE above
2. When asked to choose/change a color: Use setSquareColor tool ONCE, then confirm
3. After you already responded to a request, do NOT repeat the action
4. IMPORTANT: Always use English HTML color names (e.g., "red", "blue", "green", "yellow", "purple", "orange", "pink", "brown", "black", "white") when calling setSquareColor, even if the user requests the color in another language (e.g., "azul" → "blue", "vermelho" → "red", "verde" → "green")""")

    # Check if last message is a tool result (meaning we just executed a tool)
    last_message = state["messages"][-1] if state.get("messages") else None
    just_executed_tool = last_message and hasattr(last_message, 'type') and last_message.type == 'tool'

    # If we just executed a tool, add instruction to respond to user
    modified_system_content = system_message.content
    if just_executed_tool:
        modified_system_content += "\n\nIMPORTANT: A tool was just executed. Now respond to the user confirming the action. Do NOT call the tool again."

    # Add current state as a reminder at the end to override any conflicting info in history
    state_reminder = SystemMessage(content=f"[REAL-TIME UPDATE] {current_state}This is the ACTUAL current state RIGHT NOW. Use this value, not what you said before.")

    messages_to_send = [SystemMessage(content=modified_system_content), *state["messages"], state_reminder]

    if all_tools:
        model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)
    else:
        model_with_tools = model

    response = await model_with_tools.ainvoke(messages_to_send, config)

    await copilotkit_emit_state(config, state)

    # If response has tool_calls, return it and let CopilotKit handle tool execution
    # CopilotKit will call us again after executing the tool
    return Command(goto="__end__", update={"messages": response})


workflow = StateGraph(AgentState)
workflow.add_node("chat_node", chat_node)

if tools:
    workflow.add_node("tool_node", ToolNode(tools=tools))
    workflow.add_edge("tool_node", "chat_node")

workflow.set_entry_point("chat_node")

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
