from langchain_core.tools import tool
from langgraph.types import Command, interrupt
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]

## v1.llm has llm without tools binded
## v1.State
## v2.tool is a TavilySearch tool
from basic_chat_bot.v1.bot import llm, State
from basic_chat_bot.v2.bot import tool

tools = [tool, human_assistance]

llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    # Because we will be interrupting during tool execution, we disable parallel tool calling to avoid repeating any tool invocations when we resume.
    assert len(message.tool_calls) <= 1
    return {"messages": [message]}

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition
)
graph_builder.add_edge("tools", "chatbot")

memory = MemorySaver()

graph = graph_builder.compile(checkpointer=memory)

def get_human_command(human_response: str):

    return Command(resume={"data": human_response})

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
                    print(f"AI Message: {ai_message}")

                    human_response = input("Human Response: ")
                    events = graph.stream(get_human_command(human_response), config, stream_mode="values")
                    for event in events:
                        if "messages" in event:
                            print(f"Assistant: {event['messages'][-1].content}")
            else:
                print(f"Assistant: {event['messages'][-1].content}")