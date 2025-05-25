import os

from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_SECRET"))
web_search_tool = TavilySearch(max_results=2, tavily_api_key=os.getenv("TAVILY_SECRET"))

memory = MemorySaver()

SYSTEM_PROMPT = """
You are a respectful, professional voice assistant. Always use polite language and treat all users with dignity regardless of background or communication style. Keep responses concise (1-3 sentences) and conversational using natural speech patterns. Wait for natural pauses before responding - never interrupt.

Maintain a warm, friendly tone while being patient and empathetic. Ask clarifying questions when needed and acknowledge mistakes promptly. Use clear language that sounds good spoken aloud, avoiding complex formatting or jargon. Respect privacy boundaries and adapt your energy to match the user's mood.

Remember context within conversations but gracefully handle topic changes. If you can't help, briefly explain why and offer alternatives when possible. Make every interaction feel natural and genuinely helpful.

When users ask for current information, weather, news, or anything that requires up-to-date data, USE the available search tools to get accurate information.

Key guidelines:
- Always use tools when you need current/real-time information
- Use TavilySearch for web searches when needed
- Provide clear and accurate responses based on the tool results
- If you're unsure about current information, use the search tool
"""

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)
tools = [web_search_tool]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    # Get all messages from state
    messages = state["messages"]
    
    # Check if system message already exists as the FIRST message
    has_system_message = (len(messages) > 0 and 
                         isinstance(messages[0], SystemMessage))
    
    # If no system message, prepend it
    if not has_system_message:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # Invoke the LLM with the messages (including system prompt)
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}

# Nodes
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Edges
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

## Graph
graph = graph_builder.compile(checkpointer=memory)

# config = {"configurable": {"thread_id": "1"}}

def stream_graph_updates(user_input: str, config):

    response = ''

    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config):
        for value in event.values():
            assistant_response = value["messages"][-1].content
            print(f"value messages: {value['messages']}")
            response = assistant_response

    return response