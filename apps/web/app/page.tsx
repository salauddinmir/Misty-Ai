"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { BrainMonitor } from "@/components/brain-monitor/BrainMonitor";
import { CognitiveTrace } from "@/components/brain-monitor/CognitiveTrace";
import { ActivityFeed } from "@/components/brain-monitor/ActivityFeed";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { AvatarPanel } from "@/components/avatar/AvatarPanel";
import { BrainWebSocket } from "@/lib/websocket";
import { BrainState, BrainEvent, ChatMessage } from "@/types";
import { getBrainState } from "@/lib/api";

export default function Home() {
  const [brainState, setBrainState] = useState<BrainState | null>(null);
  const [events, setEvents] = useState<BrainEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef<BrainWebSocket | null>(null);
  const latestAssistantMessage = [...chatMessages].reverse().find((message) => message.role === "assistant");

  const handleBrainEvent = useCallback((event: BrainEvent) => {
    setEvents((prev) => [event, ...prev].slice(0, 100));

    if (event.type === "state_update" && event.data) {
      setBrainState(event.data as unknown as BrainState);
    }
  }, []);

  useEffect(() => {
    // Fetch initial brain state
    getBrainState()
      .then(setBrainState)
      .catch(() => {
        // Backend not available, use default state
      });

    // Connect WebSocket
    const ws = new BrainWebSocket();
    wsRef.current = ws;

    ws.onEvent(handleBrainEvent);
    ws.onConnect(() => setConnected(true));
    ws.onDisconnect(() => setConnected(false));
    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, [handleBrainEvent]);

  const handleBrainStateUpdate = useCallback((state: BrainState) => {
    setBrainState(state);
  }, []);

  return (
    <main className="flex h-screen overflow-hidden">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-6 py-3 border-b border-neural-border bg-neural-bg/90 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-3 h-3 rounded-full bg-neural-accent neural-pulse" />
          </div>
          <h1 className="text-lg font-bold tracking-wider text-neural-accent">
            MISTY
          </h1>
          <span className="text-xs text-neural-muted">
            Artificial Cognitive System
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              connected ? "bg-neural-success" : "bg-neural-error"
            }`}
          />
          <span className="text-xs text-neural-muted">
            {connected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex w-full pt-14">
        {/* Left Panel - Avatar + Chat */}
        <div className="w-1/2 h-full border-r border-neural-border flex flex-col overflow-hidden">
          <AvatarPanel
            messages={chatMessages}
            brainState={brainState}
            processing={isLoading}
          />
          <div className="flex-1 overflow-hidden">
            <ChatInterface
              onBrainStateUpdate={handleBrainStateUpdate}
              onMessagesChange={setChatMessages}
              onProcessingChange={setIsLoading}
            />
          </div>
        </div>

        {/* Right Panel - Brain Monitor */}
        <div className="w-1/2 h-full flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
            <BrainMonitor brainState={brainState} />
            <CognitiveTrace message={latestAssistantMessage} />
          </div>
          <div className="h-1/3 border-t border-neural-border">
            <ActivityFeed events={events} />
          </div>
        </div>
      </div>
    </main>
  );
}
