"use client";
import { useMemo } from "react";
import { EmotionalState } from "@/types";

/**
 * Phase 8: MISTY's virtual body — an expressive SVG avatar driven entirely
 * by the brain's emotional_state. No image assets, no LLM: the face geometry
 * (eyes, brows, mouth, glow color) is computed from emotion weights so the
 * avatar visibly reflects how the brain "feels" after each cognitive cycle.
 */

interface AvatarProps {
  emotionalState?: Partial<EmotionalState>;
  /** True while the brain is processing the current turn. */
  processing?: boolean;
  size?: number;
}

/** Dominant emotion category mapped to a mood and accent color. */
function dominantMood(emotions: Partial<EmotionalState>) {
  const weights = [
    { name: "satisfaction" as const, value: emotions.satisfaction ?? 0 },
    { name: "confidence" as const, value: emotions.confidence ?? 0 },
    { name: "interest" as const, value: emotions.interest ?? 0 },
    { name: "curiosity" as const, value: emotions.curiosity ?? 0 },
    { name: "frustration" as const, value: emotions.frustration ?? 0 },
    { name: "urgency" as const, value: emotions.urgency ?? 0 },
    { name: "uncertainty" as const, value: emotions.uncertainty ?? 0 },
    { name: "attention" as const, value: emotions.attention ?? 0 },
  ];
  const sorted = [...weights].sort((a, b) => b.value - a.value);
  const top = sorted[0];
  if (!top || top.value < 0.05) return { mood: "neutral" as const, value: 0, color: "#00d4ff" };
  if (top.name === "satisfaction" || top.name === "confidence")
    return { mood: "happy" as const, value: top.value, color: "#00ff88" };
  if (top.name === "frustration" || top.name === "urgency")
    return { mood: "frustrated" as const, value: top.value, color: "#ff4466" };
  if (top.name === "uncertainty")
    return { mood: "puzzled" as const, value: top.value, color: "#ffaa00" };
  return { mood: "curious" as const, value: top.value, color: "#00d4ff" };
}

/** Eye aperture: squints when satisfied, widens when uncertain/curious. */
function eyeHeight(mood: string, value: number) {
  if (mood === "happy") return 7 + value * 5;
  if (mood === "frustrated") return 4 + value * 2;
  return 9 + value * 6;
}

/** Brow tilt: raised when curious/puzzled, lowered when frustrated. */
function browY(mood: string) {
  if (mood === "curious" || mood === "puzzled") return 42;
  if (mood === "frustrated") return 36;
  return 39;
}

/** Mouth shape varies with mood: smile arc, flat, or frowned arc. */
function mouthPath(mood: string, value: number) {
  const depth = 4 + Math.min(value, 1) * 8;
  if (mood === "happy") return `M 45 72 Q 65 ${72 + depth} 85 72`;
  if (mood === "frustrated") return `M 45 78 Q 65 ${78 - depth * 0.6} 85 78`;
  if (mood === "puzzled") return `M 50 76 Q 65 ${76 + depth * 0.4} 80 76`;
  return "M 48 75 L 82 75";
}

export function Avatar({ emotionalState, processing, size = 160 }: AvatarProps) {
  const { mood, value, color } = useMemo(
    () => dominantMood(emotionalState ?? {}),
    [emotionalState]
  );

  const eyes = useMemo(() => {
    const h = eyeHeight(mood, value);
    return [
      { cx: 45, cy: 55 },
      { cx: 85, cy: 55 },
    ].map((eye) => ({ ...eye, rx: 8, ry: h / 2 }));
  }, [mood, value]);

  return (
    <div className="flex flex-col items-center gap-3" data-testid="avatar">
      <svg
        width={size}
        height={size}
        viewBox="0 0 130 130"
        className="transition-all duration-500"
        style={{
          filter: `drop-shadow(0 0 ${8 + value * 14}px ${color}66)`,
        }}
      >
        {/* Head halo */}
        <circle
          cx="65"
          cy="65"
          r="58"
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeOpacity={0.35}
          className={processing ? "animate-pulse_glow" : ""}
        />
        {/* Head */}
        <circle cx="65" cy="65" r="46" fill="#12121a" stroke={color} strokeWidth="2" />
        {/* Brows */}
        <line
          x1="34"
          y1={browY(mood)}
          x2="56"
          y2={mood === "puzzled" ? browY(mood) - 4 : browY(mood)}
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          style={{ transition: "all 0.4s" }}
        />
        <line
          x1="74"
          y1={mood === "puzzled" ? browY(mood) - 4 : browY(mood)}
          x2="96"
          y2={browY(mood)}
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          style={{ transition: "all 0.4s" }}
        />
        {/* Eyes */}
        {eyes.map((eye, i) => (
          <ellipse
            key={i}
            cx={eye.cx}
            cy={eye.cy}
            rx={eye.rx}
            ry={eye.ry}
            fill={color}
            style={{ transition: "all 0.4s" }}
          />
        ))}
        {/* Mouth */}
        <path
          d={mouthPath(mood, value)}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          style={{ transition: "all 0.4s" }}
        />
        {/* Processing blink */}
        {processing && (
          <circle cx="65" cy="20" r="3" fill={color} className="animate-pulse_glow" />
        )}
      </svg>
      <div className="text-center">
        <p className="text-xs font-semibold tracking-widest text-neural-accent uppercase">
          MISTY
        </p>
        <p className="text-[10px] text-neural-muted capitalize">
          {processing ? "thinking…" : `mood: ${mood}`}
        </p>
      </div>
    </div>
  );
}
