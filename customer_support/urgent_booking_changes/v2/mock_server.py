from fastapi import HTTPException, Header
from customer_support.urgent_booking_changes.v1.mock_server import app, mock_bookings, AgentRequest

@app.post("/bookings/{booking_id}/reschedule")
def reschedule_booking(booking_id: str, new_date: str, api_key: str = Header(...)):
    if booking_id not in mock_bookings:
        raise HTTPException(status_code=404, detail="Booking not allowed")
    mock_bookings[booking_id]["date"] = new_date
    return {"message": f"Rescheduled to {new_date}"}

@app.post("/agent/v2")
def agent_invoke(request: AgentRequest, api_key: str = Header(...)):
  user_input = request.user_input

  initial_state = {
    "user_input": user_input,
    "api_key": "SECRET_KEY_123"
  }

  from customer_support.urgent_booking_changes.v2.graph import agent
  result = agent.invoke(initial_state)

  return {"message": str(result)}