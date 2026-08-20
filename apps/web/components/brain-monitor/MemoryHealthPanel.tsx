"use client";

import { BrainState } from "@/types";

interface FactAgingSummary {
  enabled?: boolean;
  total_decisions?: number;
  counts?: Record<string, number>;
  config?: {
    half_life_days?: number;
    prune_threshold?: number;
    junk_threshold?: number;
  };
  recent?: Array<{
    fact_key?: string;
    subject?: string;
    action?: string;
    confidence_before?: number;
    confidence_after?: number;
  }>;
}

interface ConsolidationSummary {
  enabled?: boolean;
  total_decisions?: number;
  counts?: Record<string, number>;
  config?: {
    rehearse_window?: number[];
    max_merged_per_sweep?: number;
    max_rehearsed_per_sweep?: number;
  };
  recent?: Array<{
    fact_key?: string;
    action?: string;
    confidence?: number;
    detail?: string;
  }>;
}

interface MemoryHealthPanelProps {
  brainState: BrainState | null;
}

function SectionTitle({ icon, label }: { icon: string; label: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-sm">{icon}</span>
      <span className="text-xs text-neural-muted uppercase tracking-wide">
        {label}
      </span>
    </div>
  );
}

function AgingDecisionRow({
  decision,
}: {
  decision: NonNullable<FactAgingSummary["recent"]>[number];
}) {
  const actionColor =
    decision.action === "protected"
      ? "text-neural-success"
      : decision.action === "pruned"
        ? "text-neural-error"
        : decision.action === "decayed"
          ? "text-neural-warning"
          : "text-neural-accent";

  return (
    <div className="flex items-center justify-between gap-2 text-xs py-1 border-b border-neural-border/50 last:border-0">
      <span className="text-slate-400 truncate font-mono" title={decision.fact_key}>
        {decision.subject || decision.fact_key}
      </span>
      <div className="flex items-center gap-2 shrink-0">
        {decision.confidence_before !== undefined && (
          <span className="font-mono text-neural-muted">
            {Math.round((decision.confidence_before ?? 0) * 100)}% →{" "}
            {Math.round((decision.confidence_after ?? 0) * 100)}%
          </span>
        )}
        <span className={`font-semibold uppercase ${actionColor}`}>
          {decision.action}
        </span>
      </div>
    </div>
  );
}

function ConsolidationRow({
  decision,
}: {
  decision: NonNullable<ConsolidationSummary["recent"]>[number];
}) {
  const actionColor =
    decision.action === "rehearsed"
      ? "text-neural-accent"
      : decision.action === "merged_winner"
        ? "text-neural-success"
        : decision.action === "merged_loser" ||
            decision.action === "quarantine_removed"
          ? "text-neural-error"
          : "text-neural-muted";

  return (
    <div className="flex items-center justify-between gap-2 text-xs py-1 border-b border-neural-border/50 last:border-0">
      <span className="text-slate-400 truncate font-mono" title={decision.fact_key}>
        {decision.fact_key}
      </span>
      <div className="flex items-center gap-2 shrink-0">
        {decision.confidence !== undefined && (
          <span className="font-mono text-neural-muted">
            {Math.round((decision.confidence ?? 0) * 100)}%
          </span>
        )}
        <span className={`font-semibold uppercase ${actionColor}`}>
          {decision.action}
        </span>
      </div>
    </div>
  );
}

export function MemoryHealthPanel({ brainState }: MemoryHealthPanelProps) {
  const aging = (brainState?.fact_aging ?? {}) as FactAgingSummary;
  const consolidation =
    (brainState?.consolidation ?? {}) as ConsolidationSummary;
  const counts = aging.counts ?? {};
  const consCounts = consolidation.counts ?? {};
  const agingActions = [
    "decayed",
    "refreshed",
    "protected",
    "pruned",
    "skipped",
  ];
  const consolidationActions = [
    "rehearsed",
    "merged_winner",
    "merged_loser",
    "removed",
    "quarantine_removed",
    "skipped",
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 mb-2">
        <h2 className="text-sm font-bold uppercase tracking-wider text-neural-accent">
          Memory Health
        </h2>
        <div className="flex-1 h-px bg-neural-border" />
      </div>

      {/* Fact aging card */}
      <div className="bg-neural-surface border border-neural-border rounded-lg p-3 flex flex-col gap-3">
        <SectionTitle icon="🕰️" label="Fact Aging — confidence decay" />
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-neural-bg/60 border border-neural-border rounded p-2">
            <div className="text-neural-muted uppercase tracking-wide text-[10px]">
              Half-life
            </div>
            <div className="text-neural-accent font-bold">
              {aging.config?.half_life_days ?? 90} days
            </div>
          </div>
          <div className="bg-neural-bg/60 border border-neural-border rounded p-2">
            <div className="text-neural-muted uppercase tracking-wide text-[10px]">
              Prune floor
            </div>
            <div className="text-neural-accent font-bold">
              {Math.round((aging.config?.prune_threshold ?? 0.35) * 100)}%
            </div>
          </div>
          {agingActions.map((action) => (
            <div
              key={action}
              className="bg-neural-bg/60 border border-neural-border rounded p-2 flex justify-between items-center"
            >
              <span className="text-neural-muted uppercase tracking-wide text-[10px]">
                {action}
              </span>
              <span className="text-neural-accent font-bold">
                {counts[action] ?? 0}
              </span>
            </div>
          ))}
        </div>
        {aging.recent && aging.recent.length > 0 && (
          <div>
            <div className="text-[10px] text-neural-muted uppercase tracking-wide mb-1">
              Recent decisions
            </div>
            {aging.recent.map((decision, index) => (
              <AgingDecisionRow key={index} decision={decision} />
            ))}
          </div>
        )}
        {(aging.total_decisions ?? 0) === 0 && (
          <div className="text-xs text-neural-muted italic">
            Waiting for the first autonomous reflection tick...
          </div>
        )}
      </div>

      {/* Consolidation card */}
      <div className="bg-neural-surface border border-neural-border rounded-lg p-3 flex flex-col gap-3">
        <SectionTitle icon="🌙" label="Consolidation — sleep-strengthening" />
        <div className="grid grid-cols-2 gap-2 text-xs">
          {consolidationActions.map((action) => (
            <div
              key={action}
              className="bg-neural-bg/60 border border-neural-border rounded p-2 flex justify-between items-center"
            >
              <span className="text-neural-muted uppercase tracking-wide text-[10px]">
                {action}
              </span>
              <span className="text-neural-accent font-bold">
                {consCounts[action] ?? 0}
              </span>
            </div>
          ))}
          <div className="bg-neural-bg/60 border border-neural-border rounded p-2">
            <div className="text-neural-muted uppercase tracking-wide text-[10px]">
              Rehearsal window
            </div>
            <div className="text-neural-accent font-bold">
              {(consolidation.config?.rehearse_window ?? [40, 70])
                .map((v) => `${v}%`)
                .join(" – ")}
            </div>
          </div>
        </div>
        {consolidation.recent && consolidation.recent.length > 0 && (
          <div>
            <div className="text-[10px] text-neural-muted uppercase tracking-wide mb-1">
              Recent decisions
            </div>
            {consolidation.recent.map((decision, index) => (
              <ConsolidationRow key={index} decision={decision} />
            ))}
          </div>
        )}
        {(consolidation.total_decisions ?? 0) === 0 && (
          <div className="text-xs text-neural-muted italic">
            No consolidation sweep has run yet.
          </div>
        )}
      </div>
    </div>
  );
}
