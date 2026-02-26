# Quick Start Guide - AI Dental Receptionist

## Prerequisites
- Python 3.11+
- Node.js & npm
- pip (Python package manager)

## Installation & Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd /home/anandchoudhary/Documents/MVP_Project/ai-dental-receptionist/backend

# Install Python dependencies
pip install -r requirements.txt

# Verify .env file exists with required keys
cat .env
```

**Required .env variables:**
```
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
COMPANY_NAME=Bright Dental Clinic
SESSION_DURATION_SECONDS=120
```

### 2. Frontend Setup

```bash
# Navigate to project root
cd /home/anandchoudhary/Documents/MVP_Project

# Install Node dependencies
npm install

# Verify installation
npm list react vite tailwindcss
```

---

## Running the Project

### Start Backend Server

```bash
cd /home/anandchoudhary/Documents/MVP_Project/ai-dental-receptionist/backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Start Frontend Server

In a new terminal:

```bash
cd /home/anandchoudhary/Documents/MVP_Project
npm run dev
```

**Expected output:**
```
  VITE v5.4.21  ready in 416 ms
  ➜  Local:   http://localhost:3001/
```

---

## Access the Application

1. **Frontend:** http://localhost:3001
2. **API Docs:** http://localhost:8000/docs
3. **Backend Health:** http://localhost:8000/

---

## Using the Application

### Starting a Conversation

1. Click "Start Call with AI" button on the frontend
2. The app will:
   - Create a new session with the backend
   - Establish WebSocket connection
   - Display the AI's greeting message

### Messaging

1. Type your message in the input field
2. Click "Send" or press Enter
3. The message appears in the chat
4. AI response will appear automatically

### Available Intent Categories

The AI can help with:
- 🎯 **General Enquiries** - Questions about the clinic
- 💰 **Treatment Pricing** - Cost information
- 📅 **Booking Appointments** - Schedule new appointments
- 🔄 **Rescheduling Appointments** - Modify existing appointments

### Ending a Call

Click the "End Call" button to:
- Close WebSocket connection
- End the session
- Return to the initial screen

---

## Testing

### Run Full Flow Test

```bash
cd /home/anandchoudhary/Documents/MVP_Project
python test_full_flow.py
```

This will test:
- ✅ Health check endpoint
- ✅ Conversation start
- ✅ WebSocket connection
- ✅ API documentation
- ✅ Backend components

### Test Individual Endpoints

**Health Check:**
```bash
curl http://localhost:8000/
```

**Start Conversation:**
```bash
curl -X POST http://localhost:8000/conversation/start | python -m json.tool
```

---

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>
```

**Module import errors:**
```bash
# Ensure you're in the backend directory
cd ai-dental-receptionist/backend
python -m uvicorn app:app --reload
```

**Missing dependencies:**
```bash
pip install -r requirements.txt --upgrade
```

### Frontend Issues

**Port 3000/3001 in use:**
```bash
# The frontend automatically tries port 3001 if 3000 is in use
# Or kill the process
lsof -i :3000
kill -9 <PID>
```

**Node modules not installed:**
```bash
npm install
npm cache clean --force
npm install
```

**Vite build errors:**
```bash
npm run build
```

### WebSocket Connection Issues

**Check if backend is running:**
```bash
ps aux | grep uvicorn
```

**Check if frontend can reach backend:**
```bash
curl http://localhost:8000/
```

**Browser console errors:**
- Open browser DevTools (F12)
- Check Console tab for WebSocket errors
- Check Network tab for connection details

---

## API Reference

### REST Endpoints

#### Start Conversation
```
POST /conversation/start

Response:
{
  "session_id": "uuid-string",
  "message": "AI greeting message",
  "expires_at": "2026-01-28T..."
}
```

### WebSocket Endpoints

#### Stream Conversation
```
WS /conversation/stream/{session_id}

Send:
{
  "user_input": "User message here"
}

Receive:
{
  "response": "AI response here",
  "intent": "booking|pricing|enquiry|reschedule"
}
```

---

## Project Structure

```
MVP_Project/
├── ai-dental-receptionist/
│   └── backend/
│       ├── api/              # API endpoints
│       ├── core/             # Core logic
│       │   ├── conversation_manager.py
│       │   ├── intent_classifier.py
│       │   ├── response_router.py
│       │   └── stream_handler.py
│       ├── llm/              # LLM integration
│       │   ├── groq_client.py
│       │   ├── model_loader.py
│       │   └── prompt_templates.py
│       ├── rag/              # Vector search (FAISS)
│       │   ├── chunker.py
│       │   ├── retriever.py
│       │   ├── vector_store.py
│       │   └── clinic.index
│       ├── models/           # Data models
│       ├── utils/            # Utilities
│       ├── tools/            # Calendar integration
│       ├── app.py            # Main FastAPI app
│       ├── config.py         # Configuration
│       └── requirements.txt
├── src/                      # React frontend
│   ├── App.tsx
│   ├── components/
│   └── main.tsx
├── test_full_flow.py
├── TEST_REPORT.md
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

---

## Configuration

### Environment Variables

Create/update `.env` file in `backend/` directory:

```
# LLM Configuration
GROQ_API_KEY=your_api_key_here
GEMINI_API_KEY=your_api_key_here

# Clinic Configuration
COMPANY_NAME=Bright Dental Clinic

# Session Configuration
SESSION_DURATION_SECONDS=120
```

### Application Configuration

Edit `backend/config.py` to modify:
- Session duration
- Company name
- LLM parameters
- RAG settings

---

## Production Deployment

### Using Docker

Create `Dockerfile` in backend:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t ai-dental-receptionist .
docker run -p 8000:8000 --env-file .env ai-dental-receptionist
```

### Using PM2 (Node.js process manager)

```bash
# For backend
pm2 start "python -m uvicorn app:app --host 0.0.0.0 --port 8000" --name "backend"

# For frontend (build first)
npm run build
pm2 start "npm run preview" --name "frontend"
```

---

## Support & Resources

- **Backend Docs:** http://localhost:8000/docs
- **OpenAPI Schema:** http://localhost:8000/openapi.json
- **Test Script:** `python test_full_flow.py`
- **Troubleshooting:** See section above

---

**Last Updated:** 2026-01-28  
**Status:** ✅ Production Ready
