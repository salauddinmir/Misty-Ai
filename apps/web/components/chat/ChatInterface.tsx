"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessage as ChatMessageType, BrainState } from "@/types";
import { ChatMessage } from "./ChatMessage";
import { sendMessage } from "@/lib/api";

interface ChatInterfaceProps {
  onBrainStateUpdate: (state: BrainState) => void;
}

export function ChatInterface({ onBrainStateUpdate }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessageType = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: Date.now() / 1000,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendMessage(userMessage.content);

      const assistantMessage: ChatMessageType = {
        id: `msg-${Date.now()}`,
        role: "assistant",
        content: response.response,
        timestamp: Date.now() / 1000,
        brain_state: response.brain_state,
        processing_time: response.processing_time,
        cycle_count: response.cycle_count,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      onBrainStateUpdate(response.brain_state);
    } catch {
      const errorMessage: ChatMessageType = {
        id: `msg-${Date.now()}`,
        role: "assistant",
        content:
          "Unable to connect to MISTY brain. Please ensure the backend is running.",
        timestamp: Date.now() / 1000,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-neural-border">
        <h2 className="text-sm font-bold uppercase tracking-wider text-neural-accent">
          Chat Interface
        </h2>
        <div className="flex-1 h-px bg-neural-border" />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        {messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl mb-4">🧠</div>
              <p className="text-neural-muted text-sm">
                Start a conversation with MISTY
              </p>
              <p className="text-neural-muted/60 text-xs mt-1">
                Type a message to begin cognitive processing
              </p>
            </div>
          </div>
        )}
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex items-center gap-2 text-neural-muted text-sm pl-3">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-neural-accent rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 bg-neural-accent rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 bg-neural-accent rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
            <span className="text-xs">Processing...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-neural-border"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isLoading}
            className="flex-1 bg-neural-surface border border-neural-border rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder:text-neural-muted focus:outline-none focus:border-neural-accent focus:shadow-glow-sm transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-2.5 bg-neural-accent/10 border border-neural-accent/30 rounded-lg text-neural-accent text-sm font-medium hover:bg-neural-accent/20 hover:border-neural-accent/50 focus:outline-none focus:shadow-glow-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
