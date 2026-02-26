import { useEffect, useRef, useState } from "react";

interface Props {
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  connectionStatus?: 'idle' | 'connecting' | 'connected' | 'error';
}

export default function AIVoiceOrb({
  isListening,
  isSpeaking,
  isProcessing,
  connectionStatus = 'idle',
}: Props) {
  const [volume, setVolume] = useState(0);
  const [frequencies, setFrequencies] = useState<number[]>(Array(32).fill(0));
  const rafRef = useRef<number | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Advanced audio analysis setup
  useEffect(() => {
    if (!isListening) {
      setVolume(0);
      setFrequencies(Array(32).fill(0));
      return;
    }

    const setup = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 512;
        analyser.smoothingTimeConstant = 0.85;
        source.connect(analyser);

        audioCtxRef.current = audioCtx;
        analyserRef.current = analyser;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const freqBins = new Uint8Array(32);

        const tick = () => {
          analyser.getByteFrequencyData(dataArray);

          // Calculate overall volume
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
          setVolume(Math.min(sum / dataArray.length / 128, 1));

          // Calculate frequency bins for visualization
          const binSize = Math.floor(dataArray.length / 32);
          for (let i = 0; i < 32; i++) {
            let binSum = 0;
            for (let j = 0; j < binSize; j++) {
              binSum += dataArray[i * binSize + j];
            }
            freqBins[i] = Math.floor(binSum / binSize / 255 * 100);
          }
          setFrequencies(Array.from(freqBins));

          rafRef.current = requestAnimationFrame(tick);
        };

        tick();
      } catch (err) {
        console.error("Audio setup failed:", err);
      }
    };

    setup();

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      if (audioCtxRef.current) {
        audioCtxRef.current.close().catch(() => {});
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [isListening]);

  // Determine state-based styling
  let orbGradient = "from-slate-600 to-slate-800";
  let orbShadow = "shadow-slate-500/50";
  let auraGradient = "from-slate-500/40 to-slate-700/40";
  let ringColor = "border-slate-500/30";
  let pulseColor = "border-slate-400/30";
  let accentColor = "text-slate-400";
  let scale = 1;
  let orbScale = 1;

  if (connectionStatus === 'connecting') {
    orbGradient = "from-amber-500 to-orange-600";
    orbShadow = "shadow-amber-500/70";
    auraGradient = "from-amber-500/50 to-orange-600/50";
    ringColor = "border-amber-400/50";
    pulseColor = "border-amber-300/50";
    accentColor = "text-amber-300";
    orbScale = 1.08;
  }

  if (isListening) {
    orbGradient = "from-cyan-400 via-blue-500 to-indigo-600";
    orbShadow = "shadow-cyan-400/80";
    auraGradient = "from-cyan-400/60 via-blue-500/50 to-indigo-600/40";
    ringColor = "border-cyan-300/70";
    pulseColor = "border-cyan-200/80";
    accentColor = "text-cyan-300";
    scale = 1 + Math.max(volume * 0.8, 0.1);
    orbScale = 1.12;
  }

  if (isSpeaking) {
    orbGradient = "from-emerald-400 via-green-500 to-teal-600";
    orbShadow = "shadow-green-500/80";
    auraGradient = "from-emerald-400/60 via-green-500/50 to-teal-600/40";
    ringColor = "border-emerald-300/70";
    pulseColor = "border-emerald-200/80";
    accentColor = "text-emerald-300";
    orbScale = 1.15;
  }

  if (isProcessing) {
    orbGradient = "from-purple-500 via-pink-500 to-rose-500";
    orbShadow = "shadow-purple-500/80";
    auraGradient = "from-purple-500/60 via-pink-500/50 to-rose-500/40";
    ringColor = "border-purple-300/70";
    pulseColor = "border-pink-300/70";
    accentColor = "text-purple-300";
    orbScale = 1.1;
  }

  if (connectionStatus === 'error') {
    orbGradient = "from-red-500 to-red-700";
    orbShadow = "shadow-red-500/70";
    auraGradient = "from-red-500/50 to-red-700/40";
    ringColor = "border-red-400/50";
    pulseColor = "border-red-300/50";
    accentColor = "text-red-300";
    orbScale = 0.95;
  }

  return (
    <div className="w-full h-screen flex flex-col items-center justify-center gap-8 bg-gradient-to-b from-slate-950 via-slate-900 to-black overflow-hidden relative">
      {/* Background Grid */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 opacity-5 bg-[linear-gradient(to_right,#000_1px,transparent_1px),linear-gradient(to_bottom,#000_1px,transparent_1px)] bg-[size:50px_50px]" />
        <div className="absolute top-0 left-0 w-96 h-96 bg-gradient-to-br from-cyan-500/10 to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-tl from-purple-500/10 to-transparent rounded-full blur-3xl" />
      </div>

      {/* Main Orb Container */}
      <div className="relative flex items-center justify-center h-96 z-10">
        {/* Outer Aura Rings */}
        <div
          className={`absolute w-96 h-96 rounded-full blur-3xl opacity-60 bg-gradient-to-br ${auraGradient} transition-all duration-300`}
          style={{ transform: `scale(${1.2 * orbScale})` }}
        />

        {/* Middle Ring Visualization (Frequency Bars) */}
        <div className="absolute w-80 h-80 rounded-full">
          {frequencies.map((freq, i) => {
            const angle = (i / 32) * Math.PI * 2;
            const radius = 160;
            const height = Math.max(freq / 100 * 40, 4);
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;

            return (
              <div
                key={i}
                className={`absolute w-1 bg-gradient-to-t ${
                  isListening
                    ? "from-cyan-400 to-blue-300"
                    : isSpeaking
                    ? "from-emerald-400 to-green-300"
                    : isProcessing
                    ? "from-purple-400 to-pink-300"
                    : "from-slate-400 to-slate-300"
                } rounded-full transition-all duration-75`}
                style={{
                  height: `${height}px`,
                  left: `160px`,
                  top: `160px`,
                  transform: `rotate(${angle * (180 / Math.PI)}deg) translateY(-${radius}px)`,
                  opacity: isListening || isSpeaking ? 0.8 : 0.3,
                }}
              />
            );
          })}
        </div>

        {/* Inner Rotating Ring */}
        {(isListening || isSpeaking) && (
          <div
            className={`absolute w-72 h-72 rounded-full border border-transparent bg-gradient-to-r ${
              isListening
                ? "from-cyan-400 via-blue-500 to-transparent"
                : "from-emerald-400 via-green-500 to-transparent"
            } animate-spin opacity-30`}
            style={{ animationDuration: "8s" }}
          />
        )}

        {/* Pulsing Ring */}
        {(isListening || isSpeaking || isProcessing) && (
          <div
            className={`absolute w-72 h-72 rounded-full border-2 ${ringColor} animate-pulse`}
            style={{ animationDuration: "1.5s" }}
          />
        )}

        {/* Main Orb */}
        <div
          className={`relative w-64 h-64 rounded-full bg-gradient-to-br ${orbGradient} ${orbShadow} shadow-2xl transition-all duration-200`}
          style={{ transform: `scale(${orbScale * scale})` }}
        >
          {/* Inner Shine/Specular Highlight */}
          <div className="absolute top-8 left-8 w-20 h-20 rounded-full bg-white/20 blur-xl" />

          {/* Rotating Gradient Overlay */}
          {(isListening || isSpeaking) && (
            <div
              className={`absolute inset-0 rounded-full bg-gradient-to-tr ${
                isListening
                  ? "from-cyan-300/30 via-transparent to-blue-600/30"
                  : "from-emerald-300/30 via-transparent to-green-600/30"
              } animate-spin opacity-70`}
              style={{ animationDuration: "4s" }}
            />
          )}

          {/* Center Glow */}
          <div className="absolute inset-0 rounded-full flex items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-white/30 blur-xl animate-pulse" />
          </div>
        </div>

        {/* Outer Pulsing Rings */}
        {(isListening || isSpeaking) && (
          <>
            <div
              className={`absolute rounded-full border border-white/10 animate-ping`}
              style={{
                width: `${280 + (isListening ? volume * 40 : 20)}px`,
                height: `${280 + (isListening ? volume * 40 : 20)}px`,
                animationDuration: "1.2s",
              }}
            />
            <div
              className={`absolute rounded-full border border-white/5 animate-ping`}
              style={{
                width: `${340 + (isListening ? volume * 50 : 30)}px`,
                height: `${340 + (isListening ? volume * 50 : 30)}px`,
                animationDuration: "1.8s"
              }}
            />
          </>
        )}
      </div>

      {/* Status Information */}
      <div className="relative z-10 text-center space-y-3">
        <div className={`text-sm font-semibold tracking-widest uppercase ${accentColor}`}>
          {isListening && "🎤 LISTENING"}
          {isSpeaking && "🔊 SPEAKING"}
          {isProcessing && "⚙️ PROCESSING"}
          {connectionStatus === "connecting" && "🟡 CONNECTING"}
          {connectionStatus === "connected" && !isListening && !isSpeaking && "🟢 READY"}
          {connectionStatus === "error" && "🔴 ERROR"}
          {connectionStatus === "idle" && !isListening && !isSpeaking && !isProcessing && "⚪ STANDBY"}
        </div>

        {isListening && (
          <div className="flex justify-center gap-1">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="w-1 h-8 bg-gradient-to-t from-cyan-400 to-cyan-200 rounded-full animate-pulse"
                style={{
                  animationDelay: `${i * 0.1}s`,
                  height: `${8 + frequencies[i * 6] * 0.3}px`,
                }}
              />
            ))}
          </div>
        )}

        {isSpeaking && (
          <p className="text-sm text-emerald-300 font-medium animate-pulse">
            Speaking with natural rhythm...
          </p>
        )}

        {isProcessing && (
          <p className="text-sm text-purple-300 font-medium animate-pulse">
            Processing your request...
          </p>
        )}
      </div>
    </div>
  );
}