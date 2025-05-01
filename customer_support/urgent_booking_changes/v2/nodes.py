import openai
from dotenv import load_dotenv
import os
import json
import requests
from customer_support.urgent_booking_changes.v1.state import AgentState
from customer_support.urgent_booking_changes.v1.nodes import hosted_url

load_dotenv()
openai.api_key = os.getenv("OPENAI_SECRET")

def llm_parse_input(state: AgentState) -> AgentState:
    """Use  LLM to extract intent/entities."""
    user_input = state["user_input"]

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """
Extract intent and entities from travel queries:
- Intent: cancel_booking, reschedule_booking, general_inquiry
- Entities: booking_id, new_date, destination
Return JSON only.
"""
            }, 
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    parsed = json.loads(response.choices[0].message.content)
    state.update(parsed)
    return state

# Rescheduling nodes
def check_availability(state: AgentState) -> AgentState:
    """Mock flight/hotel availability check."""
    state["is_available"] = True
    return state

def process_rescheduling(state: AgentState) -> AgentState:
    """Call reschedule API."""
    if state.get("confirmation") and state["is_available"]:
        response = requests.post(
            f"{hosted_url}/bookings/{state['booking_id']}/reschedule",
            headers={"api-key": state["api_key"]},
            json={"new_date": state["new_date"]}
        )
        if response.status_code != 200:
            state["error"] = "Rescheduling failed"
    return state

def suggest_alternatives(state: AgentState) -> AgentState:
    """Propose alternative options when original request isn't feasible."""
    booking_details = state.get("booking_details", {})

    # Mock alternatives database/API call
    state["alternatives"] = {
        "date_options": [
            booking_details.get("date", "") + " +2 days",
            booking_details.get("date", "") + " +5 days"
        ],
        "destination_options": [
            {"route": "NYC-LON -> NYC-PAR", "price_diff": -150},
            {"route": "NYC-LON -> NYC-AMS", "price_diff": -75}
        ],
        "class_upgrade": {
            "available": True,
            "new_class": "Business",
            "price_diff": +300
        }
    }

    # General natural language suggestions
    suggestions = [
        "Alternative dates available:",
        *state["alternatives"]["date_options"],
        "\nAlternative destinations:",
        *[f"{opt['route']} (${opt['price_diff']})" for opt in state["alternatives"]["destination_options"]],
        "\nClass upgrade available: Business (+$300)"
    ]

    # For production: Integrate with chat interface
    print("\nSUGGESTIONS:\n" + "\n-".join(suggestions))

    # Simulate user choice (mock - would by UI input in production)
    state["selected_alternative"] = "date" # Can be 'date', 'destination', 'class', or None

    return state

# Modified conditional edges
def route_alternative_selection(state: AgentState) -> str:
    from customer_support.urgent_booking_changes.v2.graph import PROCESS_RESCHEDULING, ESCALATE_TO_HUMAN

    if state.get("selected_alternative"):
        return PROCESS_RESCHEDULING
    return ESCALATE_TO_HUMAN

def handle_alternative_choice(state: AgentState) -> str:
    """Process user's selected alternative"""
    selected = state["selected_alternative"]
    alternatives = state["alternatives"]

    if selected == "date":
        state["new_date"] = alternatives["date_options"][0] # Take first alternative date
    elif selected == "destination":
        new_route = alternatives["destination_options"][0]["route"]
        state["destination"] = new_route.split("-> ")[-1]
    elif selected == "class":
        state["booking_class"] = alternatives["class_upgrade"]["new_class"]
    
    return state

def general_enquiry_handler(state: AgentState) -> AgentState:
    """Handle non-urgent general inquiries using knowledge base"""
    try:
        # Use LLM to generate response from knowledge base
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"""
Answer travel questions using this knowledge base:
{KNOWLEDGE_BASE}
If unsure, direct user to help center.
"""
                }, 
                {
                    "role": "user",
                    "content": state["user_input"]
                }
            ]
        )

        state["response"] = response.choices[0].message.content
        state["sources"] = _find_knowledge_sources(state["user_input"])

    except Exception as e:
        state["error"] = f"Enquiry handling failed: {str(e)}"
        state["response"] = DEFAULT_FALLBACK_RESPONSE
    
    return state

# Helper functions
def _find_knowledge_sources(query: str) -> list:
    """Retrieve relevant knowledge base articles"""
    # Vector similarity search implementation
    return []

# Constants
KNOWLEDGE_BASE = {
    "baggage_policy": "Allow 1 checked bag up to 23kg",
    "visa_requirements": "Check destination embassy website",
    "contact_info": "24/7 support: 1-800-TRAVEL"
}

DEFAULT_FALLBACK_RESPONSE = """
I'm unable to answer that precisely.
Please visit our Help Center or contact support.
"""

def escalate_to_human(state: AgentState) -> AgentState:
    """Transfer complex cases to human agents with proper context packaging."""
    # Create escalation ticket
    ticket_data = {
        "user_id": state.get("user_id", "unknown"),
        "booking_id": state.get("booking_id"),
        "conversation_history": state.get("conversation_history", []),
        "error_reason": state.get("error", "Unknown error"),
        "escalation_reason": _determine_escalation_reason(state),
        "priority": _calculate_escalation_priority(state),
        "attachments": {
            "booking_details": state.get("booking_details"),
            "payment_history": _get_related_payments(state),
            "user_profile": _get_user_profile(state)
        }
    }

    # Call ticketing API
    response = requests.post(
        f"{hosted_url}/tickets",
        headers={"api-key": state['api_key']},
        json=ticket_data
    )

    if response.status_code == 201:
        state["escalation_ticket_id"] = response.json()["ticket_id"]
        state["human_eta"] = _calculate_sla_eta(state)
    else:
        state["error"] = f"Escalation failed: {response.text}"
    
    # Generate human-readable message
    state["response_message"] = _format_escalation_message(state)
    return state

def _determine_escalation_reason(state) -> str:
    """Classify escalation reason for routing"""
    if state.get("error"):
        if "payment" in state["error"].lower():
            return "payment_verification"
        if "availability" in state["error"].lower():
            return "inventory_management"
    return "complex_case"

def _calculate_escalation_priority(state) -> int:
    """Dynamic priority based on business rules"""
    priority = 3
    if state.get("booking_details", {}).get("departure_in_hours", 999) < 48:
        priority = 1
    elif state.get("user_profile", {}).get("loyalty_tier", 0) > 3:
        priority = 2
    return priority

def _format_escalation_message(state) -> str:
    """Generate user-facing escalation message"""
    base_msg = "Your case has been escalated to our specialist team"
    if state.get("human_eta"):
        base_msg += f" (expected response within {state['human_eta']} minutes)"
    
    contact_options = "\n".join([
        "Continue via this chat",
        "Email: premium-support@travelagency.com",
        "Call: +1-800-555-HELP"
    ])

    return f"""
{base_msg}

Your reference: {state.get('escalation_ticket_id', 'N/A')}

Contact options:
{contact_options}
"""

# Helper functions
def _get_related_payments(state):
    """Mock payment history lookup"""
    return requests.get(
        f"{hosted_url}/payments",
        params={"booking_id": state["booking_id"]},
        headers={"api-key": state["api_key"]}
    ).json()

def _get_user_profile(state):
    """Fetch user metadata"""
    return requests.get(
        f"{hosted_url}/users/{state['user_id']}",
        headers={"api-key": state["api_key"]}
    ).json()

def _calculate_sla_eta(state) -> int:
    """Calculate expected response time based on priority"""
    sla_matrix = {
        1: 15, # Urgent: Departure within 48h
        2: 60, # High-value customer
        3: 240 # Standard
    }
    return sla_matrix.get(state.get("priority", 3), 240)