# Phase 48 — ONA Reasoning Layer (state notes)

## Goal
Connection-based reasoning over knowledge graph + semantic memory, so MISTY derives NEW conclusions from stored facts (transitivity, category inheritance, composition), with confidence decay along chains. Deterministic, no LLM.

## Existing context (audited)
- `brain/knowledge/inference.py` — `InferenceSynthesizer.synthesize(question, brain)` = NLU-fallback answer synthesis; chains facts depth<=2; NOT a general reasoning layer; doesn't store derived facts.
- `brain/graph/concepts.py` — `ConceptGraph`: DiGraph; `get_relations(cid, direction)` returns dicts with source/target/relation_type/relation_id/weight/confidence; `find_related`, `get_neighbors`, `get_concept_by_name`, `add_relation`, `add_concept`, `set_edge_weight`. `num_concepts`/`num_relations` properties.
- `brain/memory/semantic.py` — `SemanticFact(subject, predicate, obj, confidence, source, created_at, accessed_at)`; `SemanticMemory.facts` dict keyed "s:p:o"; methods: store_fact(subject, predicate, obj, confidence=1.0, source="user_input", created_at=None), query, get_facts_for_concept(concept_id), remove_fact(key), size().
- `brain/core/brain.py` — attrs: concept_graph (line 160), semantic_memory, inference_synthesizer (line 263), working_memory (capped 7). get_state() at 3803 with phase comments (Phase 45 block ends "consolidation": self.consolidation_engine.summary(),). Brain class name: Brain.
- Key rule: every new get_state() key MUST be added to apps/api/routes/brain.py BrainStateResponse (Dict[str, Any]|None field).
- Protected sources for aging: training/user_input/core/curriculum etc. New derived facts: use source="inferred".
- CI: ruff check + format brain/ apps/ tools/ tests/; pytest -q; benchmark PYTHONPATH=. python3 tests/benchmark_conversation.py (57/57); push main; CI wait ~220s; gh run list --repo salauddinmir/Misty-Ai --limit 1 --json headSha,status,conclusion.
- Tests pattern: asyncio.run() not loop.run_until_complete; ruff format before commit.

## Phase 48 design (agreed plan)
New module: `brain/learning/reasoning.py`
- `ReasoningEngine(brain)`:
  - Inference rule classes over semantic triples + graph edges:
    1. TRANSITIVITY: (A p B) ^ (B p C) → (A p C), conf = min*c1*c2 with per-hop decay 0.9
    2. CATEGORY INHERITANCE: graph edge A -(isa/type_of)-> B and fact about B → fact about A (via concept_graph.get_relations for "is_a"/"type_of"/"is_part_of" relation types)
    3. SYMMETRIC/REVERSE: e.g. "A causes B" → "B caused_by A" (predicate whitelist)
  - `_derive()` runs once per conversation turn (bounded: max 8 new derivations per call) over a window of recent (created_at within last HOUR or all facts if <50) — keep deterministic and cheap.
  - Stores derived facts into semantic_memory with source="inferred"; tracks _total_derived, _decisions log (bounded 100), last_derived list (5).
  - summary(): enabled, total_derived, rules_fired (per-rule counts), recent (5 derivations with rule/key/confidence).
- Wire: brain.reasoning_engine = ReasoningEngine(self) in __init__ (alphabetical: after learning_planner). In process() or a method called each turn — simplest: call in Brain.process after recall phase; name hook `_phase_reasoning()`. Add to get_state: "reasoning": self.reasoning_engine.summary().
- BrainStateResponse: add `reasoning: Dict[str, Any] | None = None`.
- DO NOT touch reflection tick (aging/consolidation). Reasoning runs per-turn like inference.
- Confidence composition: min(base1, base2) * hop_decay (0.9**hops), clamped to [0.05, 0.95]; derived facts must have conf >= 0.25 to store.

## Tests: tests/test_phase48_reasoning.py (~12)
- Engine instantiate; transitivity derivation + conf composition; inheritance via graph edge; symmetric rule; source=inferred; no derivation below conf floor; dedupe (don't re-derive existing fact); bounded per call (max 8); summary shape; brain.reasoning_engine attr; get_state includes reasoning; route response includes reasoning field.

## Report
docs/phase48_completion_report_bn.md — same format as phase47 report (header with Pixline/Salauddin Mir/Netvai, tables for gates, next steps: Phase 49 autonomous learning scheduler, Phase 50 memory history chart).

## Status tracker
- [x] Audit graph/semantic/inference APIs
- [ ] Create brain/learning/reasoning.py
- [ ] Wire into Brain + BrainStateResponse
- [ ] tests/test_phase48_reasoning.py
- [ ] lint/format/regression/benchmark gates
- [ ] commit+push, CI green
- [ ] Bengali report, deliver

## Progress tracker (updated)
- [x] brain/learning/reasoning.py created (ReasoningEngine: transitivity/inheritance/symmetric rules; store source="inferred"; conf floor 0.25; max 8/turn; log max 100; summary with total_derived/recent/rules_fired/config).
- [x] Wired into Brain: import after post_learning_loop; self.reasoning_engine in __init__ (after inference_synthesizer); derive() called in process() after _phase_learn before consolidate; get_state has "reasoning": self.reasoning_engine.summary().
- [x] apps/api/routes/brain.py: reasoning field added after consolidation.
- [x] tests/test_phase48_reasoning.py written (12 tests); used _fresh_brain() clearing facts+graph; removed dataclass field() misuse; fixed PERF/B007 lint.
- Current: 10 passed, 2 failing:
  1. test_inheritance_via_graph_edge (line ~70): assert 0 == 1. Cause: Brain().semantic_memory.store_fact() may NOT create graph concept "fruit" unless registered_concepts... concept_associations exists but no Concept object; graph.get_concept_by_name("fruit") returns None. FIX: in test (or engine), ensure concepts exist — engine should call brain.concept_graph.get_concept_by_name which only finds graph concepts. In _fresh_brain(), add concept + relation properly (mango node exists). But Brain() init also seeds corpus/identity facts — the "fruit" fact's subject isn't a graph node. Fix test: create "fruit" and "mango" concepts in graph, set name_index. Alternatively make engine robust: skip if no graph concept (it already does). So test must register concepts via brain.concept_graph.create_concept("fruit") BEFORE storing the fact? Actually store_fact doesn't touch graph. Just ensure test creates mango and fruit concepts, adds is_a relation.
  2. test_low_confidence_chain_not_stored: summary from a NEW engine sees total_derived=0 (decisions belong to first engine). FIX: reuse same engine for derive() and summary().
- Remaining: fix tests, re-run, ruff format brain/ apps/ tools/ tests/, full regression (expect 989+12=1001), benchmark 57/57, commit/push, CI check, Bengali report, deliver.
