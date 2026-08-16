"use client";

import { ChatMessage as ChatMessageType } from "@/types";

interface ChatMessageProps {
  message: ChatMessageType;
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2.5 ${
          isUser
            ? "bg-neural-accent/10 border border-neural-accent/30 text-slate-200"
            : "bg-neural-surface border border-neural-border text-slate-300"
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      </div>
      <div className="flex items-center gap-2 mt-1 px-1">
        <span className="text-[10px] text-neural-muted">
          {formatTime(message.timestamp)}
        </span>
        {message.processing_time !== undefined && (
          <span className="text-[10px] text-neural-muted">
            {message.processing_time.toFixed(2)}s
          </span>
        )}
        {message.cycle_count !== undefined && (
          <span className="text-[10px] text-neural-accent/60">
            cycle #{message.cycle_count}
          </span>
        )}
      </div>
    </div>
  );
}
