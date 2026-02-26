# 🎙️ Voice Conversation Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Web Speech API                              │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ SpeechRecognition (STT)      SpeechSynthesis (TTS)  │  │
│  │ • Continuous listening       • Auto-narration       │  │
│  │ • Real-time transcription    • Adjustable rate      │  │
│  │ • Auto send on sentence end  • Stop controls        │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↕ WebSocket                        │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Stream Handler (WebSocket)                    │  │
│  │                                                      │  │
│  │  1. Receive text message                            │  │
│  │  2. Parse JSON payload                              │  │
│  │  3. Buffer until sentence complete                  │  │
│  │  4. Route to Intent Classifier                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Intent Classifier (Groq LLM)                 │  │
│  │  • Booking                                           │  │
│  │  • Pricing/Enquiry                                   │  │
│  │  • Rescheduling                                      │  │
│  │  • Greetings                                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Response Router                               │  │
│  │  ├─ Enquiry/Pricing → RAG Pipeline (FAISS)          │  │
│  │  ├─ Booking → Google Calendar                        │  │
│  │  ├─ Rescheduling → Calendar Modification            │  │
│  │  └─ Greetings → Direct Response                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Response Generation                           │  │
│  │  • Format response text                              │  │
│  │  • Add context/suggestions                           │  │
│  │  • Return to frontend                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↕ WebSocket (JSON)                │
└─────────────────────────────────────────────────────────────┘
                          ↕
                    Frontend (React)
                    • Display response
                    • Speak via TTS
                    • Resume listening
```

## Component Details

### Frontend: Speech-to-Text (STT)

**Technology:** Web Speech API (SpeechRecognition)

**Flow:**
```
1. User clicks "Start Listening"
   ↓
2. Microphone stream starts
   ↓
3. Real-time transcription
   ├─ Interim results: Appear as user types
   └─ Final results: Added to transcript buffer
   ↓
4. Sentence detection (ends with . ? !)
   ↓
5. Auto-send to backend via WebSocket
   ↓
6. Resume listening for next input
```

**Code Location:** `src/App.tsx`
- `recognitionRef.current` - SpeechRecognition instance
- `startListening()` - Activate microphone
- `stopListening()` - Deactivate microphone
- `transcript` - Stores final text

### Frontend: Text-to-Speech (TTS)

**Technology:** Web Speech API (SpeechSynthesis)

**Flow:**
```
1. Receive response from backend
   ↓
2. Create utterance with response text
   ↓
3. Configure speech rate, pitch, volume
   ↓
4. Play audio to speakers
   ↓
5. Set isSpeaking state
   ↓
6. Resume listening when done
```

**Code Location:** `src/App.tsx`
- `speakText(text)` - Text-to-speech function
- `synthRef.current` - SpeechSynthesisUtterance instance
- `isSpeaking` - State indicator

### Backend: Stream Handler

**Technology:** FastAPI WebSocket

**File:** `ai-dental-receptionist/backend/core/stream_handler.py`

**Process:**
```
1. Accept WebSocket connection
   ↓
2. Parse incoming message (JSON)
   ↓
3. Extract user_input
   ↓
4. Buffer until complete sentence
   ↓
5. Send to Intent Classifier
   ↓
6. Route based on intent
   ↓
7. Generate response
   ↓
8. Send JSON back to frontend
   ↓
9. Loop for next message
```

**JSON Format:**

Request (Frontend → Backend):
```json
{
  "user_input": "I'd like to book an appointment"
}
```

Response (Backend → Frontend):
```json
{
  "response": "Sure! Here are the available slots...",
  "intent": "booking",
  "session_id": "uuid-string"
}
```

## Data Flow Sequence

### Initial Connection
```
Frontend                          Backend
   │                                 │
   ├─ POST /conversation/start ─────>│
   │                                 │
   │<────── Session + Greeting ──────┤
   │                                 │
   ├─ Speak greeting ✓               │
   │                                 │
   ├─ WS /stream/session_id ─────────>│
   │                                 │
   │<────── Connected ✓ ─────────────┤
   │                                 │
   └─ Start listening ✓              │
```

### Message Exchange
```
Frontend                          Backend
   │                                 │
   │ (User speaks) ✓                 │
   ├─ STT: Convert to text           │
   ├─ {"user_input": "..."} ────────>│
   │                                 │
   │                                 ├─ Parse message
   │                                 ├─ Classify intent
   │                                 ├─ Route to handler
   │                                 ├─ Generate response
   │                                 │
   │<────── {"response": "..."} ─────┤
   │                                 │
   ├─ TTS: Speak response            │
   ├─ Display in chat                │
   ├─ Resume listening ✓             │
   │                                 │
```

### Call Termination
```
Frontend                          Backend
   │                                 │
   │ (2 minutes elapsed)             │
   ├─ Stop recording                 │
   ├─ Close WebSocket ───────────────>│
   │                                 │
   │                                 ├─ Cleanup session
   │                                 ├─ Delete temp data
   │                                 │
   │ (App returns to home screen)    │
   │                                 │
```

## State Management

### Frontend States
```javascript
// Audio States
isListening    // Mic active?
isSpeaking     // AI speaking?
transcript     // Final speech-to-text
userInput      // Current message text

// Session States
isCallActive   // Call in progress?
sessionId      // Current session UUID
messages       // Chat history
timeRemaining  // Call timer

// Connection States
wsConnection   // WebSocket instance
isLoading      // Processing response?
```

### Backend States
```python
# Session State
session.session_id
session.messages        # Chat history
session.expires_at
session.booking_state   # Booking progress
session.reschedule_state

# Processing State
buffer          # Message buffer
intent          # Current intent
response        # Generated response
```

## Error Handling

### Frontend Errors

**Microphone Not Available:**
```javascript
if (!navigator.mediaDevices?.getUserMedia) {
  // Fallback to text input
}
```

**Speech Recognition Error:**
```javascript
recognitionRef.current.onerror = (event) => {
  console.error('STT Error:', event.error);
  // Allow manual text input
};
```

**WebSocket Disconnection:**
```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Show reconnect button
};
```

### Backend Errors

**Invalid Message Format:**
```python
try:
    message_data = json.loads(data)
except json.JSONDecodeError:
    # Treat as plain text
    user_input = data.strip()
```

**Session Expired:**
```python
session = get_session(session_id)
if not session:
    await websocket.close()
```

**Processing Timeout:**
```python
try:
    response = await route_intent(...)
except Exception as e:
    return f"Error processing request: {str(e)}"
```

## Performance Metrics

| Operation | Time | Target |
|-----------|------|--------|
| Speech recognition start | 500ms | < 1s |
| STT response | 1-2s | < 3s |
| Intent classification | 800ms | < 2s |
| Response generation | 1-2s | < 3s |
| TTS start | 200ms | < 1s |
| Total latency | 4-8s | < 10s |

## Browser Compatibility

### Speech Recognition (STT)
- ✅ Chrome 25+
- ✅ Edge 79+
- ⚠️ Firefox 44+ (experimental)
- ⚠️ Safari 14.1+

### Speech Synthesis (TTS)
- ✅ Chrome 33+
- ✅ Edge 12+
- ✅ Firefox 49+
- ✅ Safari 7+

### WebSocket
- ✅ All modern browsers

## Security Considerations

1. **Microphone Permission**
   - Explicitly requested
   - User can revoke anytime
   - Only active during call

2. **Data Transmission**
   - WebSocket over HTTPS (secure)
   - Text only (no audio files)
   - Session expires in 2 minutes

3. **Local Processing**
   - STT runs locally in browser
   - No voice data sent to server
   - Only text transcription transmitted

4. **Session Management**
   - Unique session ID per call
   - Automatic cleanup on expiry
   - No persistent storage

## Configuration

### Frontend
- File: `src/App.tsx`
- Duration: Line with `CALL_DURATION = 120`
- Speech rate: `utterance.rate = 1`
- Pitch: `utterance.pitch = 1`
- Volume: `utterance.volume = 1`

### Backend
- File: `backend/core/stream_handler.py`
- Sentence detection: `endswith((".", "?", "!"))`
- Buffer threshold: `len(buffer.strip()) > 50`
- Session duration: `backend/config.py` (SESSION_DURATION_SECONDS)

## Testing Strategy

1. **Unit Tests**
   - STT functionality
   - TTS functionality
   - Intent classification
   - Response routing

2. **Integration Tests**
   - Full voice conversation flow
   - WebSocket messaging
   - Session management
   - Error recovery

3. **User Tests**
   - Microphone input quality
   - Voice clarity
   - Response timing
   - UI/UX flow

## Future Enhancements

- [ ] Support for multiple languages
- [ ] Speaker identification
- [ ] Emotion detection
- [ ] Voice customization
- [ ] Call recording (with consent)
- [ ] Advanced noise cancellation
- [ ] Real-time transcript display
- [ ] Voice commands for UI control

---

**Created:** January 28, 2026  
**Version:** 1.0  
**Status:** Production Ready
