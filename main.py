from pyngrok import ngrok
import uvicorn
from customer_support.urgent_booking_changes.v1.mock_server import app

# Start server via ngrok (for Colab Compatibility)
ngrok_tunnel = ngrok.connect(8000)
print(f"API URL: {ngrok_tunnel.public_url}")

import nest_asyncio
nest_asyncio.apply()
uvicorn.run(app, host="0.0.0.0", port=8000)