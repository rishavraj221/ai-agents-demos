import requests

from customer_support.urgent_booking_changes.state import AgentState
hosted_url = "http://localhost:8000"

# ---- Node 1: Parse User Input ----
def parse_input(state: AgentState) -> AgentState:
  """Extract booking ID/intent from natural language."""
  text = state["user_input"].lower()
  state["intent"] = "cancel_booking" if "cancel" in text else "unknown"
  state["booking_id"] = "BOOKING123" # Mock extraction (use LLM in production)
  return state

# ---- Node 2: Authenticate ----
def authenticate(state: AgentState) -> AgentState:
  """Validate API key against mock system."""
  if state.get("api_key") != "SECRET_KEY_123":
    state["error"] = "Invalid API key"
  return state

# ---- Node 3: Fetch Booking Details ----
def fetch_booking(state: AgentState) -> AgentState:
  """Call mock API to retrieve booking data."""
  if state.get("error"):
    return state # Skip if auth failed
  
  booking_id = state["booking_id"]
  response = requests.get(
      f"{hosted_url}/bookings/{booking_id}",
      headers={"api-key": state["api_key"]}
  )
  if response.status_code == 200:
    state["booking_details"] = response.json()
  else:
    state["error"] = response.json()["detail"]
  return state

# ---- Node 4: Confirm Action ----
def confirm_action(state: AgentState) -> AgentState:
  """Seek user confirmation (mock UI interaction)."""
  if not state.get("error"):
    print(f"PROMPT: Cancel booking {state['booking_id']}? [yes/no]")
    state["confirmation"] = True # Simulate user input "yes"
  return state

# ---- Node 5: Process Cancellation ----
def process_cancellation(state: AgentState) -> AgentState:
  """Execute cancellation via mock API."""
  if state.get("confirmation") and not state.get("error"):
    response = requests.post(
        f"{hosted_url}/bookings/{state['booking_id']}/cancel",
        headers={"api-key": state["api_key"]}
    )
    if response.status_code != 200:
      state["error"] = "Cancellation failed"
  return state

# ---- Node 6: Error Handler ----
def handle_error(state: AgentState) -> AgentState:
  """Route errors to escalation or retry."""
  if state.get("error"):
    print(f"ERROR: {state['error']} - Escalating to human agent.")
  return state