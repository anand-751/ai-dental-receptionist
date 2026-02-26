import { useEffect, useRef, useState } from "react";

interface Props {
  size?: "small" | "medium" | "large";
  color?: "cyan" | "blue" | "purple" | "emerald" | "amber";
}

export default function AnimatedOrb({ size = "large", color = "cyan" }: Props) {
  const [isAnimating, setIsAnimating] = useState(true);

  // Color schemes
  const colorSchemes = {
    cyan: {
      gradient: "from-cyan-400 to-blue-500",
      shadow: "shadow-cyan-500/50",
      aura: "from-cyan-400/50 to-blue-500/30",
      ring: "border-cyan-300/60",
    },
    blue: {
      gradient: "from-blue-400 to-indigo-600",
      shadow: "shadow-blue-500/50",
      aura: "from-blue-400/50 to-indigo-600/30",
      ring: "border-blue-300/60",
    },
    purple: {
      gradient: "from-purple-500 to-pink-600",
      shadow: "shadow-purple-500/50",
      aura: "from-purple-500/50 to-pink-600/30",
      ring: "border-purple-300/60",
    },
    emerald: {
      gradient: "from-emerald-400 to-green-600",
      shadow: "shadow-emerald-500/50",
      aura: "from-emerald-400/50 to-green-600/30",
      ring: "border-emerald-300/60",
    },
    amber: {
      gradient: "from-amber-400 to-orange-600",
      shadow: "shadow-amber-500/50",
      aura: "from-amber-400/50 to-orange-600/30",
      ring: "border-amber-300/60",
    },
  };

  const sizeConfigs = {
    small: {
      container: "h-32 w-32",
      orb: "w-28 h-28",
      aura: "w-36 h-36",
      ring: "w-32 h-32",
      pulse: "w-36 h-36",
    },
    medium: {
      container: "h-48 w-48",
      orb: "w-40 h-40",
      aura: "w-56 h-56",
      ring: "w-48 h-48",
      pulse: "w-56 h-56",
    },
    large: {
      container: "h-64 w-64",
      orb: "w-56 h-56",
      aura: "w-80 h-80",
      ring: "w-64 h-64",
      pulse: "w-80 h-80",
    },
  };

  const scheme = colorSchemes[color];
  const config = sizeConfigs[size];

  useEffect(() => {
    setIsAnimating(true);
  }, []);

  return (
    <div className={`flex items-center justify-center ${config.container} relative`}>
      {/* Outer Aura Glow */}
      <div
        className={`absolute ${config.aura} rounded-full blur-3xl opacity-60 bg-gradient-to-br ${scheme.aura} animate-pulse`}
        style={{ animationDuration: "3s" }}
      />

      {/* Pulsing Ring */}
      <div
        className={`absolute ${config.ring} rounded-full border-2 ${scheme.ring} animate-pulse`}
        style={{ animationDuration: "2s" }}
      />

      {/* Rotating Ring */}
      <div
        className={`absolute ${config.ring} rounded-full border border-white/20 animate-spin`}
        style={{ animationDuration: "8s" }}
      />

      {/* Main Orb */}
      <div
        className={`relative ${config.orb} rounded-full bg-gradient-to-br ${scheme.gradient} ${scheme.shadow} shadow-2xl`}
      >
        {/* Inner Shine */}
        <div className="absolute top-6 left-6 w-1/4 h-1/4 rounded-full bg-white/30 blur-lg" />

        {/* Rotating Overlay */}
        <div
          className={`absolute inset-0 rounded-full bg-gradient-to-tr from-white/20 via-transparent to-transparent animate-spin`}
          style={{ animationDuration: "4s" }}
        />

        {/* Center Glow */}
        <div className="absolute inset-0 rounded-full flex items-center justify-center">
          <div className="w-8 h-8 rounded-full bg-white/40 blur-xl animate-pulse" />
        </div>
      </div>

      {/* Outer Ping Rings */}
      <div
        className={`absolute ${config.pulse} rounded-full border border-white/10 animate-ping`}
        style={{ animationDuration: "1.5s" }}
      />
    </div>
  );
}