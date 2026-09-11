"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { BrainMonitor } from "@/components/brain-monitor/BrainMonitor";
import { MemoryHealthPanel } from "@/components/brain-monitor/MemoryHealthPanel";
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
    if (event.type === "state_update" && event.data) setBrainState(event.data as unknown as BrainState);
  }, []);

  useEffect(() => {
    getBrainState().then(setBrainState).catch(() => undefined);
    const ws = new BrainWebSocket();
    wsRef.current = ws;
    ws.onEvent(handleBrainEvent);
    ws.onConnect(() => setConnected(true));
    ws.onDisconnect(() => setConnected(false));
    ws.connect();
    return () => ws.disconnect();
  }, [handleBrainEvent]);

  const handleBrainStateUpdate = useCallback((state: BrainState) => setBrainState(state), []);

  return (
    <main className="flex h-dvh flex-col overflow-hidden bg-[#070b16] text-slate-200">
      <header className="z-20 flex h-14 shrink-0 items-center justify-between border-b border-white/[0.07] bg-[#090e1c]/95 px-4 backdrop-blur sm:px-6">
        <div className="flex items-center gap-3">
          <div className="relative flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-300 to-violet-400 text-xs font-black text-slate-950">M</div>
          <div className="hidden sm:block">
            <div className="text-xs font-semibold tracking-[0.18em] text-slate-200">MISTY</div>
            <div className="text-[10px] text-slate-600">Artificial cognitive system</div>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.025] px-3 py-1.5">
          <span className={`h-1.5 w-1.5 rounded-full ${connected ? "bg-emerald-300 shadow-[0_0_9px_rgba(110,231,183,0.8)]" : "bg-amber-300"}`} />
          <span className="text-[10px] text-slate-500">{connected ? "Brain connected" : "Connecting"}</span>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <section className="flex min-w-0 flex-1 flex-col overflow-hidden lg:flex-[1.25]">
          <div className="hidden max-h-44 shrink-0 overflow-hidden border-b border-white/[0.06] bg-[#0a0f1d] md:block">
            <AvatarPanel messages={chatMessages} brainState={brainState} processing={isLoading} />
          </div>
          <div className="min-h-0 flex-1 overflow-hidden">
            <ChatInterface onBrainStateUpdate={handleBrainStateUpdate} onMessagesChange={setChatMessages} onProcessingChange={setIsLoading} />
          </div>
        </section>

        <aside className="hidden min-h-0 w-[38%] max-w-[560px] flex-col border-l border-white/[0.07] bg-[#090e1a] lg:flex">
          <div className="flex h-12 shrink-0 items-center justify-between border-b border-white/[0.06] px-5">
            <div>
              <div className="text-xs font-semibold text-slate-300">Cognitive monitor</div>
              <div className="text-[10px] text-slate-600">Inspectable internal state</div>
            </div>
            <span className="rounded-md border border-violet-300/10 bg-violet-300/[0.04] px-2 py-1 text-[10px] text-violet-200/70">LIVE</span>
          </div>
          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
            <BrainMonitor brainState={brainState} />
            <MemoryHealthPanel brainState={brainState} />
            <CognitiveTrace message={latestAssistantMessage} />
          </div>
          <div className="h-1/3 min-h-[180px] shrink-0 border-t border-white/[0.06]">
            <ActivityFeed events={events} />
          </div>
        </aside>
      </div>
    </main>
  );
}
