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

    system_content = f"You are a helpful assistant. Talk in {state.get('language', 'english')}. "

    if frontend_tools:
        tool_descriptions = []
        for tool in frontend_tools:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "No description")
            tool_descriptions.append(f"- {name}: {desc}")

        system_content += (
            "\n\nYou have access to the following UI control tools:\n"
            + "\n".join(tool_descriptions)
            + "\n\nUse these tools proactively when the user asks to change or interact with the interface."
        )

    if frontend_data:
        data_descriptions = []
        for data in frontend_data:
            desc = getattr(data, "description", "unknown data")
            value = getattr(data, "value", "N/A")
            data_descriptions.append(f"- {desc}: {value}")

        system_content += (
            "\n\nCurrent frontend state:\n"
            + "\n".join(data_descriptions)
            + "\n\nUse this information to answer questions about the current state of the interface."
        )

    system_message = SystemMessage(content=system_content)

    if all_tools:
        model_with_tools = model.bind_tools(
            all_tools,
            parallel_tool_calls=False,
        )
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
