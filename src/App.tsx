

import { useState, useEffect, useRef } from 'react';
import { Phone, PhoneOff, Send, Mic, MicOff, Volume2 } from 'lucide-react';


type Page = 'FORM' | 'INTRO' | 'CALL';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const isSpeakingRef = useRef(false);
  const CALL_DURATION = 120;
  // const BACKEND_URL = 'http://localhost:8000';
  // const BACKEND_URL = 'http://192.168.1.9:8000';
  const BACKEND_URL = "https://somniferous-unpursued-lin.ngrok-free.dev";

  const transcriptBufferRef = useRef('');
  const [isQueued, setIsQueued] = useState(false);



  const [page, setPage] = useState<Page>("FORM");
  const [isCallActive, setIsCallActive] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(CALL_DURATION);
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const wsConnectionRef = useRef<WebSocket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Speech Recognition states
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesisUtterance | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSpeechTimeRef = useRef<number>(0);
  const isCallActiveRef = useRef(false);
  const isListeningRef = useRef(false);
  const lastSentPartialRef = useRef<string>("");
  const partialThrottleTimerRef = useRef<number | null>(null);


  useEffect(() => {
    const loadVoices = () => {
      window.speechSynthesis.getVoices();
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }, []);


  useEffect(() => {
    window.speechSynthesis.getVoices();
  }, []);


  useEffect(() => {
    const checkHindiVoice = () => {
      const voices = window.speechSynthesis.getVoices();

      if (!voices.length) return;

      const hasHindi = voices.some(
        v => v.lang === "hi-IN" || v.name.toLowerCase().includes("hindi")
      );

      if (!hasHindi) {
        alert(
          "⚠️ Hindi voice not found.\n\n" +
          "For best experience, please enable Hindi voice in your device settings.\n\n" +
          "📱 Android:\n" +
          "Settings → Language & Input → Text-to-Speech → Install Hindi\n\n" +
          "💻 Windows:\n" +
          "Settings → Time & Language → Speech → Add Hindi voice\n\n" +
          
          "Then refresh this page."
        );
      }
    };

    window.speechSynthesis.onvoiceschanged = checkHindiVoice;
    checkHindiVoice();
  }, []);



  // TEMP DEBUG (remove later)
  useEffect(() => {
    const int = setInterval(() => {
      console.debug("DBG: speaking:", isSpeakingRef.current, "listening:", isListeningRef.current, "processing:", isProcessing);
    }, 2000);
    return () => clearInterval(int);
  }, []);

  useEffect(() => {
    const checkVoices = () => {
      const voices = window.speechSynthesis.getVoices();

      if (!voices.length) return;

      const hindiExists = voices.some(
        v => v.lang === "hi-IN" || v.name.toLowerCase().includes("hindi")
      );

      if (!hindiExists) {
        alert(
          "For better Indian accent, please install Hindi voice in your device.\n\n" +
          "Android:\nSettings → Language → Text-to-Speech → Install Hindi\n\n" +
          "Windows:\nSettings → Time & Language → Speech → Add Hindi voice\n\n" +
          "Mac:\nSystem Settings → Accessibility → Spoken Content → Voices → Hindi"
        );
      }
    };

    // voices load async
    window.speechSynthesis.onvoiceschanged = checkVoices;
    checkVoices();
  }, []);




  const ensureMicPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (err) {
      alert("Microphone permission is required to talk with the AI receptionist.");
      return false;
    }
  };


  const [lastBooking, setLastBooking] = useState<{
    date: string;
    time: string;
  } | null>(null);

  // user profile stored locally and passed to backend
  const [userProfile, setUserProfile] = useState<{
    name?: string;
    phone?: string;
    email?: string;
  } | null>(null);

  // form field local states (for controlled inputs in FORM page)
  const [formName, setFormName] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [formEmail, setFormEmail] = useState("");



  useEffect(() => {
    const stored = localStorage.getItem("userProfile");
    const storedTime = localStorage.getItem("userProfileTime");

    if (!stored || !storedTime) {
      setPage("FORM");
      return;
    }

    const age = Date.now() - Number(storedTime);
    const oneDay = 24 * 60 * 60 * 1000;

    if (age > oneDay) {
      localStorage.removeItem("userProfile");
      localStorage.removeItem("userProfileTime");
      setPage("FORM");
      return;
    }

    // profile valid
    const profile = JSON.parse(stored);
    setUserProfile(profile);
    setPage("INTRO");
  }, []);





  // Scroll to bottom of messages
  // ======================= SPEECH RECOGNITION =======================
  // ---------- SPEECH RECOGNITION SETUP (replace your useEffect) ----------
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("SpeechRecognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-IN";
    recognition.maxAlternatives = 1;

    recognitionRef.current = recognition;

    recognition.onstart = () => {
      console.log("🎤 Speech recognition started");
      isListeningRef.current = true;
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      if (isProcessing || isSpeakingRef.current) return;

      let interim = "";
      let finalChunk = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalChunk += text + " ";
        } else {
          interim += text;
        }
      }

      if (interim) setUserInput(interim);

      if (finalChunk) {
        transcriptBufferRef.current += finalChunk.trim() + " ";
        lastSpeechTimeRef.current = Date.now();

        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
        }

        silenceTimerRef.current = setTimeout(() => {
          autoSendTranscript();
        }, 1500);
      }
    };

    recognition.onerror = (event: any) => {
      console.warn("🎤 Speech recognition error:", event.error);

      isListeningRef.current = false;
      setIsListening(false);

      // 🚨 DO NOT restart on aborted
      if (event.error === "no-speech") {
        setTimeout(() => {
          if (!isSpeakingRef.current && isCallActiveRef.current) {
            startListening();
          }
        }, 800);
      }
    };


    recognition.onend = () => {
      console.log("🎤 Speech recognition ended");

      isListeningRef.current = false;
      setIsListening(false);

      if (isSpeakingRef.current || isProcessing) return;

      if (window.speechSynthesis.speaking) return;

      if (
        isCallActiveRef.current &&
        wsConnectionRef.current &&
        wsConnectionRef.current.readyState === WebSocket.OPEN
      ) {
        setTimeout(() => {
          if (!isSpeakingRef.current && !isProcessing && !window.speechSynthesis.speaking) {
            startListening();
          }
        }, 2200);
      }
    };


    return () => {
      try { recognition.stop(); } catch { }
      recognitionRef.current = null;
    };
  }, [isProcessing]); // note: depends on isProcessing only



  // ======================= CALL TIMER =======================
  useEffect(() => {
    if (!isCallActive) return;

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          console.log("⏰ Call time expired - ending call");
          endCall();
          return CALL_DURATION;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isCallActive]);


  const hasHindiVoice = () => {
    const voices = window.speechSynthesis.getVoices();
    return voices.some(
      v =>
        v.lang === "hi-IN" ||
        v.name.toLowerCase().includes("hindi")
    );
  };


  // ======================= TEXT TO SPEECH =======================
  const speakText = (text: string) => {
    if (!text) return;

    console.log("🗣️ SPEAKING:", text);

    // Stop mic first
    try { recognitionRef.current?.abort(); } catch { }
    isListeningRef.current = false;
    setIsListening(false);

    // Stop any existing speech
    try {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
    } catch { }

    const utterance = new SpeechSynthesisUtterance(text);

    // =========================
    // 🎙️ FORCE HINDI ACCENT FIRST
    // =========================
    const voices = window.speechSynthesis.getVoices();

    let selectedVoice =
      // PRIMARY: Hindi voices
      voices.find(v => v.lang === "hi-IN") ||
      voices.find(v => v.name.toLowerCase().includes("hindi")) ||

      // SECONDARY: Indian English voices
      voices.find(v => v.name.includes("Ravi")) ||
      voices.find(v => v.lang === "en-IN") ||

      // FALLBACK ONLY if Hindi not available
      voices.find(v => v.lang === "en-GB") ||
      voices.find(v => v.lang === "en-US") ||
      voices[0];

    if (selectedVoice) {
      utterance.voice = selectedVoice;

      // Force language to match accent
      if (selectedVoice.lang === "hi-IN") {
        utterance.lang = "hi-IN";
      } else {
        utterance.lang = "en-IN";
      }

      console.log("🎙️ Using voice:", selectedVoice.name, selectedVoice.lang);
    }

    // =========================
    // 🧠 HUMAN-LIKE SPEED TUNING
    // =========================
    const lower = text.toLowerCase();

    let rate = 1.18;
    let pitch = 1.02;

    if (lower.includes("namaste") || lower.includes("hello")) {
      rate = 0.95;
      pitch = 1.08;
    }
    else if (lower.includes("booked") || lower.includes("confirm")) {
      rate = 1.0;
      pitch = 1.12;
    }
    else if (text.includes("?")) {
      rate = 0.96;
      pitch = 1.05;
    }
    else if (lower.includes("sorry")) {
      rate = 0.9;
      pitch = 0.98;
    }

    // Micro-variation for realism
    rate += (Math.random() * 0.04 - 0.02);
    pitch += (Math.random() * 0.05 - 0.02);

    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = 1;

    // =========================
    // ⏸️ NATURAL PAUSES
    // =========================
    utterance.text = text
      .replace(/,/g, ", ")
      .replace(/\./g, "... ")
      .replace(/\?/g, "? ")
      .replace(/!/g, "! ");

    // =========================
    // SPEECH EVENTS
    // =========================
    utterance.onstart = () => {
      isSpeakingRef.current = true;
      setIsSpeaking(true);

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
    };

    utterance.onend = () => {
      isSpeakingRef.current = false;
      setIsSpeaking(false);

      setTimeout(() => {
        if (
          isCallActiveRef.current &&
          !isListeningRef.current &&
          !isProcessing &&
          wsConnectionRef.current &&
          wsConnectionRef.current.readyState === WebSocket.OPEN
        ) {
          startListening();
        }
      }, 500);
    };

    utterance.onerror = () => {
      isSpeakingRef.current = false;
      setIsSpeaking(false);
    };

    setTimeout(() => {
      window.speechSynthesis.speak(utterance);
    }, 120);
  };






  // ======================= AUTO SEND TRANSCRIPT =======================
  const autoSendTranscript = () => {
    const text = transcriptBufferRef.current.trim();
    if (!text) return;

    const ws = wsConnectionRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    const raw = localStorage.getItem("userProfile");
    const profile = raw ? JSON.parse(raw) : {};

    const payload = {
      user_input: text,
      user_profile: {
        name: profile?.name || "Guest",
        phone: profile?.phone || null,
        email: profile?.email || ""
      }
    };

    console.log("🚀 SENDING PAYLOAD:", payload);

    ws.send(JSON.stringify(payload));

    setMessages(prev => [...prev, { role: "user", content: text }]);

    transcriptBufferRef.current = "";
    setUserInput("");
    setIsProcessing(true);
  };



  // ======================= LISTENING CONTROLS =======================
  // ---------- LISTENING CONTROLS (replace startListening / stopListening) ----------
  const startListening = () => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    // Critical guards: do not start if already listening, speaking, processing, or not connected
    if (
      isListeningRef.current ||
      isSpeakingRef.current ||
      isProcessing ||
      !isCallActiveRef.current ||
      !wsConnectionRef.current ||
      wsConnectionRef.current.readyState !== WebSocket.OPEN
    ) {
      return;
    }

    try {
      recognition.start();
      console.log("🎤 Speech recognition start requested");
    } catch (e) {
      console.warn("recognition.start() failed", e);
    }
  };


  const stopListening = () => {
    if (recognitionRef.current && isListeningRef.current) {
      try {
        recognitionRef.current.stop();
      } catch { }
    }
  };


  // ======================= START CALL =======================
  // ---------- START CALL (replace your startCall function) ----------
  const startCall = async () => {
    console.log("📞 Starting call...");

    const allowed = await ensureMicPermission();
    if (!allowed) return;

    if (isCallActiveRef.current) return;

    setPage("CALL");
    setError(null);
    setConnectionStatus("connecting");
    setMessages([]);
    setIsProcessing(false);

    const WS_URL = `${BACKEND_URL.replace(/^http/, "ws")}/conversation/stream`;

    const ws = new WebSocket(WS_URL);
    wsConnectionRef.current = ws;

    ws.onopen = () => {
      console.log("🟢 WS connected. Waiting for agent...");
    };

    ws.onmessage = (event) => {
      let res: any = null;
      try {
        res = JSON.parse(event.data);
      } catch (e) {
        console.warn("Failed to parse WS message", e, event.data);
        return;
      }

      console.log("WS:", res);

      // =========================
      // 🟡 BUSY / QUEUE SIGNAL
      // =========================
      if (res?.type === "busy") {
        console.log("⏳ Agent busy — added to queue");
        setIsQueued(true);
        setConnectionStatus("connecting");
        return;
      }

      // =========================
      // 🟢 START SIGNAL (PROMOTED FROM QUEUE OR DIRECT CONNECT)
      // =========================
      if (res?.type === "start") {
        console.log("🚀 Agent ready");

        setIsQueued(false); // <-- important
        setConnectionStatus("connected");
        isCallActiveRef.current = true;
        setIsCallActive(true);
        setTimeRemaining(CALL_DURATION);

        const intro =
          "Namaste ji! Main Bright Dental Clinic ki AI receptionist bol rahi hoon. Hanji, batayiye — appointment book karna hai, reschedule karna hai, ya koi information chahiye?";

        try { recognitionRef.current?.abort(); } catch { }
        isListeningRef.current = false;
        setIsListening(false);

        setMessages([{ role: "assistant", content: intro }]);
        speakText(intro);
        return;
      }

      // =========================
      // NORMAL RESPONSE FLOW
      // =========================
      setIsProcessing(false);

      let textToSpeak: string | null = null;
      const payload = res?.response ?? null;

      if (typeof payload === "string" && payload.trim()) {
        textToSpeak = payload;
      } else if (payload && typeof payload === "object") {
        if (typeof payload.message === "string" && payload.message.trim()) {
          textToSpeak = payload.message;
        } else if (typeof payload.text === "string" && payload.text.trim()) {
          textToSpeak = payload.text;
        } else if (typeof payload.reply === "string" && payload.reply.trim()) {
          textToSpeak = payload.reply;
        } else if (typeof payload.answer === "string" && payload.answer.trim()) {
          textToSpeak = payload.answer;
        }
      } else if (typeof res?.message === "string") {
        textToSpeak = res.message;
      }

      if (!textToSpeak) {
        console.log("⚠️ No speakable text found in WS payload:", res);
        return;
      }

      // Save booking info if present
      try {
        if (payload && payload.booking) {
          setLastBooking(payload.booking);
        }
      } catch { }

      try { recognitionRef.current?.abort(); } catch { }
      isListeningRef.current = false;
      setIsListening(false);

      setMessages(prev => [
        ...prev,
        { role: "assistant", content: textToSpeak! }
      ]);

      console.log("🗣️ SPEAKING:", textToSpeak);
      if (isSpeakingRef.current) return;

      speakText(textToSpeak);
    };

    ws.onerror = () => {
      setConnectionStatus("error");
      setError("Connection error.");
    };

    ws.onclose = () => {
      console.log("🟡 WS closed");
      wsConnectionRef.current = null;
      isCallActiveRef.current = false;
      setIsCallActive(false);

      // Ensure recognition is stopped
      try { recognitionRef.current?.abort(); } catch { }
      isListeningRef.current = false;
      setIsListening(false);
    };
  };




  // ======================= END CALL =======================

  const endCall = () => {
    console.log("📞 Ending call...");

    if (!isCallActiveRef.current) return;

    isCallActiveRef.current = false;
    setIsCallActive(false);

    try { stopListening(); } catch { }
    try { window.speechSynthesis.cancel(); } catch { }

    if (wsConnectionRef.current) {
      try { wsConnectionRef.current.close(); } catch { }
      wsConnectionRef.current = null;
    }

    // ❌ DO NOT touch messages here
    // ❌ DO NOT reset booking state

    setUserInput("");
    setIsListening(false);
    setIsSpeaking(false);
    setIsProcessing(false);
    setConnectionStatus("idle");

    setPage("INTRO"); // ✅ correct
    console.log("✅ Call ended cleanly");
  };



  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-black flex items-center justify-center p-4">

      {/* PAGE 0 — FORM */}
      {page === 'FORM' && (
        <div className="flex flex-col items-center gap-6 max-w-md w-full">
          <h1 className="text-4xl font-semibold text-white">Welcome to Bright Dental Clinic</h1>

          <p className="text-gray-300 text-center">
            Please enter your details so we can create your booking and identify you for reschedules.
          </p>

          <input
            type="text"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
            placeholder="Full Name"
            className="w-full px-4 py-3 rounded bg-slate-800 text-white"
          />

          <input
            type="tel"
            value={formPhone}
            onChange={(e) => setFormPhone(e.target.value)}
            placeholder="Phone Number"
            className="w-full px-4 py-3 rounded bg-slate-800 text-white mt-2"
          />

          <input
            type="email"
            value={formEmail}
            onChange={(e) => setFormEmail(e.target.value)}
            placeholder="Email (optional)"
            className="w-full px-4 py-3 rounded bg-slate-800 text-white mt-2"
          />

          <div className="flex gap-3 mt-4">
            <button
              className="px-6 py-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white font-semibold"


              onClick={async () => {
                if (!formName.trim() || !formPhone.trim()) {
                  alert("Please enter name and phone.");
                  return;
                }

                const profile = {
                  name: formName.trim(),
                  phone: formPhone.trim(),
                  email: formEmail.trim() || ""
                };

                localStorage.setItem("userProfile", JSON.stringify(profile));
                localStorage.setItem("userProfileTime", Date.now().toString());
                setUserProfile(profile);

                try {
                  const res = await fetch(`${BACKEND_URL}/store-profile`, {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json"
                    },
                    body: JSON.stringify(profile)
                  });

                  await res.json();

                  console.log("✅ PROFILE STORED ON BACKEND");

                  // ONLY NOW move to intro
                  setPage("INTRO");

                } catch (err) {
                  console.error("❌ Failed to store profile:", err);
                  alert("Network error. Please try again.");
                }
              }}




            >
              Continue
            </button>

            <button
              className="px-6 py-3 rounded-full bg-gray-600 hover:bg-gray-700 text-white font-semibold"
              onClick={() => {
                // clear and remain on form
                setFormName("");
                setFormPhone("");
                setFormEmail("");
              }}
            >
              Clear
            </button>
          </div>
        </div>
      )}



      {/* PAGE 1 — INTRO */}
      {page === 'INTRO' && (
        <div className="flex flex-col items-center gap-8">
          <h1 className="text-5xl font-semibold text-white">
            AI Dental Receptionist
          </h1>

          <p className="text-xl text-gray-300 text-center max-w-md">
            Welcome to Bright Dental Clinic. Click below to start a voice
            conversation with our AI receptionist.
          </p>

          <button
            onClick={startCall}
            className="px-8 py-4 rounded-full text-lg flex items-center gap-3 
                       bg-blue-500 hover:bg-blue-600 text-white font-semibold transition"
          >
            <Phone />
            Start Voice Call (2 mins)
          </button>

          {lastBooking && (
            <div className="mt-6 p-4 rounded-lg bg-green-600/20 border border-green-500 max-w-md text-center">
              <p className="text-green-400 font-semibold">
                ✅ Appointment Confirmed
              </p>
              <p className="text-green-300 mt-1">
                {lastBooking.date} at {lastBooking.time}
              </p>
            </div>
          )}


        </div>
      )}

      {/* PAGE 2 — CALL */}
      {page === 'CALL' && (
        <div className="w-full max-w-2xl flex flex-col gap-4">

          {isQueued && (
            <div className="bg-yellow-600/20 border border-yellow-500 rounded-lg p-3 text-center">
              <p className="text-yellow-400 font-semibold">
                All agents are busy. Please wait while we connect you...
              </p>
            </div>
          )}


          {error && (
            <div className="bg-red-600/20 border border-red-500 rounded-lg p-4">
              <p className="text-red-400 font-semibold">⚠️ Error</p>
              <p className="text-red-300 text-sm mt-1">{error}</p>
              <button
                onClick={() => {
                  setError(null);
                  setConnectionStatus('idle');
                  startCall();
                }}
                className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm"
              >
                Retry Connection
              </button>
            </div>
          )}

          <div className={`px-4 py-2 rounded-lg text-sm font-semibold ${connectionStatus === 'connected' ? 'bg-green-600/20 text-green-400' :
            connectionStatus === 'connecting' ? 'bg-yellow-600/20 text-yellow-400' :
              connectionStatus === 'error' ? 'bg-red-600/20 text-red-400' :
                'bg-gray-600/20 text-gray-400'
            }`}>
            {connectionStatus === 'connected' && '🟢 Connected'}
            {connectionStatus === 'connecting' && '🟡 Connecting...'}
            {connectionStatus === 'error' && '🔴 Connection Error'}
            {connectionStatus === 'idle' && '⚪ Initializing...'}
          </div>

          <div className="flex items-center justify-between text-white">
            <h2 className="text-2xl font-semibold">AI Dental Receptionist</h2>
            <div className={`text-lg font-mono px-4 py-2 rounded-lg ${timeRemaining <= 10 ? 'bg-red-600/30 border border-red-500' : 'bg-red-600/20'
              }`}>
              Time: {Math.floor(timeRemaining / 60)}:
              {timeRemaining % 60 < 10 ? '0' : ''}
              {timeRemaining % 60}
            </div>
          </div>

          <div className="flex-1 bg-slate-800/30 rounded-lg p-6 overflow-y-auto max-h-96 border border-slate-700">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-400 text-center">
                  {connectionStatus === 'connecting' ? 'Connecting to AI Agent...' : 'Waiting for AI response...'}
                </p>
              </div>
            ) : (
              messages.map((m, i) => (
                <div
                  key={i}
                  className={`mb-4 flex ${m.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                >
                  <span
                    className={`max-w-xs px-4 py-2 rounded-lg ${m.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-slate-700 text-gray-100 rounded-bl-none'
                      }`}
                  >
                    {m.content}
                  </span>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {isListening && (
            <div className="bg-slate-700/50 p-3 rounded-lg border border-green-500/50 animate-pulse">
              <p className="text-green-400 text-sm font-semibold">🎤 Listening...</p>
              {userInput && (
                <p className="text-gray-300 text-sm mt-1">{userInput}</p>
              )}
            </div>
          )}

          {isSpeaking && (
            <div className="bg-slate-700/50 p-3 rounded-lg border border-yellow-500/50 animate-pulse">
              <p className="text-yellow-400 text-sm font-semibold">🔊 AI is speaking...</p>
            </div>
          )}

          <div className="flex justify-center gap-4">
            {/* <button
              onClick={isListening ? stopListening : startListening}
              disabled={isSpeaking || connectionStatus !== 'connected' || isProcessing}
              className={`px-6 py-3 rounded-full flex items-center gap-2 font-semibold transition ${
                isListening
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-green-500 hover:bg-green-600 text-white'
              } ${(isSpeaking || connectionStatus !== 'connected' || isProcessing) ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
              {isListening ? 'Stop' : 'Speak'}
            </button> */}

            <button
              onClick={endCall}
              className="px-6 py-3 rounded-full flex items-center gap-2 font-semibold 
                         bg-red-600 hover:bg-red-700 text-white transition"
            >
              <PhoneOff size={20} />
              End Call
            </button>
          </div>

          <p className="text-center text-gray-400 text-sm">
            {isProcessing ? (
              '⏳ AI is processing...'
            ) : isSpeaking ? (
              '🔊 AI is speaking...'
            ) : connectionStatus === 'connected' ? (
              isListening ? '🎤 Listening to your voice...' : 'Click Speak to start talking'
            ) : (
              'Waiting for connection...'
            )}
          </p>
        </div>
      )}
    </div>
  );
}

export default App;














// import { useState, useEffect, useRef } from 'react';
// import { Phone, PhoneOff } from 'lucide-react';
// import AIVoiceOrb from './components/AIVoiceOrb';
// import AnimatedOrb from './components/AnimatedOrb';

// type Page = 'FORM' | 'INTRO' | 'CALL';

// interface Message {
//   role: 'user' | 'assistant';
//   content: string;
// }

// function App() {
//   const isSpeakingRef = useRef(false);
//   const CALL_DURATION = 120;
//   const BACKEND_URL = "https://somniferous-unpursued-lin.ngrok-free.dev";

//   const transcriptBufferRef = useRef('');
//   const [isQueued, setIsQueued] = useState(false);

//   const [page, setPage] = useState<Page>("FORM");
//   const [isCallActive, setIsCallActive] = useState(false);
//   const [timeRemaining, setTimeRemaining] = useState(CALL_DURATION);
//   const [sessionId, setSessionId] = useState<string>('');
//   const [messages, setMessages] = useState<Message[]>([]);
//   const [userInput, setUserInput] = useState('');
//   const [isLoading, setIsLoading] = useState(false);
//   const wsConnectionRef = useRef<WebSocket | null>(null);
//   const [error, setError] = useState<string | null>(null);
//   const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle');
//   const [isProcessing, setIsProcessing] = useState(false);
//   const messagesEndRef = useRef<HTMLDivElement>(null);

//   // Speech Recognition states
//   const [isListening, setIsListening] = useState(false);
//   const [transcript, setTranscript] = useState('');
//   const [isSpeaking, setIsSpeaking] = useState(false);
//   const recognitionRef = useRef<any>(null);
//   const synthRef = useRef<SpeechSynthesisUtterance | null>(null);
//   const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
//   const lastSpeechTimeRef = useRef<number>(0);
//   const isCallActiveRef = useRef(false);
//   const isListeningRef = useRef(false);
//   const lastSentPartialRef = useRef<string>("");
//   const partialThrottleTimerRef = useRef<number | null>(null);

//   useEffect(() => {
//     const loadVoices = () => {
//       window.speechSynthesis.getVoices();
//     };
//     loadVoices();
//     window.speechSynthesis.onvoiceschanged = loadVoices;
//   }, []);

//   useEffect(() => {
//     window.speechSynthesis.getVoices();
//   }, []);

//   useEffect(() => {
//     const checkHindiVoice = () => {
//       const voices = window.speechSynthesis.getVoices();
//       if (!voices.length) return;
//       const hasHindi = voices.some(
//         v => v.lang === "hi-IN" || v.name.toLowerCase().includes("hindi")
//       );
//       if (!hasHindi) {
//         alert(
//           "⚠️ Hindi voice not found.\n\n" +
//           "For best experience, please enable Hindi voice in your device settings.\n\n" +
//           "📱 Android:\n" +
//           "Settings → Language & Input → Text-to-Speech → Install Hindi\n\n" +
//           "💻 Windows:\n" +
//           "Settings → Time & Language → Speech → Add Hindi voice\n\n" +
//           "Then refresh this page."
//         );
//       }
//     };
//     window.speechSynthesis.onvoiceschanged = checkHindiVoice;
//     checkHindiVoice();
//   }, []);

//   useEffect(() => {
//     const int = setInterval(() => {
//       console.debug("DBG: speaking:", isSpeakingRef.current, "listening:", isListeningRef.current, "processing:", isProcessing);
//     }, 2000);
//     return () => clearInterval(int);
//   }, []);

//   useEffect(() => {
//     const checkVoices = () => {
//       const voices = window.speechSynthesis.getVoices();
//       if (!voices.length) return;
//       const hindiExists = voices.some(
//         v => v.lang === "hi-IN" || v.name.toLowerCase().includes("hindi")
//       );
//       if (!hindiExists) {
//         alert(
//           "For better Indian accent, please install Hindi voice in your device.\n\n" +
//           "Android:\nSettings → Language → Text-to-Speech → Install Hindi\n\n" +
//           "Windows:\nSettings → Time & Language → Speech → Add Hindi voice\n\n" +
//           "Mac:\nSystem Settings → Accessibility → Spoken Content → Voices → Hindi"
//         );
//       }
//     };
//     window.speechSynthesis.onvoiceschanged = checkVoices;
//     checkVoices();
//   }, []);

//   const ensureMicPermission = async () => {
//     try {
//       const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//       stream.getTracks().forEach(track => track.stop());
//       return true;
//     } catch (err) {
//       alert("Microphone permission is required to talk with the AI receptionist.");
//       return false;
//     }
//   };

//   const [lastBooking, setLastBooking] = useState<{
//     date: string;
//     time: string;
//   } | null>(null);

//   const [userProfile, setUserProfile] = useState<{
//     name?: string;
//     phone?: string;
//     email?: string;
//   } | null>(null);

//   const [formName, setFormName] = useState("");
//   const [formPhone, setFormPhone] = useState("");
//   const [formEmail, setFormEmail] = useState("");

//   useEffect(() => {
//     const stored = localStorage.getItem("userProfile");
//     const storedTime = localStorage.getItem("userProfileTime");

//     if (!stored || !storedTime) {
//       setPage("FORM");
//       return;
//     }

//     const age = Date.now() - Number(storedTime);
//     const oneDay = 24 * 60 * 60 * 1000;

//     if (age > oneDay) {
//       localStorage.removeItem("userProfile");
//       localStorage.removeItem("userProfileTime");
//       setPage("FORM");
//       return;
//     }

//     const profile = JSON.parse(stored);
//     setUserProfile(profile);
//     setPage("INTRO");
//   }, []);

//   useEffect(() => {
//     const SpeechRecognition =
//       (window as any).SpeechRecognition ||
//       (window as any).webkitSpeechRecognition;

//     if (!SpeechRecognition) {
//       console.warn("SpeechRecognition not supported");
//       return;
//     }

//     const recognition = new SpeechRecognition();
//     recognition.continuous = false;
//     recognition.interimResults = true;
//     recognition.lang = "en-IN";
//     recognition.maxAlternatives = 1;

//     recognitionRef.current = recognition;

//     recognition.onstart = () => {
//       console.log("🎤 Speech recognition started");
//       isListeningRef.current = true;
//       setIsListening(true);
//     };

//     recognition.onresult = (event: any) => {
//       if (isProcessing || isSpeakingRef.current) return;

//       let interim = "";
//       let finalChunk = "";

//       for (let i = event.resultIndex; i < event.results.length; i++) {
//         const text = event.results[i][0].transcript;
//         if (event.results[i].isFinal) {
//           finalChunk += text + " ";
//         } else {
//           interim += text;
//         }
//       }

//       if (interim) setUserInput(interim);

//       if (finalChunk) {
//         transcriptBufferRef.current += finalChunk.trim() + " ";
//         lastSpeechTimeRef.current = Date.now();

//         if (silenceTimerRef.current) {
//           clearTimeout(silenceTimerRef.current);
//         }

//         silenceTimerRef.current = setTimeout(() => {
//           autoSendTranscript();
//         }, 1500);
//       }
//     };

//     recognition.onerror = (event: any) => {
//       console.warn("🎤 Speech recognition error:", event.error);
//       isListeningRef.current = false;
//       setIsListening(false);

//       if (event.error === "no-speech") {
//         setTimeout(() => {
//           if (!isSpeakingRef.current && isCallActiveRef.current) {
//             startListening();
//           }
//         }, 800);
//       }
//     };

//     recognition.onend = () => {
//       console.log("🎤 Speech recognition ended");
//       isListeningRef.current = false;
//       setIsListening(false);

//       if (isSpeakingRef.current || isProcessing) return;
//       if (window.speechSynthesis.speaking) return;

//       if (
//         isCallActiveRef.current &&
//         wsConnectionRef.current &&
//         wsConnectionRef.current.readyState === WebSocket.OPEN
//       ) {
//         setTimeout(() => {
//           if (!isSpeakingRef.current && !isProcessing && !window.speechSynthesis.speaking) {
//             startListening();
//           }
//         }, 2200);
//       }
//     };

//     return () => {
//       try { recognition.stop(); } catch { }
//       recognitionRef.current = null;
//     };
//   }, [isProcessing]);

//   useEffect(() => {
//     if (!isCallActive) return;

//     const interval = setInterval(() => {
//       setTimeRemaining((prev) => {
//         if (prev <= 1) {
//           console.log("⏰ Call time expired - ending call");
//           endCall();
//           return CALL_DURATION;
//         }
//         return prev - 1;
//       });
//     }, 1000);

//     return () => clearInterval(interval);
//   }, [isCallActive]);

//   const hasHindiVoice = () => {
//     const voices = window.speechSynthesis.getVoices();
//     return voices.some(
//       v =>
//         v.lang === "hi-IN" ||
//         v.name.toLowerCase().includes("hindi")
//     );
//   };

//   const speakText = (text: string) => {
//     if (!text) return;

//     console.log("🗣️ SPEAKING:", text);

//     try { recognitionRef.current?.abort(); } catch { }
//     isListeningRef.current = false;
//     setIsListening(false);

//     try {
//       if (window.speechSynthesis.speaking) {
//         window.speechSynthesis.cancel();
//       }
//     } catch { }

//     const utterance = new SpeechSynthesisUtterance(text);

//     const voices = window.speechSynthesis.getVoices();

//     let selectedVoice =
//       voices.find(v => v.lang === "hi-IN") ||
//       voices.find(v => v.name.toLowerCase().includes("hindi")) ||
//       voices.find(v => v.name.includes("Ravi")) ||
//       voices.find(v => v.lang === "en-IN") ||
//       voices.find(v => v.lang === "en-GB") ||
//       voices.find(v => v.lang === "en-US") ||
//       voices[0];

//     if (selectedVoice) {
//       utterance.voice = selectedVoice;

//       if (selectedVoice.lang === "hi-IN") {
//         utterance.lang = "hi-IN";
//       } else {
//         utterance.lang = "en-IN";
//       }

//       console.log("🎙️ Using voice:", selectedVoice.name, selectedVoice.lang);
//     }

//     const lower = text.toLowerCase();

//     let rate = 1.18;
//     let pitch = 1.02;

//     if (lower.includes("namaste") || lower.includes("hello")) {
//       rate = 0.95;
//       pitch = 1.08;
//     }
//     else if (lower.includes("booked") || lower.includes("confirm")) {
//       rate = 1.0;
//       pitch = 1.12;
//     }
//     else if (text.includes("?")) {
//       rate = 0.96;
//       pitch = 1.05;
//     }
//     else if (lower.includes("sorry")) {
//       rate = 0.9;
//       pitch = 0.98;
//     }

//     rate += (Math.random() * 0.04 - 0.02);
//     pitch += (Math.random() * 0.05 - 0.02);

//     utterance.rate = rate;
//     utterance.pitch = pitch;
//     utterance.volume = 1;

//     utterance.text = text
//       .replace(/,/g, ", ")
//       .replace(/\./g, "... ")
//       .replace(/\?/g, "? ")
//       .replace(/!/g, "! ");

//     utterance.onstart = () => {
//       isSpeakingRef.current = true;
//       setIsSpeaking(true);

//       if (silenceTimerRef.current) {
//         clearTimeout(silenceTimerRef.current);
//         silenceTimerRef.current = null;
//       }
//     };

//     utterance.onend = () => {
//       isSpeakingRef.current = false;
//       setIsSpeaking(false);

//       setTimeout(() => {
//         if (
//           isCallActiveRef.current &&
//           !isListeningRef.current &&
//           !isProcessing &&
//           wsConnectionRef.current &&
//           wsConnectionRef.current.readyState === WebSocket.OPEN
//         ) {
//           startListening();
//         }
//       }, 500);
//     };

//     utterance.onerror = () => {
//       isSpeakingRef.current = false;
//       setIsSpeaking(false);
//     };

//     setTimeout(() => {
//       window.speechSynthesis.speak(utterance);
//     }, 120);
//   };

//   const autoSendTranscript = () => {
//     const text = transcriptBufferRef.current.trim();
//     if (!text) return;

//     const ws = wsConnectionRef.current;
//     if (!ws || ws.readyState !== WebSocket.OPEN) return;

//     const raw = localStorage.getItem("userProfile");
//     const profile = raw ? JSON.parse(raw) : {};

//     const payload = {
//       user_input: text,
//       user_profile: {
//         name: profile?.name || "Guest",
//         phone: profile?.phone || null,
//         email: profile?.email || ""
//       }
//     };

//     console.log("🚀 SENDING PAYLOAD:", payload);

//     ws.send(JSON.stringify(payload));

//     setMessages(prev => [...prev, { role: "user", content: text }]);

//     transcriptBufferRef.current = "";
//     setUserInput("");
//     setIsProcessing(true);
//   };

//   const startListening = () => {
//     const recognition = recognitionRef.current;
//     if (!recognition) return;

//     if (
//       isListeningRef.current ||
//       isSpeakingRef.current ||
//       isProcessing ||
//       !isCallActiveRef.current ||
//       !wsConnectionRef.current ||
//       wsConnectionRef.current.readyState !== WebSocket.OPEN
//     ) {
//       return;
//     }

//     try {
//       recognition.start();
//       console.log("🎤 Speech recognition start requested");
//     } catch (e) {
//       console.warn("recognition.start() failed", e);
//     }
//   };

//   const stopListening = () => {
//     if (recognitionRef.current && isListeningRef.current) {
//       try {
//         recognitionRef.current.stop();
//       } catch { }
//     }
//   };

//   const startCall = async () => {
//     console.log("📞 Starting call...");

//     const allowed = await ensureMicPermission();
//     if (!allowed) return;

//     if (isCallActiveRef.current) return;

//     setPage("CALL");
//     setError(null);
//     setConnectionStatus("connecting");
//     setMessages([]);
//     setIsProcessing(false);

//     const WS_URL = `${BACKEND_URL.replace(/^http/, "ws")}/conversation/stream`;

//     const ws = new WebSocket(WS_URL);
//     wsConnectionRef.current = ws;

//     ws.onopen = () => {
//       console.log("🟢 WS connected. Waiting for agent...");
//     };

//     ws.onmessage = (event) => {
//       let res: any = null;
//       try {
//         res = JSON.parse(event.data);
//       } catch (e) {
//         console.warn("Failed to parse WS message", e, event.data);
//         return;
//       }

//       console.log("WS:", res);

//       if (res?.type === "busy") {
//         console.log("⏳ Agent busy — added to queue");
//         setIsQueued(true);
//         setConnectionStatus("connecting");
//         return;
//       }

//       if (res?.type === "start") {
//         console.log("🚀 Agent ready");

//         setIsQueued(false);
//         setConnectionStatus("connected");
//         isCallActiveRef.current = true;
//         setIsCallActive(true);
//         setTimeRemaining(CALL_DURATION);

//         const intro =
//           "Namaste ji! Main Bright Dental Clinic ki AI receptionist bol rahi hoon. Haan ji, batayiye — appointment book karna hai, reschedule karna hai, ya koi information chahiye?";

//         try { recognitionRef.current?.abort(); } catch { }
//         isListeningRef.current = false;
//         setIsListening(false);

//         setMessages([{ role: "assistant", content: intro }]);
//         speakText(intro);
//         return;
//       }

//       setIsProcessing(false);

//       let textToSpeak: string | null = null;
//       const payload = res?.response ?? null;

//       if (typeof payload === "string" && payload.trim()) {
//         textToSpeak = payload;
//       } else if (payload && typeof payload === "object") {
//         if (typeof payload.message === "string" && payload.message.trim()) {
//           textToSpeak = payload.message;
//         } else if (typeof payload.text === "string" && payload.text.trim()) {
//           textToSpeak = payload.text;
//         } else if (typeof payload.reply === "string" && payload.reply.trim()) {
//           textToSpeak = payload.reply;
//         } else if (typeof payload.answer === "string" && payload.answer.trim()) {
//           textToSpeak = payload.answer;
//         }
//       } else if (typeof res?.message === "string") {
//         textToSpeak = res.message;
//       }

//       if (!textToSpeak) {
//         console.log("⚠️ No speakable text found in WS payload:", res);
//         return;
//       }

//       try {
//         if (payload && payload.booking) {
//           setLastBooking(payload.booking);
//         }
//       } catch { }

//       try { recognitionRef.current?.abort(); } catch { }
//       isListeningRef.current = false;
//       setIsListening(false);

//       setMessages(prev => [
//         ...prev,
//         { role: "assistant", content: textToSpeak! }
//       ]);

//       console.log("🗣️ SPEAKING:", textToSpeak);
//       if (isSpeakingRef.current) return;

//       speakText(textToSpeak);
//     };

//     ws.onerror = () => {
//       setConnectionStatus("error");
//       setError("Connection error.");
//     };

//     ws.onclose = () => {
//       console.log("🟡 WS closed");
//       wsConnectionRef.current = null;
//       isCallActiveRef.current = false;
//       setIsCallActive(false);

//       try { recognitionRef.current?.abort(); } catch { }
//       isListeningRef.current = false;
//       setIsListening(false);
//     };
//   };

//   const endCall = () => {
//     console.log("📞 Ending call...");

//     if (!isCallActiveRef.current) return;

//     isCallActiveRef.current = false;
//     setIsCallActive(false);

//     try { stopListening(); } catch { }
//     try { window.speechSynthesis.cancel(); } catch { }

//     if (wsConnectionRef.current) {
//       try { wsConnectionRef.current.close(); } catch { }
//       wsConnectionRef.current = null;
//     }

//     setUserInput("");
//     setIsListening(false);
//     setIsSpeaking(false);
//     setIsProcessing(false);
//     setConnectionStatus("idle");

//     setPage("INTRO");
//     console.log("✅ Call ended cleanly");
//   };

//   return (
//     <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-black flex items-center justify-center p-4">

//       {/* PAGE 0 — FORM */}
//       {page === 'FORM' && (
//         <div className="flex flex-col items-center gap-6 max-w-md w-full">
//           <h1 className="text-4xl font-semibold text-white">Welcome to Bright Dental Clinic</h1>

//           <p className="text-gray-300 text-center">
//             Please enter your details so we can create your booking and identify you for reschedules.
//           </p>

//           <input
//             type="text"
//             value={formName}
//             onChange={(e) => setFormName(e.target.value)}
//             placeholder="Full Name"
//             className="w-full px-4 py-3 rounded bg-slate-800 text-white"
//           />

//           <input
//             type="tel"
//             value={formPhone}
//             onChange={(e) => setFormPhone(e.target.value)}
//             placeholder="Phone Number"
//             className="w-full px-4 py-3 rounded bg-slate-800 text-white mt-2"
//           />

//           <input
//             type="email"
//             value={formEmail}
//             onChange={(e) => setFormEmail(e.target.value)}
//             placeholder="Email (optional)"
//             className="w-full px-4 py-3 rounded bg-slate-800 text-white mt-2"
//           />

//           <div className="flex gap-3 mt-4">
//             <button
//               className="px-6 py-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white font-semibold"
//               onClick={async () => {
//                 if (!formName.trim() || !formPhone.trim()) {
//                   alert("Please enter name and phone.");
//                   return;
//                 }

//                 const profile = {
//                   name: formName.trim(),
//                   phone: formPhone.trim(),
//                   email: formEmail.trim() || ""
//                 };

//                 localStorage.setItem("userProfile", JSON.stringify(profile));
//                 localStorage.setItem("userProfileTime", Date.now().toString());
//                 setUserProfile(profile);

//                 try {
//                   const res = await fetch(`${BACKEND_URL}/store-profile`, {
//                     method: "POST",
//                     headers: {
//                       "Content-Type": "application/json"
//                     },
//                     body: JSON.stringify(profile)
//                   });

//                   await res.json();

//                   console.log("✅ PROFILE STORED ON BACKEND");

//                   setPage("INTRO");

//                 } catch (err) {
//                   console.error("❌ Failed to store profile:", err);
//                   alert("Network error. Please try again.");
//                 }
//               }}
//             >
//               Continue
//             </button>

//             <button
//               className="px-6 py-3 rounded-full bg-gray-600 hover:bg-gray-700 text-white font-semibold"
//               onClick={() => {
//                 setFormName("");
//                 setFormPhone("");
//                 setFormEmail("");
//               }}
//             >
//               Clear
//             </button>
//           </div>
//         </div>
//       )}

//       {/* PAGE 1 — INTRO with ANIMATED ORB */}
//       {page === 'INTRO' && (
//         <div className="w-full h-screen flex flex-col">
//           {/* TOP SECTION — TITLE */}
//           <div className="flex-none pt-16 text-center px-4">
//             <h1 className="text-6xl md:text-7xl font-bold text-white tracking-tight">
//               AI Dental Receptionist
//             </h1>
//           </div>

//           {/* MIDDLE SECTION — ANIMATED ORB */}
//           <div className="flex-1 flex items-center justify-center">
//             <AnimatedOrb size="large" color="cyan" />
//           </div>

//           {/* BOTTOM SECTION — TEXT & BUTTON */}
//           <div className="flex-none pb-16 text-center space-y-6 px-4">
//             <div className="max-w-xl mx-auto">
//               <p className="text-xl text-gray-300">
//                 Welcome to Bright Dental Clinic. Click below to start a voice
//                 conversation with our AI receptionist.
//               </p>
//             </div>

//             <button
//               onClick={startCall}
//               className="px-8 py-4 rounded-full text-lg flex items-center gap-3 
//                          bg-blue-500 hover:bg-blue-600 text-white font-semibold 
//                          transition mx-auto border-2 border-white/20 hover:border-white/40
//                          transform hover:scale-105 duration-200"
//             >
//               <Phone size={24} />
//               Start Voice Call (2 mins)
//             </button>

//             {lastBooking && (
//               <div className="mt-6 p-4 rounded-lg bg-green-600/20 border border-green-500 max-w-md mx-auto text-center">
//                 <p className="text-green-400 font-semibold">
//                   ✅ Appointment Confirmed
//                 </p>
//                 <p className="text-green-300 mt-1">
//                   {lastBooking.date} at {lastBooking.time}
//                 </p>
//               </div>
//             )}
//           </div>
//         </div>
//       )}

//       {/* PAGE 2 — CALL with HIGH-TECH AI VOICE ORB */}
//       {page === 'CALL' && (
//         <div className="w-full h-screen flex flex-col relative bg-gradient-to-b from-slate-950 via-slate-900 to-black">
          
//           {/* FULL-SCREEN HIGH-TECH ANIMATED AI VOICE ORB - CENTERED */}
//           <div className="flex-1 flex items-center justify-center">
//             <AIVoiceOrb
//               isListening={isListening}
//               isSpeaking={isSpeaking}
//               isProcessing={isProcessing}
//               connectionStatus={connectionStatus}
//             />
//           </div>

//           {/* BOTTOM CONTROLS OVERLAY - FIXED AT BOTTOM */}
//           <div className="flex-none bg-gradient-to-t from-black via-black/90 to-transparent p-8 space-y-4">
//             {isQueued && (
//               <div className="bg-yellow-600/20 border border-yellow-500 rounded-lg p-3 text-center max-w-md mx-auto w-full">
//                 <p className="text-yellow-400 font-semibold">
//                   ⏳ All agents are busy. Please wait...
//                 </p>
//               </div>
//             )}

//             {error && (
//               <div className="bg-red-600/20 border border-red-500 rounded-lg p-4 max-w-md mx-auto w-full">
//                 <p className="text-red-400 font-semibold">⚠️ Error</p>
//                 <p className="text-red-300 text-sm mt-1">{error}</p>
//                 <button
//                   onClick={() => {
//                     setError(null);
//                     setConnectionStatus('idle');
//                     startCall();
//                   }}
//                   className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm"
//                 >
//                   Retry Connection
//                 </button>
//               </div>
//             )}

//             <div className="flex justify-center gap-4">
//               <button
//                 onClick={endCall}
//                 className="px-8 py-3 rounded-full flex items-center gap-2 font-semibold 
//                            bg-red-600 hover:bg-red-700 text-white transition transform hover:scale-105
//                            border-2 border-red-500/50"
//               >
//                 <PhoneOff size={20} />
//                 End Call
//               </button>
//             </div>

//             <div className="text-center text-gray-300 text-sm font-semibold">
//               Time: {Math.floor(timeRemaining / 60)}:{timeRemaining % 60 < 10 ? '0' : ''}{timeRemaining % 60}
//             </div>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }

// export default App;