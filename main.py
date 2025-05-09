# from pyngrok import ngrok
# import uvicorn
# from customer_support.urgent_booking_changes.v2.mock_server import app

# # Start server via ngrok (for Colab Compatibility)
# ngrok_tunnel = ngrok.connect(8000)
# print(f"API URL: {ngrok_tunnel.public_url}")

# import nest_asyncio
# nest_asyncio.apply()
# uvicorn.run(app, host="0.0.0.0", port=8000)

# from basic_chat_bot.v1.bot import stream_graph_updates
from basic_chat_bot.v3.bot import graph, stream_graph_updates

if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        ## Now let's interact with the bot. First, pick a thread to use as the key for this conversation.
        config = {"configurable": {"thread_id": "1"}}

        stream_graph_updates(graph, user_input, config)