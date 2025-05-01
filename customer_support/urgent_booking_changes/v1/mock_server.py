from fastapi import FastAPI, HTTPException, Header
from pyngrok import ngrok
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Authenticate ngrok
ngrok.set_auth_token(os.getenv("NGROK_AUTH_TOKEN"))

# Mock database
mock_bookings = {
    "BOOKING123": {
        "user_id": "USER456",
        "status": "confirmed",
        "flight": "NYC-LON 2024-10-20"
    }
}

# Define the request body model
class AgentRequest(BaseModel):
  user_input: str

# --- Mock APIs ---
@app.get("/bookings/{booking_id}")
def get_booking(booking_id: str, api_key: str = Header(...)):
  if booking_id not in mock_bookings:
    raise HTTPException(status_code=404, detail="Booking not found")
  return mock_bookings[booking_id]

@app.post("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: str, api_key: str = Header(...)):
  if booking_id not in mock_bookings:
    raise HTTPException(status_code=404, detail="Booking not found")
  mock_bookings[booking_id]["status"] = "cancelled"
  return {"message": "Cancellation successful"}

@app.post("/agent/v1")
def agent_invoke(request: AgentRequest, api_key: str = Header(...)):
  user_input = request.user_input

  initial_state = {
    "user_input": user_input,
    "api_key": "SECRET_KEY_123"
  }

  from customer_support.urgent_booking_changes.v1.graph import agent
  result = agent.invoke(initial_state)

  return {"message": str(result)}