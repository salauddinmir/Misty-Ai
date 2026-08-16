"use client";

import { BrainEvent } from "@/types";

interface ActivityFeedProps {
  events: BrainEvent[];
}

function getEventIcon(type: string): string {
  switch (type) {
    case "phase_change":
      return "\u{1F504}";
    case "concept_created":
      return "\u{1F4A1}";
    case "relation_created":
      return "\u{1F517}";
    case "memory_stored":
      return "\u{1F4BE}";
    case "activation_spread":
      return "\u{26A1}";
    case "learning_event":
      return "\u{1F4DA}";
    case "state_update":
      return "\u{1F4CA}";
    default:
      return "\u{2022}";
  }
}

function getEventColor(type: string): string {
  switch (type) {
    case "phase_change":
      return "text-neural-accent";
    case "concept_created":
      return "text-neural-success";
    case "relation_created":
      return "text-blue-400";
    case "memory_stored":
      return "text-purple-400";
    case "activation_spread":
      return "text-yellow-400";
    case "learning_event":
      return "text-neural-warning";
    case "state_update":
      return "text-neural-muted";
    default:
      return "text-neural-muted";
  }
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function getEventDescription(event: BrainEvent): string {
  const data = event.data;
  switch (event.type) {
    case "phase_change":
      return `Phase: ${data.phase || "unknown"}`;
    case "concept_created":
      return `New concept: ${data.name || data.id || "unnamed"}`;
    case "relation_created":
      return `Relation: ${data.source || "?"} -> ${data.target || "?"}`;
    case "memory_stored":
      return `Memory stored: ${data.type || "general"}`;
    case "activation_spread":
      return `Activation: ${data.concept || data.id || "spread"}`;
    case "learning_event":
      return `Learning: ${data.type || data.description || "update"}`;
    case "state_update":
      return `State updated (cycle ${data.cycle_count || "?"})`;
    default:
      return event.type;
  }
}

export function ActivityFeed({ events }: ActivityFeedProps) {
  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-neural-border">
        <h3 className="text-xs font-bold uppercase tracking-wider text-neural-accent">
          Activity Feed
        </h3>
        <div className="flex-1 h-px bg-neural-border" />
        <span className="text-xs text-neural-muted">{events.length} events</span>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-2">
        {events.length === 0 ? (
          <div className="flex items-center justify-center h-full text-neural-muted text-xs">
            Waiting for brain activity...
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            {events.map((event, index) => (
              <div
                key={`${event.timestamp}-${index}`}
                className="activity-item flex items-start gap-2 py-1 text-xs"
              >
                <span className="flex-shrink-0">
                  {getEventIcon(event.type)}
                </span>
                <span className="text-neural-muted font-mono flex-shrink-0">
                  {formatTimestamp(event.timestamp)}
                </span>
                <span className={`${getEventColor(event.type)} truncate`}>
                  {getEventDescription(event)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
