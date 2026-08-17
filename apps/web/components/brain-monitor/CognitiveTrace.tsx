"use client";

import { ChatMessage } from "@/types";

interface CognitiveTraceProps {
  message?: ChatMessage;
}

function pct(value?: number): string {
  return value === undefined ? "—" : `${Math.round(value * 100)}%`;
}

export function CognitiveTrace({ message }: CognitiveTraceProps) {
  const trace = message?.thought_trace;
  const model = message?.self_model;
  const grounding = message?.grounding;
  const timings = message?.phase_timings_ms;

  return (
    <section className="bg-neural-surface border border-neural-border rounded-lg p-3 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <span className="text-sm">◈</span>
        <span className="text-xs text-neural-muted uppercase tracking-wide">Inspectable Cognition</span>
        <div className="flex-1 h-px bg-neural-border" />
        <span className="text-[10px] text-neural-success">LIVE TRACE</span>
      </div>
      {!trace ? (
        <p className="text-xs text-neural-muted">Send a message to inspect MISTY&apos;s internal cycle.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div><span className="text-neural-muted">Focus</span><p className="text-slate-300 truncate">{trace.focus || "—"}</p></div>
            <div><span className="text-neural-muted">Intent</span><p className="text-neural-accent truncate">{trace.intent || "—"}</p></div>
            <div><span className="text-neural-muted">Evidence</span><p className="text-slate-300">{trace.evidence_count}</p></div>
            <div><span className="text-neural-muted">Hypotheses</span><p className="text-slate-300">{trace.hypothesis_count}</p></div>
            <div><span className="text-neural-muted">Confidence</span><p className="text-neural-success">{pct(trace.confidence)}</p></div>
            <div><span className="text-neural-muted">Decision</span><p className="text-slate-300">{trace.decision}</p></div>
          </div>
          <div className="border-t border-neural-border pt-2 text-xs">
            <div className="flex justify-between"><span className="text-neural-muted">Grounding</span><span className="text-slate-300">{grounding?.strategy || "workspace evidence"}</span></div>
            <div className="flex justify-between mt-1"><span className="text-neural-muted">Self uncertainty</span><span className="text-neural-warning">{pct(model?.uncertainty ?? trace.uncertainty)}</span></div>
          </div>
          {timings && Object.keys(timings).length > 0 && (
            <div className="border-t border-neural-border pt-2">
              <p className="text-[10px] text-neural-muted uppercase tracking-wide mb-2">Phase timings</p>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(timings).map(([phase, ms]) => (
                  <span key={phase} className="rounded border border-neural-border px-1.5 py-0.5 text-[10px] font-mono text-neural-muted">
                    {phase}: {Number(ms).toFixed(1)}ms
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
