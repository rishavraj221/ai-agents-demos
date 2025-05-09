from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    birthday: str

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool

from langgraph.types import Command, interrupt

@tool
# Note that because we are generating a ToolMessage for a state update, 
# we generatlly require the ID of the corresponding tool call. 
# We can use LangChain's InjectedToolCallId to signal that this argument 
# should not be revealed to the model in the tool's schema.
def human_assistance(name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> str:
    """Request assistance from a human."""
    human_response = interrupt(
        {
            "question": "Is this correct?",
            "name": name,
            "birthday": birthday
        }
    )
    # If the information is correct, update the state as-is.
    if human_response.get("correct", "").lower().startswith("y"):
        verified_name = name
        verified_birthday = birthday
        response = "Correct"
    # Otherwise, receive information from the human reviewer.
    else:
        verified_name = human_response.get("name", name)
        verified_birthday = human_response.get("birthday", birthday)
        response = f"Made a correction: {human_response}"

    # This time we explicitly update the state with a ToolMessage inside the tool.
    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)]
    }
    # We return a Command object in the tool to update our state.
    return Command(update=state_update)

## v1.llm has llm without tools binded
from basic_chat_bot.v1.bot import llm
## v2.tool is a TavilySearch tool
from basic_chat_bot.v2.bot import tool

tools = [tool, human_assistance]
llm_with_tools = llm.bind_tools(tools)

## chatbot
def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    assert len(message.tool_calls) <= 1
    return {"messages": [message]}

from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

## graph builder
graph_builder = StateGraph(State)

## Nodes
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

def get_graph_state(graph, config):

    return graph.get_state(config)

def update_graph_state(graph, config, updated_state):
    
    graph.update_state(config, updated_state)

    return

def get_human_command(name: str, birthday: str):

    return Command(resume={"name": name, "birthday": birthday})

def stream_graph_updates(graph, user_input: str, config): 

    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values"
    )

    for event in events:
        if "messages" in event:
            adt_kw = dict(event["messages"][-1].additional_kwargs)
            if 'tool_calls' in adt_kw:
                if adt_kw['tool_calls'][0]['function']['name'] == 'human_assistance':
                    ai_message = adt_kw['tool_calls'][0]['function']['arguments']

                    name = input("Name: ")
                    birthday = input("Birthday: ")
                    events = graph.stream(get_human_command(name, birthday), config, stream_mode="values")
                    for event in events:
                        if "messages" in event:
                            print(f"Assistant: {event['messages'][-1].content}")
            else:
                print(f"Assistant: {event['messages'][-1].content}")