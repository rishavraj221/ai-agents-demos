from typing import Annotated

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

## NOTE - We are using an in-memory checkpointer. This is convenient for our tutorial.
## In a production application, we will change this to use 'SqliteSaver' or 'PostgresSaver' and connect to your own DB.

## State
class State(TypedDict):
    messages: Annotated[list, add_messages]

## Graph Builder
graph_builder = StateGraph(State)

## v2.tool is a TavilySearch tool
## v2.llm_with_tools has tool binded with it
from basic_chat_bot.v2.bot import llm_with_tools, tool

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

## Nodes
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

## Edges
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

## Graph
graph = graph_builder.compile(checkpointer=memory)

## Now let's interact with the bot. First, pick a thread to use as the key for this conversation.
config = {"configurable": {"thread_id": "1"}}

def stream_graph_updates(graph, user_input: str, config):

    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

def get_snapshot(config):
    snapshot = graph.get_state(config)
    return snapshot

## to get 'next' node to process
# snapshot.next