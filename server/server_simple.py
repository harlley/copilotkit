"""
Simple CopilotKit Python server that mimics the Node.js CopilotRuntime behavior.
This implementation provides the standard CopilotKit API endpoints without LangGraph.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

load_dotenv()

app = FastAPI()

# Initialize OpenAI model
model = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    streaming=True
)

# Define tools
@tool
def get_weather(location: str) -> str:
    """Get the weather for a given location."""
    return f"The weather for {location} is 70 degrees and sunny."

tools = [get_weather]

# Request/Response models
class Message(BaseModel):
    role: str
    content: str

class CopilotRequest(BaseModel):
    messages: List[Message]
    tools: Optional[List[Dict[str, Any]]] = None
    system: Optional[str] = None

class CopilotResponse(BaseModel):
    messages: List[Dict[str, Any]]

class GraphQLRequest(BaseModel):
    query: str
    variables: Optional[Dict[str, Any]] = {}
    operationName: Optional[str] = None

def convert_langchain_to_copilot_format(messages: List) -> List[Dict[str, Any]]:
    """Convert LangChain messages to CopilotKit format."""
    copilot_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            copilot_messages.append({
                "role": "user",
                "content": msg.content
            })
        elif isinstance(msg, AIMessage):
            copilot_messages.append({
                "role": "assistant", 
                "content": msg.content
            })
        elif isinstance(msg, SystemMessage):
            copilot_messages.append({
                "role": "system",
                "content": msg.content
            })
    return copilot_messages

def convert_copilot_to_langchain_format(messages: List[Message]) -> List:
    """Convert CopilotKit messages to LangChain format."""
    langchain_messages = []
    for msg in messages:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_messages.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            langchain_messages.append(SystemMessage(content=msg.content))
    return langchain_messages

@app.post("/api/copilotkit")
async def copilotkit_endpoint(request: Request):
    """Main CopilotKit endpoint that handles both GraphQL and chat requests."""
    
    try:
        body = await request.json()
        
        # Check if this is a GraphQL request
        if "query" in body:
            return await handle_graphql_request(body)
        else:
            # Handle as regular chat request
            chat_request = CopilotRequest(**body)
            return await handle_chat_request(chat_request)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def handle_graphql_request(body: Dict[str, Any]):
    """Handle GraphQL queries from CopilotKit client."""
    query = body.get("query", "")
    operation_name = body.get("operationName", "")
    variables = body.get("variables", {})
    
    if operation_name == "availableAgents" or "availableAgents" in query:
        return {
            "data": {
                "availableAgents": {
                    "agents": [
                        {
                            "name": "default",
                            "id": "default", 
                            "description": "Default CopilotKit agent",
                            "__typename": "Agent"
                        }
                    ],
                    "__typename": "AvailableAgentsResponse"
                }
            }
        }
    
    elif operation_name == "generateCopilotResponse" or "generateCopilotResponse" in query:
        return await handle_generate_copilot_response(variables)
    
    # Handle other GraphQL operations as needed
    return {"data": {}}

async def handle_generate_copilot_response(variables: Dict[str, Any]):
    """Handle the generateCopilotResponse mutation."""
    data = variables.get("data", {})
    messages_data = data.get("messages", [])
    context = data.get("context", [])
    thread_id = data.get("threadId", f"thread_{os.urandom(4).hex()}")
    run_id = data.get("runId", f"run_{os.urandom(4).hex()}")
    
    # Extract messages from the format sent by client
    langchain_messages = []
    for msg in messages_data:
        if "textMessage" in msg:
            text_msg = msg["textMessage"]
            role = text_msg.get("role", "user")
            content = text_msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
    
    # Add context information to system message
    if context:
        context_text = "\n".join([f"{ctx.get('description', '')}: {ctx.get('value', '')}" for ctx in context])
        if langchain_messages and isinstance(langchain_messages[0], SystemMessage):
            langchain_messages[0].content += f"\n\nContext:\n{context_text}"
        else:
            langchain_messages.insert(0, SystemMessage(content=f"Context:\n{context_text}"))
    
    # Generate response
    model_with_tools = model.bind_tools(tools)
    response = await model_with_tools.ainvoke(langchain_messages)
    
    # Format response according to CopilotKit GraphQL schema
    response_content = response.content if hasattr(response, 'content') else str(response)
    
    return {
        "data": {
            "generateCopilotResponse": {
                "threadId": thread_id,
                "runId": run_id,
                "extensions": {
                    "__typename": "Extensions"
                },
                "status": {
                    "code": "SUCCESS",
                    "__typename": "SuccessResponseStatus"
                },
                "messages": [
                    {
                        "id": f"msg_{os.urandom(4).hex()}",
                        "createdAt": "2025-10-18T11:01:25.000Z",
                        "content": response_content,
                        "role": "assistant",
                        "parentMessageId": None,
                        "status": {
                            "code": "SUCCESS",
                            "__typename": "SuccessMessageStatus"
                        },
                        "__typename": "TextMessageOutput"
                    }
                ],
                "metaEvents": [],
                "__typename": "CopilotResponse"
            }
        }
    }

async def handle_chat_request(request: CopilotRequest):
    """Handle regular chat requests."""
    
    # Convert messages to LangChain format
    langchain_messages = convert_copilot_to_langchain_format(request.messages)
    
    # Add system message if provided
    if request.system:
        langchain_messages.insert(0, SystemMessage(content=request.system))
    
    # Bind tools to model
    model_with_tools = model.bind_tools(tools)
    
    # Generate response
    response = await model_with_tools.ainvoke(langchain_messages)
    
    # Convert response back to CopilotKit format
    response_messages = convert_langchain_to_copilot_format([response])
    
    return {"messages": response_messages}

@app.post("/api/copilotkit/stream")
async def copilotkit_stream_endpoint(request: CopilotRequest):
    """Streaming endpoint for real-time responses."""
    
    async def generate_stream():
        try:
            # Convert messages to LangChain format
            langchain_messages = convert_copilot_to_langchain_format(request.messages)
            
            # Add system message if provided
            if request.system:
                langchain_messages.insert(0, SystemMessage(content=request.system))
            
            # Bind tools to model
            model_with_tools = model.bind_tools(tools)
            
            # Stream response
            async for chunk in model_with_tools.astream(langchain_messages):
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"
                    
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.get("/api/copilotkit/available-tools")
async def available_tools():
    """Return available tools for the client."""
    return {
        "tools": [
            {
                "name": "get_weather",
                "description": "Get the weather for a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get weather for"
                        }
                    },
                    "required": ["location"]
                }
            }
        ]
    }

def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", 4000))
    uvicorn.run(
        "server_simple:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )

if __name__ == "__main__":
    main()