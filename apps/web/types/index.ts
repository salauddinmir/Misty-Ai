export interface EmotionalState {
  curiosity: number;
  confidence: number;
  uncertainty: number;
  attention: number;
  urgency: number;
  satisfaction: number;
  frustration: number;
  interest: number;
}

export interface Performance {
  total_cycles: number;
  success_rate: number;
  avg_confidence: number;
}

export interface BrainState {
  cycle_count: number;
  user_name: string;
  concepts: number;
  relations: number;
  working_memory_size: number;
  episodic_memories: number;
  semantic_facts: number;
  emotional_state: EmotionalState;
  active_concepts: Record<string, number>;
  performance: Performance;
}

export interface Concept {
  id: string;
  name: string;
  type: string;
  activation: number;
  created_at?: number;
  properties?: Record<string, unknown>;
}

export interface Relation {
  source: string;
  target: string;
  type: string;
  weight: number;
}

export interface ThoughtTrace {
  focus: string;
  intent: string;
  evidence_count: number;
  hypothesis_count: number;
  confidence: number;
  uncertainty: number;
  decision: string;
}

export interface SelfModel {
  identity?: string;
  capabilities?: string[];
  uncertainty?: number;
  [key: string]: unknown;
}

export interface Grounding {
  raw_input?: string;
  intent?: string;
  confidence?: number;
  evidence_count?: number;
  hypothesis_count?: number;
  strategy?: string;
  [key: string]: unknown;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  brain_state?: BrainState;
  processing_time?: number;
  cycle_count?: number;
  thought_trace?: ThoughtTrace;
  self_model?: SelfModel;
  grounding?: Grounding;
  phase_timings_ms?: Record<string, number>;
}

export interface ChatResponse {
  response: string;
  brain_state: BrainState;
  processing_time: number;
  cycle_count: number;
  active_concepts: Record<string, number>;
  emotional_state: EmotionalState;
  thought_trace?: ThoughtTrace;
  self_model?: SelfModel;
  grounding?: Grounding;
  phase_timings_ms?: Record<string, number>;
}

export type BrainEventType =
  | "phase_change"
  | "concept_created"
  | "relation_created"
  | "memory_stored"
  | "activation_spread"
  | "learning_event"
  | "state_update";

export interface BrainEvent {
  type: BrainEventType;
  data: Record<string, unknown>;
  timestamp: number;
}

export interface GraphData {
  concepts: Concept[];
  relations: Relation[];
  stats: Record<string, unknown>;
}
