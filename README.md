# AI Agents Agentic Demos using LangGraph

A demo codebase for building AI agentic flows to address real-world problems in customer support. This project demonstrates how to automate workflows using AI and mock APIs.

## Real-World Problems Addressed

1. **Urgent Booking Changes**  
   - Automate cancellations, rescheduling, and refunds.

2. **Payment Issues**  
   - Handle failed transactions and provide refund status updates.

3. **Itinerary Confusion**  
   - Resolve issues related to missing details, visa requirements, and baggage policies.

4. **API Integration**  
   - Securely access booking, payment, and support systems.

5. **Escalation Handling**  
   - Transfer complex issues to human agents when necessary.

---

## Project Structure

- **`customer_support/urgent_booking_changes/`**  
  Contains the implementation for handling urgent booking changes, including mock APIs, state management, and workflow orchestration.

- **`main.py`**  
  Entry point to start the mock server and expose APIs via ngrok.

- **`.env`**  
  Environment variables for API keys and ngrok authentication.

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Virtual environment (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rishavraj221/ai-agents-demos.git
   ```

2. Create and activate the virtual environment.
    ```bash
    uv new
    uv activate
    ```

3. Install dependencies:
    ```bash
    uv sync
    ```

4. Setup environment variables:
    - Copy `.env.example` to `.env` and fill in the required values.


### Running the project
Start the mock server
1. Run the server using `uvicorn`:
```bash
python main.py
```
2. The server will be exposed via ngrok. The public URL will be printed in the terminal.

### How to use
Workflow Demonstration
1. Navigate to `customer_support/urgent_booking_changes/notebook.ipynb` to explore the workflow and test cases.
2. Use the mock APIs to simulate booking changes:
    - GET `/bookings/{booking_id}`: Retrieve booking details.
    - POST `/bookings/{booking_id}/cancel`: Cancel a booking.
3. Use the POST `/agent` endpoint to initiate the agent by giving the `user_input` in request body.

### Contributing
Feel free to open issues or submit pull requests to improve the project.

### Licence
This project is licensed under the MIT Licence.