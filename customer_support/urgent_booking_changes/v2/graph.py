from langgraph.graph import StateGraph, END
from customer_support.urgent_booking_changes.v1.state import AgentState
from customer_support.urgent_booking_changes.v1.graph import PARSE_INPUT, AUTHENTICATE, FETCH_BOOKING, CONFIRM_ACTION, PROCESS_CANCELLATION, ERROR_HANDLER
from customer_support.urgent_booking_changes.v1.nodes import parse_input, authenticate, fetch_booking, confirm_action, process_cancellation, handle_error
from customer_support.urgent_booking_changes.v2.nodes import llm_parse_input, check_availability, process_rescheduling, suggest_alternatives, handle_alternative_choice, route_alternative_selection, general_enquiry_handler, escalate_to_human

# Build v2 LangGraph
builder = StateGraph(AgentState)

RESCHEDULE_BOOKING = "reschedule_booking"
CHECK_AVAILABILITY = "check_availability"
GENERAL_ENQUIRY_HANDLER = "general_enquiry_handler"
PROCESS_RESCHEDULING = "process_rescheduling"
SUGGEST_ALTERNATIVES = "suggest_alternatives"
LLM_PARSER = "llm_parser"
ESCALATE_TO_HUMAN = "escalate_to_human"
HANDLE_ALTERNATIVE_CHOICE = "handle_alternative_choice"
ROUTE_INTENT = "route_intent"
ROUTE_AVAILABILITY = "route_availability"
CONFIRM_RESCHEDULE = "confirm_reschedule"
ROUTE_ALTERNATIVE_SELECTION = "route_alternative_selection"

def route_intent(state: AgentState) -> str:
    """Conditional edge: Route based on intent."""
    if state.get("error"):
        return ERROR_HANDLER
    intent = state.get("intent")
    if intent == PROCESS_CANCELLATION:
        return PROCESS_CANCELLATION
    elif intent == RESCHEDULE_BOOKING:
        return CHECK_AVAILABILITY
    else:
        return GENERAL_ENQUIRY_HANDLER

def route_availability(state: AgentState) -> str:
    return PROCESS_RESCHEDULING if state["is_available"] else SUGGEST_ALTERNATIVES

nodes = {
    # Core Flow
    LLM_PARSER: llm_parse_input,
    AUTHENTICATE: authenticate, 
    FETCH_BOOKING: fetch_booking,

    # Cancellation Path
    CONFIRM_ACTION: confirm_action,
    PROCESS_CANCELLATION: process_cancellation,

    # Rescheduling Path
    CHECK_AVAILABILITY: check_availability,
    CONFIRM_RESCHEDULE: confirm_action,
    PROCESS_RESCHEDULING: process_rescheduling,

    # Alternative System
    SUGGEST_ALTERNATIVES: suggest_alternatives,
    HANDLE_ALTERNATIVE_CHOICE: handle_alternative_choice,

    # Special Handlers
    ERROR_HANDLER: handle_error,
    ESCALATE_TO_HUMAN: escalate_to_human,
    GENERAL_ENQUIRY_HANDLER: general_enquiry_handler
}

for name, node in nodes.items():
    builder.add_node(name, node)

# Core Flow
builder.set_entry_point(LLM_PARSER)
builder.add_edge(LLM_PARSER, AUTHENTICATE)

# Intent Routing
builder.add_conditional_edges(
    AUTHENTICATE,
    route_intent,
    {
        FETCH_BOOKING: FETCH_BOOKING,
        CHECK_AVAILABILITY: CHECK_AVAILABILITY,
        GENERAL_ENQUIRY_HANDLER: GENERAL_ENQUIRY_HANDLER,
        ERROR_HANDLER: ERROR_HANDLER
    }
)

# Cancellation Path
builder.add_edge(FETCH_BOOKING, CONFIRM_ACTION)
builder.add_edge(CONFIRM_ACTION, PROCESS_CANCELLATION)
builder.add_edge(PROCESS_CANCELLATION, ERROR_HANDLER)

# Rescheduling Path
builder.add_conditional_edges(
    CHECK_AVAILABILITY,
    route_availability,
    {
        CONFIRM_RESCHEDULE: CONFIRM_RESCHEDULE,
        SUGGEST_ALTERNATIVES: SUGGEST_ALTERNATIVES
    }
)
builder.add_edge(CONFIRM_RESCHEDULE, PROCESS_RESCHEDULING)
builder.add_edge(PROCESS_RESCHEDULING, ERROR_HANDLER)

# Alternative Subsystem
builder.add_conditional_edges(
    SUGGEST_ALTERNATIVES,
    route_alternative_selection,
    {
        HANDLE_ALTERNATIVE_CHOICE: HANDLE_ALTERNATIVE_CHOICE,
        ESCALATE_TO_HUMAN: ESCALATE_TO_HUMAN
    }
)
builder.add_edge(HANDLE_ALTERNATIVE_CHOICE, CHECK_AVAILABILITY) # Loop Back

# Termination Points
builder.add_edge(GENERAL_ENQUIRY_HANDLER, END)
builder.add_edge(ESCALATE_TO_HUMAN, END)
builder.add_edge(ERROR_HANDLER, END)

agent = builder.compile()