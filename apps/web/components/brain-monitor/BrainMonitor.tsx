"use client";

import { BrainState } from "@/types";

interface BrainMonitorProps {
  brainState: BrainState | null;
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: string;
}) {
  return (
    <div className="bg-neural-surface border border-neural-border rounded-lg p-3 flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <span className="text-sm">{icon}</span>
        <span className="text-xs text-neural-muted uppercase tracking-wide">
          {label}
        </span>
      </div>
      <span className="text-lg font-bold text-neural-accent">{value}</span>
    </div>
  );
}

function ProgressBar({
  label,
  value,
  color = "neural-accent",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  const percentage = Math.round(value * 100);
  const colorClass =
    color === "neural-warning"
      ? "bg-neural-warning"
      : color === "neural-success"
      ? "bg-neural-success"
      : "bg-neural-accent";

  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between items-center">
        <span className="text-xs text-neural-muted">{label}</span>
        <span className="text-xs font-mono text-neural-accent">
          {percentage}%
        </span>
      </div>
      <div className="h-2 bg-neural-bg rounded-full overflow-hidden border border-neural-border">
        <div
          className={`h-full ${colorClass} rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function InternalState({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const percentage = Math.round(value * 100);

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-neural-muted w-20 truncate">{label}</span>
      <div className="flex-1 h-1.5 bg-neural-bg rounded-full overflow-hidden">
        <div
          className="h-full bg-neural-accent/60 rounded-full transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-mono text-neural-muted w-8 text-right">
        {percentage}%
      </span>
    </div>
  );
}

export function BrainMonitor({ brainState }: BrainMonitorProps) {
  const defaultState: BrainState = {
    cycle_count: 0,
    user_name: "",
    concepts: 0,
    relations: 0,
    working_memory_size: 0,
    episodic_memories: 0,
    semantic_facts: 0,
    emotional_state: {
      curiosity: 0,
      confidence: 0,
      uncertainty: 0,
      attention: 0,
      urgency: 0,
      satisfaction: 0,
      frustration: 0,
      interest: 0,
    },
    active_concepts: {},
    performance: {
      total_cycles: 0,
      success_rate: 0,
      avg_confidence: 0,
    },
  };

  const state = brainState || defaultState;
  const neuronsActive = Object.keys(state.active_concepts).length;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 mb-2">
        <h2 className="text-sm font-bold uppercase tracking-wider text-neural-accent">
          Brain Activity Monitor
        </h2>
        <div className="flex-1 h-px bg-neural-border" />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Neurons Active" value={neuronsActive} icon="⚡" />
        <StatCard
          label="Memory Recall"
          value={state.working_memory_size}
          icon="🧠"
        />
        <StatCard label="Associations" value={state.relations} icon="🔗" />
        <StatCard
          label="Learning Events"
          value={state.performance.total_cycles}
          icon="📚"
        />
      </div>

      {/* Current Goal */}
      <div className="bg-neural-surface border border-neural-border rounded-lg p-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm">🎯</span>
          <span className="text-xs text-neural-muted uppercase tracking-wide">
            Current Goal
          </span>
        </div>
        <span className="text-sm text-slate-300">
          {state.cycle_count > 0
            ? `Processing cycle #${state.cycle_count}`
            : "Awaiting input..."}
        </span>
      </div>

      {/* Confidence and Uncertainty */}
      <div className="bg-neural-surface border border-neural-border rounded-lg p-3 flex flex-col gap-3">
        <ProgressBar
          label="Confidence"
          value={state.emotional_state.confidence}
          color="neural-success"
        />
        <ProgressBar
          label="Uncertainty"
          value={state.emotional_state.uncertainty}
          color="neural-warning"
        />
      </div>

      {/* Internal States */}
      <div className="bg-neural-surface border border-neural-border rounded-lg p-3">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-sm">🔮</span>
          <span className="text-xs text-neural-muted uppercase tracking-wide">
            Internal States
          </span>
        </div>
        <div className="flex flex-col gap-2">
          <InternalState
            label="Curiosity"
            value={state.emotional_state.curiosity}
          />
          <InternalState
            label="Attention"
            value={state.emotional_state.attention}
          />
          <InternalState
            label="Interest"
            value={state.emotional_state.interest}
          />
          <InternalState
            label="Satisfaction"
            value={state.emotional_state.satisfaction}
          />
          <InternalState
            label="Urgency"
            value={state.emotional_state.urgency}
          />
          <InternalState
            label="Frustration"
            value={state.emotional_state.frustration}
          />
        </div>
      </div>
    </div>
  );
}
