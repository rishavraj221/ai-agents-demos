import os
from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Twilio configuration
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = Client(
    username=account_sid, 
    password=auth_token
)

@app.route("/make_call", methods=["POST"])
def make_call():
    """Initiate a call with the agent"""
    data = request.json
    to_number = data.get("to", "+919798600997")

    call = twilio_client.calls.create(
        url=f"{request.url_root}voice_webhook",
        to=to_number,
        from_=twilio_phone_number,
        record=True
    )

    return jsonify({"call_sid": call.sid, "status": call.status})

@app.route("/voice_webhook", methods=["GET"])
def voice_webhook():
    """Handle incoming voice calls and interactions"""
    response = VoiceResponse()
    call_sid = request.args.get('CallSid')

    response.say("Hello! I'm your AI assistant. Please speak after the beep. I'll be here to listen carefully for the next 10 seconds. Please go ahead.")

    response.record(
        max_length=10,
        action=f"/process_speech/{call_sid}",
        method="POST",
    )

    return str(response)

@app.route("/process_speech/<call_sid>", methods=["POST"])
def process_speech(call_sid):
    """Process recorded speech and generate response"""
    response = VoiceResponse()

    response.say("my beloved engineers are building me, soon i will be able to understand and answer your queries, thank you for your patience, but anyway please continue, i will listen you for another 10 seconds")

    response.record(
        max_length=10,
        action=f"/process_speech/{call_sid}",
        method="POST",
    )

    return str(response)
