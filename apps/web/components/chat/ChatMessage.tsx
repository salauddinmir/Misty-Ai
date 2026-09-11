"use client";

import { useState } from "react";
import { ChatMessage as ChatMessageType } from "@/types";

interface ChatMessageProps {
  message: ChatMessageType;
}

function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ChatMessage({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const [showTrace, setShowTrace] = useState(false);
  const isUser = message.role === "user";
  const trace = (message as ChatMessageType & { reasoning_trace?: string[] }).reasoning_trace ?? [];

  const copyMessage = async () => {
    await navigator.clipboard?.writeText(message.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };

  return (
    <article className={`group flex gap-3 px-4 py-5 sm:px-8 ${isUser ? "bg-transparent" : "bg-white/[0.025]"}`}>
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold shadow-sm ${isUser ? "bg-cyan-400/15 text-cyan-200 ring-1 ring-cyan-300/20" : "bg-violet-400/15 text-violet-200 ring-1 ring-violet-300/20"}`}>
        {isUser ? "You" : "M"}
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-200">{isUser ? "You" : "MISTY"}</span>
          <span className="text-[10px] text-slate-600">{formatTime(message.timestamp)}</span>
        </div>
        <p className="max-w-3xl whitespace-pre-wrap text-sm leading-7 text-slate-300 sm:text-[15px]">{message.content}</p>
        {!isUser && (
          <div className="mt-3 flex flex-wrap items-center gap-2 opacity-80 transition group-hover:opacity-100">
            <button type="button" onClick={copyMessage} className="rounded-md px-2 py-1 text-[11px] text-slate-500 transition hover:bg-white/5 hover:text-slate-200" aria-label="Copy response">
              {copied ? "Copied" : "Copy"}
            </button>
            {trace.length > 0 && (
              <button type="button" onClick={() => setShowTrace((value) => !value)} className="rounded-md px-2 py-1 text-[11px] text-violet-300/80 transition hover:bg-violet-400/10 hover:text-violet-200">
                {showTrace ? "Hide reasoning" : "Inspect reasoning"}
              </button>
            )}
            {message.processing_time !== undefined && <span className="text-[10px] text-slate-600">{message.processing_time.toFixed(2)}s</span>}
            {message.cycle_count !== undefined && <span className="text-[10px] text-slate-600">cycle {message.cycle_count}</span>}
          </div>
        )}
        {showTrace && (
          <div className="mt-3 max-w-3xl rounded-xl border border-violet-300/10 bg-violet-400/[0.04] p-3 text-xs text-slate-400">
            <div className="mb-2 font-medium text-violet-200">Inspectable reasoning trace</div>
            <ol className="space-y-1.5">
              {trace.map((step, index) => <li key={`${index}-${step}`}><span className="mr-2 text-violet-300/60">{index + 1}.</span>{step}</li>)}
            </ol>
          </div>
        )}
      </div>
    </article>
  );
}
