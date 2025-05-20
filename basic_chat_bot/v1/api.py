from typing import Annotated

from typing_extensions import TypedDict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

def get_llm(provider, model, api_key):

    if provider == 'openai':
        return ChatOpenAI(model=model, api_key=api_key)

    else:
        raise Exception("Provider not supported yet!")
    
def build_requested_graph(nodes, edges):
    node_id_type_dict = {}
    for node in nodes:
        node_id = node.get("id", "")
        node_type = node.get("type", "")

        node_id_type_dict[node_id] = node_type

        if node_type == "start" or node_type == "end" or node_type == "io":
            continue

    edge_graph = {}
    for edge in edges:
        edge_source = edge.get("source", "")
        edge_target = edge.get("target", "")

        if edge_source == "end":
            continue

        if edge_source in edge_graph:
            edge_graph[edge_source].append(edge_target)
        else:
            edge_graph[edge_source] = [edge_target]

    # remove "io" nodes, maintaining it's edges
    for node in edge_graph:
        
        for index, neighbour in enumerate(edge_graph[node]):
            if neighbour in node_id_type_dict and node_id_type_dict[neighbour] == "io":
                edge_graph[node][index] = edge_graph[neighbour][0]

    delete_node_set = set()
    for id in node_id_type_dict:
        if node_id_type_dict[id] == "io":
            delete_node_set.add(id)
    
    for id in delete_node_set:
        del edge_graph[id]

    edge_graph_improved = {}
    for key in edge_graph:
        source = node_id_type_dict[key]
        targets = []

        for target in edge_graph[key]:
            targets.append(node_id_type_dict[target])

        if source in edge_graph_improved:
            edge_graph_improved[source].extend(targets)
        else:
            edge_graph_improved[source] = targets
    
    return edge_graph_improved

def build_graph(llm_data, nodes, edges):

    llm_provider = llm_data.get("provider", "")
    llm_model = llm_data.get("model", "")
    llm_api_key = llm_data.get("api_key", "")

    llm = get_llm(provider=llm_provider, model=llm_model, api_key=llm_api_key)

    class State(TypedDict):
        messages: Annotated[list, add_messages]

    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}

    graph_builder = StateGraph(State)

    requested_graph = build_requested_graph(nodes, edges)

    nodes_set = set()
    for node in requested_graph:
        nodes_set.add(node)

        for neighbour in requested_graph[node]:
            nodes_set.add(neighbour)
    
    # add nodes to langgraph graph_builder
    for node in nodes_set:
        if node == "start" or node == "end":
            continue
        
        if node == "chatbot":
            graph_builder.add_node(node, chatbot)
    
    for source in requested_graph:
        
        for target in requested_graph[source]:
            if source == "start":
                source = START
            if target == "end":
                target = END
            
            graph_builder.add_edge(source, target)

    return graph_builder.compile()
    

@app.route("/", methods=["GET"])
def api_test():
    return "OK"

@app.route("/graph-compile", methods=['POST'])
def graph_compile():
    body_data = request.get_json()

    llm_data = body_data.get("llm_data", "")
    nodes = body_data.get("nodes", "")
    edges = body_data.get("edges", "")
    input_text = body_data.get("input_text", "")

    langgraph_graph = build_graph(llm_data=llm_data, nodes=nodes, edges=edges)

    events = langgraph_graph.stream({"messages": [{"role": "user", "content": input_text}]})

    for event in events:
        print(event)

    return "OK"