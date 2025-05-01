from langgraph.graph import StateGraph, END
from customer_support.urgent_booking_changes.state import AgentState
from customer_support.urgent_booking_changes.nodes import parse_input, authenticate, fetch_booking, confirm_action, process_cancellation, handle_error

# Build LangGraph
builder = StateGraph(AgentState)

PARSE_INPUT = "parse_input"
AUTHENTICATE = "authenticate"
FETCH_BOOKING = "fetch_booking"
CONFIRM_ACTION = "confirm_action"
PROCESS_CANCELLATION = "process_cancellation"
ERROR_HANDLER = "error_handler"

# Add Nodes
builder.add_node(PARSE_INPUT, parse_input)
builder.add_node(AUTHENTICATE, authenticate)
builder.add_node(FETCH_BOOKING, fetch_booking)
builder.add_node(CONFIRM_ACTION, confirm_action)
builder.add_node(PROCESS_CANCELLATION, process_cancellation)
builder.add_node(ERROR_HANDLER, handle_error)

# Define Edges
builder.set_entry_point(PARSE_INPUT)
builder.add_edge(PARSE_INPUT, AUTHENTICATE)
builder.add_edge(AUTHENTICATE, FETCH_BOOKING)
builder.add_edge(FETCH_BOOKING, CONFIRM_ACTION)
builder.add_edge(CONFIRM_ACTION, PROCESS_CANCELLATION)
builder.add_edge(PROCESS_CANCELLATION, ERROR_HANDLER)
builder.add_edge(ERROR_HANDLER, END)

agent = builder.compile()