# Phase 2 Research Notes for MISTY

## Research synthesis

### Active inference and predictive cognition

Constant, Clark, Kirchhoff and Friston describe active inference as maintaining probabilistic causal/generative models and reducing uncertainty through learning, perception and selective action. The engineering implication for MISTY is not to imitate biological consciousness, but to make each autonomous tick a closed loop: choose a high-value uncertainty, retrieve or observe evidence, update a model, and select the next bounded action. The loop must expose prediction, observation, error and update rather than only emit a final answer.

Source: Constant et al., “Extended active inference: Constructing predictive cognition beyond skulls,” *Mind & Language*, 2020, PMC9292365.

### Long-term memory

The 2025 survey “AI Meets Brain” treats memory as a lifecycle rather than a passive store: extraction/encoding, organization, retrieval, use, updating, strengthening or weakening, and security. It distinguishes episodic experience from semantic concepts and procedural experience/skills, and emphasizes provenance and memory security. For MISTY, this supports separate durable ledgers for episodes, semantic facts, procedures, hypotheses, evidence and contradictions instead of putting all cognitive history into unstructured episode JSON.

Source: Liang et al., “AI Meets Brain: A Unified Survey on Memory Systems from Cognitive Neuroscience to Autonomous Agents,” arXiv:2512.23343, 2025.

### Always-on state governance

The 2026 Always-OnAgents survey frames persistent agents as systems whose behavior depends on durable state, including memories, task ledgers, permissions, commitments, provenance, audit records, triggers and externally committed effects. It proposes assessing state items by authority, scope, mutability, provenance, recoverability and actionability, with a lifecycle of write, validate, organize, retrieve, act, update, forget, audit and rollback. For MISTY, every autonomous mutation should therefore have an authority/source, confidence, scope, revision path, recoverability and audit event.

Source: Ding et al., “Always-OnAgents: A Survey of Persistent Memory, State, and Governance in LLM Agents,” arXiv:2606.30306, 2026.

### Agent evaluation

The 2025 agent-evaluation survey organizes evaluation along objectives and process. Objectives include behavior/task completion, capabilities such as planning/reasoning/tool use/memory, reliability, and safety/alignment. Process dimensions include static versus interactive evaluation, data/benchmarks, metric computation, tooling and environment context. For MISTY, a benchmark cannot score only final text. It must separately score answer correctness, evidence/grounding, uncertainty calibration, memory retention, hypothesis falsification, latency, resource budget, deterministic replay and safety policy compliance in both Bengali and English.

Source: Mohammadi et al., “Evaluation and Benchmarking of LLM Agents: A Survey,” KDD 2025, arXiv:2507.21504.

## Design principles adopted for MISTY

1. **Closed-loop cognition:** every autonomous tick has a goal/uncertainty target, candidate evidence, prediction, test, error, update and trace.
2. **Evidence before belief:** no new durable semantic truth without provenance, source reliability, contradiction scan and promotion threshold.
3. **Typed persistent state:** hypotheses, evidence, contradictions, autonomy ticks and memory promotions need first-class records.
4. **Reversible learning:** tentative knowledge can be demoted, quarantined, revised or forgotten; no silent overwrite.
5. **Budgeted autonomy:** fixed tick timeout, bounded queue, rate limits, write budget, source allowlist and no unapproved external side effects.
6. **Inspectability without hidden chain-of-thought:** expose structured summaries, evidence references, prediction/error/update fields and timings—not private raw internal reasoning.
7. **Bilingual parity:** every capability benchmark has Bengali and English variants, with language-specific normalization and same acceptance thresholds where applicable.
8. **Production-grade recovery:** restart restoration, idempotent persistence, migration/versioning, audit replay and health metrics are part of intelligence, not afterthoughts.

## References

[1]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9292365/ "Extended active inference: Constructing predictive cognition beyond skulls"
[2]: https://arxiv.org/html/2512.23343v1 "AI Meets Brain: A Unified Survey on Memory Systems from Cognitive Neuroscience to Autonomous Agents"
[3]: https://arxiv.org/abs/2606.30306 "Always-OnAgents: A Survey of Persistent Memory, State, and Governance in LLM Agents"
[4]: https://arxiv.org/html/2507.21504v1 "Evaluation and Benchmarking of LLM Agents: A Survey"
