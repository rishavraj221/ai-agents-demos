# Voice Agent

## Overview (Technical)

This is a simple Twilio-based voice agent that initiates a call to a user, greets them, listens for 10-second intervals, and responds with a predefined message. This serves as foundation for building more complex voice AI applications.

## Architecture

```
[POST /make_call] → [Twilio Voice Webhook] → [Speech Processing Loop]
                     ↑                      ↓
              [Record Audio] ← [Response Generation]
```

## Key Components

### 1. Environment Setup

- Requires Twilio credentials:
  ```env
  TWILIO_ACCOUNT_SID=your_account_sid
  TWILIO_AUTH_TOKEN=your_auth_token
  TWILIO_PHONE_NUMBER=your_twilio_number
  ```

### 2. API Endpoints

#### POST `/make_call`

- Initiates phone call to specified number
- Parameters (JSON):
  ```json
  { "to": "+1234567890" }
  ```
- Response:
  ```json
  { "call_sid": "CA...", "status": "queued" }
  ```

#### GET `/voice_webhook`

- Initial call handler
- Plays greeting message
- Starts first 10-second recording

#### POST `/process_speech/<call_sid>`

- Loop handler for continuous interaction
- Responds with static message
- Re-initiates recording

## Call Flow

1. User triggers call via API
2. Twilio calls target number
3. System plays greeting
4. Records user speech for 10s
5. Responds with static message
6. Repeats steps 4-5 until call ends

## Setup Guide

```bash
# Install dependencies
pip install flask twilio python-dotenv

# Start server
FLASK_APP=app.py flask run --port=3000
```

## Usage Example

```bash
curl -X POST http://localhost:3000/make_call \\
  -H \"Content-Type: application/json\" \\
  -d '{\"to\": \"+1234567890\"}'
```

---

# Building a Basic Voice Agent

## Introduction

Today we're launching v1 of our voice agent - a simple but functional system demonstrating core voice interaction capabilities. This initial version focuses on establishing the fundamental call flow that future enhancements will build upon.

## How It Works

The system leverages Twilio's voice API with Flask backend to:

1. Initiate outbound calls
2. Handle voice interactions through webhooks
3. Maintain basic conversation loop

Key technical aspects:

- Uses TwiML for voice response configuration
- Implements continuous 10-second listening intervals
- Maintains call state through URL parameters
- Records all conversations automatically

## Limitations & Intent

While v1 uses static responses (\"...engineers are building me...\"), it establishes critical infrastructure for:

- Call initiation/management
- Audio recording handling
- Webhook integration pattern
- Basic conversation state management

---

# Contribution Guide

We welcome contributions following our phased approach:

1. Start with improving core call handling
2. Then enhance NLP capabilities
3. Followed by integration patterns
4. Finally work on scalability/security

This phased approach allows gradual complexity while maintaining working system at each stage. Each version builds on previous foundation, enabling collaborative development without disrupting core functionality.
