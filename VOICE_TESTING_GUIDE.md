# 🎙️ Voice Conversation Testing Guide

## Overview
The AI Dental Receptionist now features complete voice functionality:
- 🎤 **Speech-to-Text (STT)** - Your speech is automatically converted to text
- 🤖 **AI Processing** - Intent classification and response generation
- 🔊 **Text-to-Speech (TTS)** - AI responses are automatically spoken back

## System Features

### Speech Recognition
- **Continuous listening** while the microphone is active
- **Real-time transcription** with interim results
- **Automatic message sending** when transcription is complete
- **Manual send option** for text messages

### Voice Output
- **Automatic narration** of AI responses
- **Natural speech synthesis** with adjustable rate/pitch
- **Stop button** to interrupt speaking if needed

### Call Duration
- **2-minute conversations** (adjustable)
- **Live timer** showing remaining time
- **Auto-end** when time expires

---

## Getting Started

### Prerequisites
- Modern browser with Web Speech API support:
  - ✅ Chrome/Chromium
  - ✅ Edge
  - ✅ Firefox (limited)
  - ✅ Safari
- Microphone access (browser will request permission)
- Speakers for hearing AI responses

### Start the Application

**Terminal 1 - Backend:**
```bash
cd ai-dental-receptionist/backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /home/anandchoudhary/Documents/MVP_Project
npm run dev
```

**Open in Browser:**
```
http://localhost:3001
```

---

## Using Voice Features

### Starting a Voice Call

1. **Click "Start Voice Call (2 mins)" button**
2. Browser will ask for microphone permission - **Allow it**
3. AI greeting will be spoken automatically
4. Microphone will start listening automatically

### Speaking to the AI

1. **Speak clearly** into your microphone
2. Your speech appears in real-time as text
3. When you pause, the text is automatically sent
4. AI response is displayed and spoken back

### Example Conversation

```
You: "Hi, I'd like to book an appointment"
AI: "Sure! Here are the available slots..." (spoken)

You: "I want slot 2"
AI: "Your appointment is booked for..." (spoken)
```

### Manual Controls

**Microphone Button:**
- 🎤 **Start Listening** - Begin speech recognition
- 🎤❌ **Stop Listening** - Stop recording (if automatic failed)

**Send Text Button:**
- Use this if you want to type instead of speaking

**Stop Speaking Button:**
- Click to interrupt AI narration

**End Call Button:**
- Ends the session immediately
- Stops all speech (input/output)

---

## Speech Recognition Tips

### Best Practices
✅ Speak clearly and at normal pace
✅ Use natural pauses between sentences
✅ Speak complete sentences (ends with . ? !)
✅ Ensure no background noise
✅ Keep microphone close but not too close
✅ Use the manual "Send Text" if auto-send doesn't work

### Troubleshooting Speech Recognition

**"Microphone not working"**
- Check browser microphone permission
- Test microphone in browser settings
- Try a different browser
- Ensure microphone is not muted

**"Speech not being recognized"**
- Speak louder and more clearly
- Reduce background noise
- Check that browser tab is active
- Try manual send button instead

**"Transcript not appearing"**
- Click "Start Listening" button explicitly
- Wait 1-2 seconds after speaking to send
- Try typing manually instead

---

## Text-to-Speech Tips

### Best Practices
✅ Keep speakers at reasonable volume
✅ Ensure speakers are not muted
✅ Close other audio applications
✅ Patience for longer responses to be spoken

### Troubleshooting Text-to-Speech

**"No sound from AI responses"**
- Check volume levels (system and browser)
- Make sure speakers are enabled
- Try clicking "Stop Speaking" then listening again
- Check browser audio permissions

**"Sound too fast/slow"**
- TTS uses system default settings
- Some browsers allow rate adjustment
- Try different browser

**"Weird pronunciation"**
- Text-to-speech uses system voice
- Some names/medical terms may be mispronounced
- This is expected behavior

---

## Supported Intents (AI Can Help With)

1. **🎯 General Enquiries**
   - "Tell me about your services"
   - "What treatments do you offer?"
   - "Are you open on weekends?"

2. **💰 Treatment Pricing**
   - "How much does a checkup cost?"
   - "What's the price of teeth whitening?"
   - "Do you have packages?"

3. **📅 Booking Appointments**
   - "I'd like to book an appointment"
   - "Can I schedule a visit?"
   - "When are you available?"

4. **🔄 Rescheduling Appointments**
   - "I need to change my appointment"
   - "Can I reschedule my visit?"
   - "Move my appointment to another day"

---

## Voice Session Flow

```
1. Click "Start Voice Call"
   ↓
2. Microphone Permission → Allow
   ↓
3. AI Greeting Spoken
   ↓
4. Listening Starts Automatically
   ↓
5. You Speak → Speech Converted to Text
   ↓
6. Message Auto-Sent to Backend
   ↓
7. Backend Processes:
   • Classifies intent
   • Retrieves information
   • Generates response
   ↓
8. AI Response Spoken Automatically
   ↓
9. Listening Resumes
   ↓
10. Repeat Steps 5-9
    ↓
11. Timer Expires → Session Ends
```

---

## Conversation Examples

### Example 1: Enquiry
```
User: "Hi, what services do you offer?"
AI: "We offer comprehensive oral health care including laser dentistry, 
    teeth whitening, orthodontic treatments, and root canal treatment..."
User: "Tell me more about teeth whitening"
AI: "Our smile makeover service includes professional teeth whitening 
    using advanced laser systems..."
```

### Example 2: Booking
```
User: "I'd like to schedule an appointment"
AI: "Sure! Here are available slots: 1. Monday 10 AM, 2. Tuesday 2 PM, 
    3. Wednesday 11 AM. Please select a slot number."
User: "Slot 2"
AI: "Your appointment is booked for Tuesday at 2 PM. Anything else?"
```

### Example 3: Rescheduling
```
User: "I need to change my appointment"
AI: "No problem. Let me help you reschedule. What date would you prefer?"
User: "Thursday morning"
AI: "Your appointment has been rescheduled to Thursday at 10 AM."
```

---

## Timing & Performance

| Operation | Time |
|-----------|------|
| Speech Recognition Start | < 1 sec |
| Speech-to-Text Conversion | 1-2 sec |
| Backend Processing | 1-2 sec |
| Text-to-Speech Start | < 1 sec |
| Total Response Time | 3-5 sec |

---

## Browser Compatibility

| Browser | STT | TTS | Status |
|---------|-----|-----|--------|
| Chrome/Chromium | ✅ | ✅ | Fully Supported |
| Edge | ✅ | ✅ | Fully Supported |
| Safari | ⚠️ | ✅ | Limited STT |
| Firefox | ⚠️ | ✅ | Limited STT |

**Recommendation:** Use Chrome or Edge for best voice experience.

---

## Privacy & Data

- 🔐 **Local Processing**: Speech recognition runs locally in your browser
- 🔐 **Encrypted Transmission**: Audio text sent via secure WebSocket
- 🔐 **No Recording**: Conversations stored only in session (2 min expiry)
- 🔐 **Automatic Cleanup**: Session data deleted after expiration

---

## Advanced Features

### Manual Text Input
If speech recognition doesn't work:
1. Stay in call (don't close app)
2. Type your message in the text area
3. Click "Send Text" button
4. AI responds normally

### Interrupting AI
If AI is speaking and you want to interrupt:
1. Click "Stop Speaking" button
2. Your microphone remains active
3. You can continue the conversation

### Session Management
- Each call has unique Session ID
- Sessions expire after 2 minutes (default)
- Closing browser ends call immediately
- Clicking "End Call" terminates session

---

## Testing Checklist

- [ ] Microphone permission granted
- [ ] Speech-to-text working (hearing transcription)
- [ ] Text-to-speech working (hearing AI voice)
- [ ] Messages appearing in chat
- [ ] Timer counting down
- [ ] All intents being recognized
- [ ] Responses relevant to queries
- [ ] No audio conflicts/glitches
- [ ] 2-minute duration working
- [ ] Call ends properly

---

## Troubleshooting Flowchart

```
Voice not working?
├─ Check microphone permission
│  ├─ Not granted? Grant it
│  └─ Granted? Continue
├─ Check microphone is enabled
│  ├─ Disabled? Enable it
│  └─ Enabled? Continue
├─ Check speaker volume
│  ├─ Muted? Unmute it
│  └─ Not muted? Continue
├─ Check browser compatibility
│  ├─ Unsupported? Try Chrome
│  └─ Supported? Continue
└─ Try different browser/device
```

---

## Support & Issues

### Speech Recognition Not Working
1. Allow microphone permission
2. Check volume settings
3. Try different browser
4. Use manual text input as fallback

### Text-to-Speech Not Working
1. Check volume (system + app)
2. Unmute speakers
3. Try different browser
4. Check system audio settings

### Conversation Not Progressing
1. Ensure complete sentences (end with . ? !)
2. Use manual send button
3. Check internet connection
4. Check WebSocket connection status

### Backend Issues
1. Verify backend is running on port 8000
2. Check API endpoint: http://localhost:8000/docs
3. Review backend logs for errors
4. Restart backend server

---

## Performance Optimization

For best voice experience:
- Close unnecessary browser tabs
- Disable browser extensions that might interfere
- Ensure stable internet connection
- Use a quiet environment
- Use quality microphone
- Use Chrome/Edge browsers

---

**Last Updated:** January 28, 2026  
**Status:** ✅ Voice Features Enabled  
**Duration:** 2 minutes per call
