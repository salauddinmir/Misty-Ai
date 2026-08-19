# Phase 39-41 State Notes (persistent across compaction)

## Task plan (current)
Phase 39 (learning roadmap) → 40 (long-term memory/personalization) → 41 (self-correction) → gates+push each → final Bengali report.

## User direction
- Continue phases per plan; ONA reasoning layer deferred to later if needed.
- Push to main after each phase; CI must be green; user speaks Bengali.

## Key facts (from earlier in session)
- Repo: /home/ubuntu/Misty-Ai, main branch, shell session "verify1".
- CI: ruff 0.16.3, `ruff check brain/ apps/ tools/ tests/` + `ruff format --check` on same paths; pytest tests/ -q matrix 3.10/3.11/3.12. First line of any file with Bengali visual-ambiguity needs `# ruff: noqa: RUF001`.
- Baselines: 840 tests pass, benchmark `PYTHONPATH=. python3 tests/benchmark_conversation.py` → 57/57=100%, `python3 tests/smoke_production.py` ALL PASS against https://misty-brain.onrender.com.
- Render auto-deploys from GitHub push (check via browser dashboard.render.com → web/srv-da16bpe7bikc738f34j0). Vercel frontend misty-ai-web.vercel.app (redeployed via vercel MCP earlier).
- GapAssessor (brain/learning/self_assessment.py): `evaluate(cases)`, `last_report()` returns GapReport; GapReport has entries (GapEntry: case_id, topic, query, expected, answer, status∈{known,unknown_honest,incorrect,missing}, confidence), counts known_count/unknown_honest_count/incorrect_count/missing_count, score/total are @property, to_dict() has 'gaps','honest_unknowns','total_cases'.
- brain.learning.training_scorecard.TrainingBatchVerifier.DEPARTMENTS: (("identity","training"),("commonsense","commonsense_layer"),("conversation","conversation_corpus"),("mathematics","misty-mathematics"),("physics","misty-physics"),("literature","misty-literature"),("culture","misty-culture")).
- WebSearchLearner (brain/knowledge/web_learning.py): async `ingest_batch(topics, topic_weights=None, min_agreement_sources=2, max_facts_per_topic=6)` → report dict. Has `post_learning_assessor` hook (Phase 37) set via `attach_to_learner(self.web_learner, self.post_learning_assessor)`.
- brain/core/brain.py: `self.gap_assessor = GapAssessor(self)` (line ~187), `self.web_learner = WebSearchLearner(self)`, `self.post_learning_assessor`, `autonomous_reflection_tick` (line ~3566), `self._learning_quarantine`, `self._assessment_mode`. get_state builds dict around line ~3400+; route model apps/api/routes/brain.py is a Pydantic-like response model — new brain state keys must be added there too (learned from Phase 38 fix).
- Brain wires imports alphabetical; brain.py already imports from brain.learning.self_assessment.

## Phase 39 implementation (learning_roadmap.py) — DONE
File written at brain/learning/learning_roadmap.py:
- LearningPlanner(brain): plan_next_topics(max_topics, budget, boost_topics) → LearningPlan(items: RoadmapItem(rank,topic,reason,gap_cases,gap_ratio,severity,weight,aliases)).
- Uses last gap report from gap_assessor, topic scores (asked/known/incorrect/unknown_honest/missing, severity = (2*incorrect + 1*unknown_honest + missing)/asked, recency_decay 0.15).
- TOPIC_ALIAS dict maps gap-case categories → web search topics (Bengali/English).
- Still TODO for Phase 39:
  1. Wire into brain: `self.learning_planner = LearningPlanner(self)` in Brain.__init__; add `learning_roadmap` to get_state output (plan.to_dict() if last_plan else []); add convenience `run_learning_roadmap(topics=None)` async method that uses web_learner.ingest_batch with weights then triggers post-learning assessor.
  2. Import at top (alphabetical within group): `from brain.learning.learning_roadmap import LearningPlanner`.
  3. Tests: tests/test_phase39_learning_roadmap.py (~10 tests) — plan from gap report, severity weights, boost_topics, budget distribution, coverage estimate, history, integration with brain.process.
  4. Run gates, commit, push, wait CI.

## Phase 40 plan (long-term memory/personalization)
- brain/memory/user_memory.py: UserProfileMemory — stores per-user conversation summaries (episodic digest), user facts ("বলেছেন তুমি ছাত্র"), last-seen timestamp. Keyed by user_id (default "default").
- Brain wires `self.user_memory`; process() writes episodic digest when session ends / per-turn digest append; response references user facts ("আপনি আগে বলেছিলেন...").
- /api/brain/users (optional) GET list; keep simple. Tests ~10. State field `user_memory` in get_state + route model.

## Phase 41 plan (self-correction)
- brain/learning/self_correction.py: CorrectionAuditor — detects challenge patterns ("ভুল", "এটা আগে বলেছিলে", "এটা ঠিক নয়"), re-checks fact vs semantic_memory, admits error with warm Bengali phrasing, stores corrected fact, tracks correction_count in state.
- Brain wires in process(): after response, check stored turn for challenge pattern → run auditor. Tests ~10.

## Report delivery
Final: docs/phase39_41_report_bn.md, attach to message.


## Phase 39 IMPLEMENTATION STATUS (updated)

### DONE
- brain/learning/learning_roadmap.py written: LearningPlanner(brain), LearningPlan, RoadmapItem. Methods: plan_next_topics(max_topics=5, boost_topics=()), estimate_coverage(gap_report=None), last_plan() -> plan, history. Topic alias map: identity,commonsense,conversation,mathematics,physics,literature,culture. Weights: _INCORRECT_WEIGHT=2.0, _HONEST_UNKNOWN_WEIGHT=1.0.
- brain/core/brain.py wired: self.learning_planner = LearningPlanner(self) (after post_learning_assessor); get_state includes "learning_roadmap" (plan.to_dict() or None); added async run_learning_roadmap(max_topics, boost_topics) hook (plans + calls web_learner.ingest_batch(topics, topic_weights=weights) -> returns dict with plan/ingestion); typing Sequence imported.
- lint clean (ruff check + format on both files).
- Gates: 861 tests pass, benchmark 57/57=100%, Render production live (memory_recall=815, active_concepts=12, learning_roadmap=None until first plan run).

### NEXT STEPS (in order)
1. apps/api/routes/brain.py BrainStateResponse model: ADD optional field `learning_roadmap: Dict[str, Any] | None = None` (currently NOT present — route drops it). Ruff format after.
2. Optional: add /api/training/roadmap endpoint (GET latest plan, POST to trigger) in apps/api/routes/training.py — guarded by MISTY_TRAINING_API_KEY like web_learn. Trigger: `await brain.run_learning_roadmap(...)`.
3. Write tests/test_phase39_learning_roadmap.py (plan generation, gap-based ranking, incorrect>honest severity, boost, history, run_learning_roadmap integration, API route key gate).
4. Commit+push, verify CI (runs d3e71dd-style: lint format + pytest 3.10/3.11/3.12), wait Render deploy, verify learning_roadmap appears in GET /api/brain/state after plan run.
5. Then Phase 40 (long-term memory/personalization) and Phase 41 (self-correction) per plan file docs/phase39_next_plan_bn.md.

### Environment facts
- Repo: /home/ubuntu/Misty-Ai, main branch, user account salauddinmir, GH_TOKEN works.
- Deploy: push to main → Render auto-deploys misty-brain.onrender.com (takes 5-10 min; verify after ~3 min).
- Frontend: Vercel misty-ai-web.vercel.app deployed via manus-mcp-cli tool call deploy_to_vercel --server vercel (projectName='misty-ai-web', files JSON via --input-file).
- Benchmark: PYTHONPATH=. python3 tests/benchmark_conversation.py → expect "57 passed, score=1.0000 (PASS)".
- Regression: PYTHONPATH=. python3 -m pytest -q (861 passed baseline).
- Smoke: PYTHONPATH=. python3 tests/smoke_production.py (transient SSL EOF ok, retry).
- ruff 0.16.3 CI; line-length 120; first line noqa RUF001 needed only if ambiguous Bengali chars flagged.

## Phase 39 COMPLETE (commit pending)

All Phase 39 work finished and gate-passed: route model now exposes `learning_roadmap` in `apps/api/routes/brain.py` BrainStateResponse; new `GET /api/training/roadmap` (read-only, no key needed) and `POST /api/training/roadmap` (MISTY_TRAINING_API_KEY gate + rate limit; body: max_topics 1-20, boost_topics list) added to training.py; `tests/test_phase39_learning_roadmap.py` (15 tests, all pass). End-to-end verified via TestClient: plan generates, ingestion runs, state key populated, GET roadmap echoes plan. Final gates: ruff check+format clean, pytest 876 passed (861+15), benchmark 57/57=100%, smoke production PASS. Note: gap_assessor stores reports via record_report() into _history; learning_roadmap to_dict keys are created_at, plan_id, total_planned_topics, items, topic_scores; RoadmapItem dict has no "priority" key. All-known topics get weight 0 but still appear in items (inspectability). Next: commit+push, then Phase 40 (long-term memory/personalization: brain/memory/user_memory.py UserProfileMemory) and Phase 41 (self-correction: brain/learning/self_correction.py CorrectionAuditor).

## Phase 40 IN PROGRESS (snapshot)

Phase 39 DONE: commit f2848cd pushed to main, CI green. Render auto-deploys from main.

Phase 40 done so far:
1. brain/memory/user_memory.py - COMPLETE (UserProfileMemory, UserProfile/UserFact/UserEpisode; record_turn extracts self-facts via _is_identity_claim markers; categories identity|occupation|preference|general; dedup via _fact_matches; personal_recall token-overlap; to_dicts/summary; _classify_language bn/en). ruff clean.
2. database/schema.sql + schema_postgres.sql - appended misty_user_memory table (user_id, memory_kind TEXT, memory_key TEXT, memory_json TEXT/JSONB, updated_at; PK triple; idx_user_memory_user).
3. apps/api/database.py - appended save_user_memory(user_id, payload{kind,memory_key,memory_json}) upsert (postgres ON CONFLICT DO UPDATE / sqlite INSERT OR REPLACE) and load_user_memory(user_id).

REMAINING Phase 40 steps:
- Brain.__init__: self.user_memory = UserProfileMemory(); get_state key "user_memory": self.user_memory.summary(); optional restore_user_memory(user_id) async via database.load_user_memory.
- apps/api/routes/chat.py: X-Misty-User-Id header (default "anon"); in persistence task call brain.user_memory.record_turn(user_id, utterance=body.message, reply=result["response"]).
- BrainStateResponse (apps/api/routes/brain.py): add user_memory optional field.
- New route apps/api/routes/memory.py: GET /api/memory/user?user_id=X&query=... -> personal_recall; include router in apps/api/main.py.
- Tests tests/test_phase40_user_memory.py (~10). Gates: ruff, pytest, benchmark 57/57, smoke. Commit+push main, CI, Render verify.
- Then Phase 41: brain/learning/self_correction.py CorrectionAuditor (challenge patterns; re-check vs semantic memory; warm bn apology; correction log). Wire in process cycle. Tests ~10. get_state "self_correction" + route model field.
- Final: docs/phase39_41_completion_report_bn.md attached to user message.

## Phase 40 COMPLETE (commit ed5f63f, pushed main)
Files: brain/memory/user_memory.py, apps/api/routes/memory.py, apps/api/routes/chat.py (_resolve_user_id, _record_user_turn, _persist_chat_state user_id param + episode persistence), apps/api/main.py (memory_router), apps/api/routes/brain.py (user_memory field in BrainStateResponse), brain/core/brain.py (user_memory wiring + state), database/*.sql (misty_user_memory table, IF NOT EXISTS, schema auto-applied in Database.initialize() on Render startup). tests/test_phase40_user_memory.py (26 tests). Post-push gate: ruff clean, 902 passed (876+26), benchmark 57/57, smoke PASS.
Schema applied automatically on Render cold start (full DDL, idempotent). CI runs on push to main; Render deploys auto.
Next: Phase 41 self-correction (brain/learning/self_correction.py CorrectionAuditor; wire in Brain process cycle: detect challenge patterns in NEXT turn's input or current utterance; re-check vs semantic_memory; warm bn apology; correction log in state "self_correction"; add field to BrainStateResponse). Tests ~10. Then final report docs/phase39_41_completion_report_bn.md.

## Phase 41 (snapshot — code complete, tests pending)
- brain/learning/self_correction.py: CorrectionAuditor(max_log_entries=50), CorrectionEntry(dataclass, to_dict), _detect_challenge (markers: 'ভুল','এটা ঠিক নয়','wrong','incorrect','false','not right','not true','আসলে তা না'...), audit(user_input, previous_answer, check_fn) -> (detected, note). Notes: accepted='আপনি ঠিক বলেছেন — আমার আগের উত্তরটা ভুল ছিল...সংশোধন করে নিচ্ছি'; unprovable='ধিমত করছেন...আগে সাবধানে ভেবে নিই'; generic='কোন বিষয়ে সঠিক তথ্য চাচ্ছেন বলুন'. _claim_tokens strips markers, keeps <=6 tokens len>2. summary() returns enabled/challenges_received/corrections_accepted/last_correction.
- brain/core/brain.py: CorrectionAuditor import (after self_assessment, line ~59), self.correction_auditor in __init__ (after user_memory, ~211), _run_correction_audit(text_input, current_response) defined before __repr__ (~3789); check_fn = semantic_memory.query(obj=token) any match -> contradicted. Called in _run_cycle after response built (before driver/tone), note prepended. self.correction_auditor.last_output = response set after self.state.last_output (~602). get_state key 'self_correction': self.correction_auditor.summary().
- apps/api/routes/brain.py: self_correction: Dict[str, Any] | None = None field added (after user_memory, ~51).
- tests/test_phase41_self_correction.py written (~11 tests incl. route TestBrainStateRoute).
- Remaining: run tests, lint, full gate (pytest expect 902+11=913, benchmark 57/57, smoke), commit+push, CI verify, Render verify, then final Bengali report docs/phase39_41_completion_report_bn.md (attach to user message with report; mention phases 39-41 complete, 39 roadmap, 40 user memory, 41 self-correction).
- Gate baseline after Phase 40: ruff clean, 902 tests, benchmark 57/57, smoke PASS. Phase 39 commit f2848cd, Phase 40 commit ed5f63f.

## Phase 42 (fact verification) — IN PROGRESS

### DONE
- brain/learning/fact_verification.py WRITTEN: FactVerifier(brain), VerificationEntry, _domains(url_str)→hosts. verify_triple(subject,predicate,obj,source_ref,observations=1) → entry with verdict∈{corroborated(single_source ≥2 independent domains), single_source, conflicted, retracted}. Retract: stronger evidence (observations>=stored observations which is stored fact.confidence) → semantic_memory.remove_fact(key); else conflicted (keep stored). confidence_after: corroborated=0.95, single=0.6. Log bounded 100. summary(): enabled/min/verified_total/corroborated/retracted/conflicted/single_source/recent(3).
- brain/knowledge/web_learning.py: WebSearchLearner.__init__ now creates self.fact_verifier = FactVerifier(brain) (lazy import). ingest() ALLOW path: _verify_and_resolve(candidate) → (verdict, reason, confidence_after); if contradicts_existing and verdict=="retracted" → quarantined+continue; else candidate.confidence = confidence_after before store_fact.
- brain/core/brain.py: self.fact_verifier = self.web_learner.fact_verifier in __init__ (line ~215); get_state key "fact_verification": self.fact_verifier.summary().
- apps/api/routes/brain.py: fact_verification: Dict[str, Any] | None = None field added to BrainStateResponse.
- tests/test_phase42_fact_verification.py written (17 tests).

### DEBUG FINDINGS (critical)
- SemanticMemory.query() kwargs are subject/predicate/obj (NOT subj). Test file uses subject=/predicate= after fix.
- evaluate_learning requires observations >= min_consolidation_observations (default 2) for ALLOW; provenance mandatory; contradicts_existing → QUARANTINE (first gate).
- Queries for "X" return 27k chars of facts (training corpus injects many). verify_triple retract works; earlier test failures were because query(obj='Y') matched stored fact obj 'Y'?? No — the assert [] was brain.semantic_memory.query(subject='X', predicate='is_a', obj='Y') returning [] because remove was followed by store only if verdict retracted — store happens in TEST via verifier.verify_triple? NO: verifier does NOT store (it only removes). The test asserted query(obj='Y') after verify — but entry.verdict=="retracted" removed Z and DID NOT store Y. Fix test: after retraction, challenger still not in memory; test should assert Z removed and Y NOT stored, OR call store_fact manually. Also test same_fact_not_conflict: verifier doesn't store; query('Y') was [] because fact was stored in Brain() then... actually it returned []?? Earlier assertion was `entry.verdict == "single_source"` — fine.
- Test fix needed: for retracted test, verifier removes old + verdict retracted; new fact NOT stored by verifier (brain ingest stores after _verify_and_resolve only if not retracted). So assertion "assert brain.semantic_memory.query(... obj='Y')" must be REMOVED, or verify separately.

### REMAINING Phase 42
1. Fix tests/test_phase42_fact_verification.py per findings above (17 tests; 5 currently failing: conflict_retract_with_stronger_evidence [assert [] on obj=Y], conflict_kept [verdict expected conflicted but got retracted? see line 72 'retracted'=='conflicted'], ingest_runs_verification [assert result.facts_learned []], contradicting [line 172 assert []], corroborated [line 188 assert []])
2. Note: conflict_kept test expects 'conflicted' but got 'retracted' — stored confidence 1.0 vs observations 1 → but _find_conflict returns observations=fact.confidence=1.0; challenger observations=1 → >=, so retracted. Fix: use stored confidence 0.9 or challenger observations=1 and expectation: when evidence equal → retract wins (by design). Adjust test: store at confidence 1.0, challenger observations=1 → retracted (acceptable); or test kept when stored obs > challenger: store confidence 2.0? Better: store fact with a wrapper attribute? SemanticFact.confidence used as observations proxy; simplest test design: conflicted case = stored fact.confidence=1.5 (evidence stronger than challenger obs=1).
3. ingest tests: facts_learned empty because _stub_search snippets' triple key support: 'The platypus is a monotreme' / 'lays eggs and nurses young' → different objects → each support entry observations=1 → REJECT (observations<2). Fix stubs: same-object snippets from same domain OR two snippets yielding same triple (e.g. 'The platypus is a monotreme' + 'The platypus is a monotreme mammal'). For corroborated test: both 'Mars is a planet' → same triple, two domains → observations=2 ALLOW, corroborated (2 domains).
4. Then ruff format/check, pytest full gate (expect 918+17=935), benchmark 57/57, smoke, commit+push, CI wait.

## Phase 42 STATUS: ALL GATES PASS — READY TO COMMIT+PUSH

Tests 935 passed, benchmark 57/57 (100%), smoke production ALL PASS, ruff clean, ruff format applied (3 files reformatted).

Files: brain/learning/fact_verification.py (FactVerifier/VerificationEntry/_domains), brain/knowledge/web_learning.py (fact_verifier in __init__, _verify_and_resolve + ingest hook), brain/core/brain.py (self.fact_verifier alias, fact_verification in get_state), apps/api/routes/brain.py (fact_verification field), tests/test_phase42_fact_verification.py (17 tests).

KEY SEMANTICS (for Phase 43+): verifier.verify_triple verdicts: retracted (observations >= stored confidence proxy), conflicted (weaker evidence — keeps stored), corroborated (2+ independent domains → confidence 0.95), single_source (confidence 0.6). Verifier NEVER stores challenger; only retracts + logs. ingest() tests: identical extract triple needed for observations>=2; asyncio.run() not get_event_loop() in tests (pytest-asyncio auto mode).

NEXT: commit+push Phase 42, wait CI, then Phase 43 (personal recall integration in conversation responses) per master plan.

## Phase 43 progress (Aug 20)
- DONE: brain.py — process(text_input, user_id), current_user_id, _last_personal_recall,
  _phase_personal_recall(parse) → dict (user_id, preferred_language, fact_matches[:4], episode_matches[:4]);
  merged into _phase_recall after semantic facts → recalled["personal_context"] + Evidence broadcast
  (personal_fact conf 0.85, personal_episode conf 0.7); result dict has "personal_recall": self._last_personal_recall;
  get_state: current_user_id + personal_recall.
- DONE: routes/chat.py — user_id resolved BEFORE brain.process; ChatResponse.personal_recall; result field passed.
- DONE: routes/brain.py — BrainStateResponse: current_user_id: str = "anon", personal_recall: Dict|None = None.
- DONE: tests/test_phase43_personal_recall.py — 11 tests pass (chat client needs database on app.state + brain router).
- ruff clean. Regression 946 passed.
- TODO: ruff format, benchmark 57/57, smoke, commit+push, CI, then phase43 report (phase 10 of plan).
