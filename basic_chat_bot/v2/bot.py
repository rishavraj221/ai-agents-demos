from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import os

load_dotenv()

######################################################
## Tool for websearch
######################################################
tool = TavilySearch(max_results=2, tavily_api_key=os.getenv("TAVILY_SECRET"))
tools = [tool]

# result = tool.invoke("What's a 'node' in langgraph?") # The 'result' are page summaries our chatbot can use to answer questions.
# import pprint
# pprint.pp(result)

######################################################
## Upgrade from v1
######################################################
from basic_chat_bot.v1.bot import llm, State, stream_graph_updates
import json
from langchain_core.messages import ToolMessage

llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

## Here is the implementation of BasicToolNode that checks the most recent message in the state and call tools if the message contains tool_calls.
## It relies on the LLM's tool_calling support (available on Anthropic, OpenAI, Gemini, ...)
## We will later replace this with Langgraph's prebuilt ToolNode, but building it ourselves is instructive.
class BasicToolNode:
    """A node that run the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}
    
    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                )
            )
        return {"messages": outputs}

tool_node = BasicToolNode(tools=[tool])
    
## Conditional Edges: usually contain "if" statements to route to different nodes depending on the current graph state.
## These functions receive the current graph state and return a string or list of strings indicating which node(s) to call next.

## route_tools is a router function that checks for tool_calls in the chatbot's output.
## Provide this function to the graph by calling add_conditional_edges, which tells the graph that whenever the chatbot node completes to check this function to see where to go next.
## The condition will route to tools if tool calls are present and END if not.
## Later, we will replace this with the prebuilt tools_condition to be more concise, but implementing it ourselves first makes things more clear.
def route_tools(state: State):
    """
    Use in the conditional_edge to route to the ToolNode if the last message has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
## The 'tools_condition' function returns "tools" if the chatbot asks to use a tool, and "END" if
## it is fine directly responding. This conditional routing defines the main agent loop.
graph_builder.add_conditional_edges(
    "chatbot", 
    route_tools,
    {"tools": "tools", END: END} # This dictionary tell the graph to interpret the condition's outputs as a specific node. It defaults to the identity function, but if you want to use a node named something else apart from "tools", you can update the value of the dictionary to something else. e.g., "tools": "my_tools"
)
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile()

## Trial
if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(graph, user_input)