"use client";
import { useMemo } from "react";
import { Avatar } from "./Avatar";
import { BrainState, EmotionalState } from "@/types";
import { ChatMessage as ChatMessageType } from "@/types";

/**
 * Phase 8: panel that renders MISTY's virtual body. It derives the avatar's
 * expression from the emotional_state of the most recent assistant message,
 * so the face updates after every brain cycle without any extra plumbing.
 */

interface AvatarPanelProps {
  messages: ChatMessageType[];
  brainState?: BrainState | null;
  processing?: boolean;
}

export function AvatarPanel({ messages, brainState, processing }: AvatarPanelProps) {
  const emotionalState: Partial<EmotionalState> = useMemo(() => {
    // Prefer the freshest assistant brain_state, fall back to the live state.
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const msg = messages[i];
      if (msg.role === "assistant" && msg.brain_state) {
        const bs = msg.brain_state as unknown as BrainState;
        if (bs.emotional_state) return bs.emotional_state;
      }
    }
    return brainState?.emotional_state ?? {};
  }, [messages, brainState]);

  const bars = useMemo(() => {
    const entries: [string, number][] = [
      ["satisfaction", emotionalState.satisfaction ?? 0],
      ["confidence", emotionalState.confidence ?? 0],
      ["curiosity", emotionalState.curiosity ?? 0],
      ["interest", emotionalState.interest ?? 0],
      ["uncertainty", emotionalState.uncertainty ?? 0],
      ["frustration", emotionalState.frustration ?? 0],
      ["urgency", emotionalState.urgency ?? 0],
      ["attention", emotionalState.attention ?? 0],
    ];
    return entries.filter(([, v]) => v > 0);
  }, [emotionalState]);

  return (
    <div className="flex flex-col items-center gap-4 p-4 border-b border-neural-border">
      <Avatar emotionalState={emotionalState} processing={processing} />
      {/* Live emotion bars */}
      <div className="w-full space-y-1">
        {bars.map(([name, value]) => (
          <div key={name} className="flex items-center gap-2">
            <span className="w-24 text-[10px] uppercase tracking-wider text-neural-muted">
              {name}
            </span>
            <div className="flex-1 h-1.5 rounded-full bg-neural-border overflow-hidden">
              <div
                className="h-full rounded-full bg-neural-accent transition-all duration-500"
                style={{ width: `${Math.min(1, value) * 100}%` }}
              />
            </div>
            <span className="w-8 text-right text-[10px] text-neural-muted">
              {value.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
