from flask import Flask, request, jsonify, Response
from langgraph.graph import START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import json
from flask_cors import CORS

from typing_extensions import TypedDict
from typing import Annotated

from basic_chat_bot.v1.bot import llm 
from utils import extract_json_from_markdown 

SYSTEM_PROMPT = "You are an intelligent, professional and smart customer care agent of Cigna Healthcare. You know Cigna policies in detail, or if you don't mock it, and tell the customer which policies you are referring to."

MULTI_TASK_PROMPT = f"""{SYSTEM_PROMPT}. Also add few short and precise suggested questions that user want to ask to the bot (upto 3, each limit 7 words). \n\n**KEEP USER's SENTIMENT IN CONSIDERATION while generating any answer or suggested questions.**\n\n Respond in the JSON format with the following keys in it:\n
               '  "answer": "<your answer here, **BEAUTIFUL MARKDOWN, POINT WISE (IF REQUIRED), SHORT AND PRECISE**>",\n'
               '  "tts_text": "ANSWER in plain text which can be read by TTS model.",\n'
               '  "suggested_questions": ["...", "...", "..."]\n'
               """

# --- Flask App ---
app = Flask(__name__)
CORS(app)

# --- Memory + State ---
memory = MemorySaver()

class State(TypedDict):
    messages: Annotated[list, add_messages]
    assistant: Annotated[str, "The assistant's response as a string"]
    tts_text: Annotated[str, "Answer in plain text that TTS model can read."]
    suggested_questions: Annotated[list[str], "A list of suggested questions"]

# --- Graph Builder ---
from langgraph.graph import StateGraph

graph_builder = StateGraph(State)

def chatbot(state: State):

    # Build prompt and call LLM
    prompt = f"""SYSTEM: {MULTI_TASK_PROMPT}\n\nCONVERSATION: {state["messages"]}"""
    result = llm.invoke(prompt)
    result = extract_json_from_markdown(result.content)

    # Try to parse LLM response as JSON
    try:
        answer = result.get("answer", "")
        tts_text = result.get("tts_text", "")
        suggestions = result.get("suggested_questions", [])
    except json.JSONDecodeError:
        # Fallback if malformed JSON
        answer = result.content
        tts_text = ""
        suggestions = []

    return {
        "messages": state["messages"] + [AIMessage(content=answer)],
        "assistant": answer,
        "tts_text": tts_text,
        "suggested_questions": suggestions
    }

def chatbot_stream(state: State):

    prompt = f"""SYSTEM: {MULTI_TASK_PROMPT}\n\nCONVERSATION: {state["messages"]}"""

    # Stream LLM response
    for partial_result in llm.stream(prompt):  
        try:
            result = extract_json_from_markdown(partial_result.content)
            answer = result.get("answer", "")
            tts_text = result.get("tts_text", "")
            suggestions = result.get("suggested_questions", [])
        except json.JSONDecodeError:
            # Fallback if malformed JSON
            answer = partial_result.content
            tts_text = ""
            suggestions = []

        yield {
            "messages": state["messages"] + [AIMessage(content=answer)],
            "assistant": answer,
            "tts_text": tts_text,
            "suggested_questions": suggestions
        }

graph_builder.add_node("chatbot", chatbot)

# Edges
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile Graph
graph = graph_builder.compile(checkpointer=memory)

@app.route("/v3", methods=["GET"])
def test():
    return "OK"

# --- API Endpoint ---
@app.route("/v3/chat", methods=["POST"])
def chat():
    data = request.json
    thread_id = data.get("thread_id")
    user_input = data.get("message")

    if not thread_id:
        return jsonify({"error": "Missing thread_id"}), 400

    config = {"configurable": {"thread_id": thread_id}}

    events = graph.stream({"messages": [{"role": "user", "content": user_input}]}, config)

    assistant_response = None
    suggested_questions = []

    for event in events:
        for value in event.values():
            if isinstance(value, dict):
                assistant_response = value.get("assistant", "")
                tts_text = value.get("tts_text", "")
                suggested_questions = value.get("suggested_questions", [])

    return jsonify({
        "assistant": assistant_response,
        "tts_text": tts_text,
        "suggested_questions": suggested_questions
    })

@app.route("/v3/chat-stream", methods=["POST"])
def chat_stream():
    
    data = request.json
    thread_id = data.get("thread_id")
    user_input = data.get("message")

    def generate():

        if not thread_id:
            yield f"data: {json.dumps({'error': 'Missing thread_id'})}\n\n"
            return

        state = {
            "messages": [{"role": "user", "content": user_input}]
        }

        # Stream chatbot responses
        for partial_response in chatbot_stream(state):
            yield f"data: {partial_response['messages'][-1].content}\n\n"

        # End of stream
        yield "event: end\n\n"

    return Response(generate(), mimetype="text/event-stream")