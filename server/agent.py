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

    # Build system message with emphasis on current state
    system_content = "You are a helpful assistant.\n\n"

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

    if current_state:
        system_content += (
            f"CRITICAL INSTRUCTION: The CURRENT REAL-TIME state is:\n{current_state}\n"
            "You MUST use ONLY this current state when answering questions about the interface. "
            "IGNORE any previous color values mentioned earlier in the conversation. "
            "The state shown above is the ONLY truth. Always answer based on this current state."
        )

    system_message = SystemMessage(content=system_content)

    if all_tools:
        model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)
    else:
        model_with_tools = model

    response = await model_with_tools.ainvoke([system_message, *state["messages"]], config)

    await copilotkit_emit_state(config, state)

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
