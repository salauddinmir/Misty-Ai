"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessage as ChatMessageType, BrainState } from "@/types";
import { ChatMessage } from "./ChatMessage";
import { sendMessage } from "@/lib/api";

interface ChatInterfaceProps {
  onBrainStateUpdate: (state: BrainState) => void;
  onMessagesChange?: (messages: ChatMessageType[]) => void;
  onProcessingChange?: (processing: boolean) => void;
}

const STARTERS = [
  { title: "Understand a concept", prompt: "Explain a complex idea simply in Bengali and English." },
  { title: "Explore the web", prompt: "What are the latest important developments in artificial intelligence?" },
  { title: "Think with MISTY", prompt: "Help me reason through a difficult decision step by step." },
  { title: "Learn together", prompt: "Teach me an interesting fact and explain why it matters." },
];

export function ChatInterface({ onBrainStateUpdate, onMessagesChange, onProcessingChange }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStartedAt, setLoadingStartedAt] = useState<number | null>(null);
  const [loadingSeconds, setLoadingSeconds] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (loadingStartedAt === null) {
      setLoadingSeconds(0);
      return;
    }
    const timer = window.setInterval(() => setLoadingSeconds((Date.now() - loadingStartedAt) / 1000), 100);
    return () => window.clearInterval(timer);
  }, [loadingStartedAt]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => scrollToBottom(), [messages, scrollToBottom]);

  const updateMessages = (next: ChatMessageType[]) => {
    setMessages(next);
    onMessagesChange?.(next);
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const content = input.trim();
    if (!content || isLoading) return;

    const userMessage: ChatMessageType = { id: `msg-${Date.now()}`, role: "user", content, timestamp: Date.now() / 1000 };
    updateMessages([...messages, userMessage]);
    setInput("");
    setIsLoading(true);
    setLoadingStartedAt(Date.now());
    onProcessingChange?.(true);

    try {
      const response = await sendMessage(content);
      const assistantMessage: ChatMessageType = {
        id: `msg-${Date.now()}`,
        role: "assistant",
        content: response.response,
        timestamp: Date.now() / 1000,
        brain_state: response.brain_state,
        processing_time: response.processing_time,
        cycle_count: response.cycle_count,
        thought_trace: response.thought_trace,
        self_model: response.self_model,
        grounding: response.grounding,
        phase_timings_ms: response.phase_timings_ms,
        reasoning_trace: response.reasoning_trace,
      };
      updateMessages([...messages, userMessage, assistantMessage]);
      onBrainStateUpdate(response.brain_state);
    } catch {
      updateMessages([...messages, userMessage, { id: `msg-${Date.now()}`, role: "assistant", content: "I could not connect to the MISTY brain. Please check the backend connection and try again.", timestamp: Date.now() / 1000 }]);
    } finally {
      setIsLoading(false);
      setLoadingStartedAt(null);
      onProcessingChange?.(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  };

  const handleStarter = (prompt: string) => {
    setInput(prompt);
    textareaRef.current?.focus();
  };

  return (
    <section className="flex h-full min-h-0 flex-col bg-[#0b1020]">
      <header className="flex items-center justify-between border-b border-white/[0.07] px-4 py-3.5 sm:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-300 to-violet-400 text-sm font-black text-slate-950 shadow-lg shadow-violet-500/10">M</div>
          <div>
            <h1 className="text-sm font-semibold tracking-wide text-slate-100">MISTY</h1>
            <p className="text-[11px] text-slate-500">Smart Artificial Brain · Bengali / English</p>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-emerald-300/10 bg-emerald-300/[0.04] px-3 py-1.5 text-[11px] text-emerald-200/80">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-300 shadow-[0_0_10px_rgba(110,231,183,0.8)]" />
          Cognitive systems online
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col justify-center px-5 py-10 sm:px-10">
            <div className="mb-8 text-center">
              <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-cyan-300/20 to-violet-400/20 text-2xl font-black text-cyan-100 ring-1 ring-white/10">M</div>
              <h2 className="text-2xl font-semibold text-slate-100 sm:text-3xl">How can MISTY help you today?</h2>
              <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-500">Ask in Bengali or English. MISTY combines memory, deterministic reasoning, evidence search, and grounded Nemotron responses.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {STARTERS.map((starter) => (
                <button key={starter.title} type="button" onClick={() => handleStarter(starter.prompt)} className="rounded-2xl border border-white/[0.08] bg-white/[0.025] p-4 text-left transition hover:border-cyan-300/25 hover:bg-cyan-300/[0.05]">
                  <div className="text-sm font-medium text-slate-200">{starter.title}</div>
                  <div className="mt-1 text-xs leading-5 text-slate-500">{starter.prompt}</div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto w-full max-w-4xl pb-8">
            {messages.map((message) => <ChatMessage key={message.id} message={message} />)}
            {isLoading && (
              <div className="flex gap-3 bg-white/[0.025] px-4 py-5 sm:px-8">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-400/15 text-xs font-bold text-violet-200">M</div>
                <div className="flex items-center gap-3 text-xs text-slate-500"><span className="flex gap-1"><i className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-300" /><i className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-300 [animation-delay:150ms]" /><i className="h-1.5 w-1.5 animate-bounce rounded-full bg-violet-300 [animation-delay:300ms]" /></span>Thinking through your request{loadingSeconds >= 1 ? ` · ${loadingSeconds.toFixed(1)}s` : "..."}</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="border-t border-white/[0.07] bg-[#0b1020]/95 px-4 py-4 backdrop-blur sm:px-8">
        <form onSubmit={handleSubmit} className="mx-auto max-w-4xl">
          <div className="flex items-end gap-2 rounded-2xl border border-white/[0.1] bg-white/[0.04] p-2 shadow-2xl shadow-black/20 transition focus-within:border-cyan-300/30 focus-within:ring-1 focus-within:ring-cyan-300/10">
            <textarea ref={textareaRef} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} disabled={isLoading} rows={1} placeholder="Message MISTY... / মিস্টিকে লিখুন..." className="max-h-40 min-h-11 flex-1 resize-none bg-transparent px-3 py-3 text-sm leading-5 text-slate-200 outline-none placeholder:text-slate-600 disabled:opacity-50" />
            <button type="submit" disabled={!input.trim() || isLoading} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-cyan-300 text-sm font-black text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-30" aria-label="Send message">↑</button>
          </div>
          <p className="mt-2 text-center text-[10px] text-slate-600">Enter to send · Shift + Enter for a new line · MISTY may make mistakes, verify important information.</p>
        </form>
      </div>
    </section>
  );
}
