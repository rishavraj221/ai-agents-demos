from customer_support.urgent_booking_changes.graph import agent
from customer_support.urgent_booking_changes.mock_server import mock_bookings

#########################################################################################
### Test Case 1

initial_state = {
    "user_input": "Urgent! Cancel my booking BOOKING123",
    "api_key": "SECRET_KEY_123"
}

result = agent.invoke(initial_state)
print("Final State:", result)
print("Booking Status:", mock_bookings["BOOKING123"]["status"]) # Should be "cancelled"
#########################################################################################