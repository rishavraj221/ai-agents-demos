from voice_chat.v1.agent import twilio_client, twilio_phone_number, account_sid, auth_token
from flask import Flask, request, jsonify
from twilio.rest import Client
from langchain_core.messages import AIMessage
from twilio.twiml.voice_response import VoiceResponse, Gather
from voice_chat.v2.bot import graph, stream_graph_updates

app = Flask(__name__)

SILENCE_TIMEOUT = 1.5
MAX_RECORDING_LENGTH = 30

@app.route("/make_call", methods=["GET", "POST"])
def make_call():
    """Initiate a call with the agent"""
    to_number = request.values.get("to", "+919798600997")

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

    response.say("Hi Rishav! What's up? Great to see you back! What can I help you with?")

    gather = Gather(
        input='speech',
        timeout=SILENCE_TIMEOUT,
        speech_timeout='auto',
        action=f"/process_speech_gather/{call_sid}",
        method="POST",
        language="en-US",
        enhanced=True,
        speech_model='phone_call'
    )

    gather.say("Please speak now...")
    response.append(gather)

    # Fallback if no speech detected
    response.say("I didn't hear anything. Let me try recording instead.")
    response.redirect(f"/fallback_record/{call_sid}")

    return str(response)

@app.route("/process_speech_gather/<call_sid>", methods=["POST"])
def process_speech_gather(call_sid):
    """Process speech from Gather (real-time transcription)"""
    response = VoiceResponse()

    # Get the transcription from Gather
    speech_result = request.values.get('SpeechResult')
    confidence = request.values.get('Confidence')

    print(f"Transcription: {speech_result}")
    print(f"Confidence: {confidence}")

    if speech_result:

        config = {"configurable": {"thread_id": call_sid}}

        for event in graph.stream({"messages": [{"role": "user", "content": speech_result}]}, config):
            for value in event.values():
                message = value["messages"][-1]

                tool_calls = message.additional_kwargs.get('tool_calls', [])

                if len(tool_calls) > 0 and tool_calls[0].get('function', {}).get('name', '') == 'tavily_search':
                    print(f"Tool Call: {tool_calls[0]}")
                    pass # handle when tool call is there     
                elif isinstance(message, AIMessage) and message.content:
                    print(f"Agent Response: {message.content}")
                    response.say(message.content)

        # Continue the conversation
        gather = Gather(
            input="speech",
            timeout=SILENCE_TIMEOUT,
            speech_timeout='auto',
            action=f"/process_speech_gather/{call_sid}",
            method="POST",
            language="en-US",
            enhanced=True,
            speech_model="phone_call"
        )
        gather.say("Please continue speaking...")
        response.append(gather)
    
    else:
        response.say("I couldn't understand what you said. Please try again.")
        response.redirect(f"/voice_webhook?CallSid={call_sid}")
    
    return str(response)


@app.route("/fallback_record/<call_sid>", methods=["GET"])
def fallback_record(call_sid):
    """Fallback to recording if Gather fails"""
    response = VoiceResponse()

    response.record(
        max_length=MAX_RECORDING_LENGTH,
        timeout=SILENCE_TIMEOUT,
        action=f"/process_speech_record/{call_sid}",
        method="POST",
        play_beep=True,
        trim="trim-silence",
        transcribe=True,
        transcribe_callback=f"/transcription_callback/{call_sid}"
    )

    return str(response)

@app.route("/process_speech_record/<call_sid>", methods=["POST"])
def process_speech_record(call_sid):
    """Process recorded speech (transcription comes via callback)"""
    response = VoiceResponse()

    recording_url = request.values.get("RecordingUrl")
    recording_duration = request.values.get('RecordingDuration')

    print(f"Recording URL: {recording_url}")
    print(f"Recording Duration: {recording_duration} seconds")

    response.say("Thank you for speaking. I'm processing what you said and will respond soon.")

    # The transcription will come via the callback, so we wait or continue
    response.record(
        max_length=MAX_RECORDING_LENGTH,
        timeout=SILENCE_TIMEOUT,
        action=f"/process_speech_record/{call_sid}",
        method="POST",
        play_beep=True,
        trim="trim-silence",
        transcribe=True,
        transcribe_callback=f"/transcription_callback/{call_sid}"
    )

    return str(response)

@app.route("/transcription_callback/<call_sid>", methods=["POST"])
def transcription_callback(call_sid):
    """Handle transcription results from recordings"""
    transcription_text = request.values.get('TranscriptionText')
    transcription_status = request.values.get('TranscriptionStatus')
    recording_url = request.values.get('RecordingUrl')

    print(f"Call {call_sid} - Transcription: {transcription_text}")
    print(f"Transcription Status: {transcription_status}")

    # Store or process the transcription
    # You can save to database, send to AI model, etc.

    if transcription_text:
        # Here you can integrate with your AI model
        # ai_response = process_with_ai_model(transcription_text)

        # For now, just log it
        print(f"User said: {transcription_text}")

    return "", 200