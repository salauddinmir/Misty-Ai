# Phase 38 — Production issues reported by user (19 Aug 2026)

## User report (screenshots from misty-ai-web.vercel.app)
1. Neurons Active = 0 always
2. Robotic generic Bengali replies after heavy training ("চমৎকার প্রশ্ন!", "Very good question!", generic follow-ups)
3. Confidence 10-20%, Uncertainty 0%
4. Memory Recall 6

## Root causes confirmed locally + against production API
### A. Neurons Active = 0
- Frontend computes Neurons Active = len(active_concepts) from /api/brain/state.
- _phase_associate only populates active_concepts when parse_result.entities contains a `target` that exists in concept_graph. Ordinary Bengali/English messages (greetings, questions, statements) produce entities={} → no activation → always 0.
- Production /api/brain/state shows "active_concepts": {} even after many cycles (concepts=307, relations=61 so graph exists).
- FIX: activation should not depend on target entity only. Activate on:
  - any entities present (name, math_text, target, keywords)
  - recall hit concepts (topic of the matched semantic facts)
  - intent-level concept ("greeting", "math", "correction"...)
  - fallback: at least N concepts sampled from graph based on input keywords/words present in concept names (Bengali + English)

### B. Robotic generic replies
- Conversation driver (Phase 23-24) appends curiosity/follow-up question to EVERY reply → reads as "এইটা নিয়ে আরো জানতে চান?".
- _act_statement fallback: "মনে রাখো ..." template is heavy.
- Some fallbacks from variator are generic ("চমৎকার প্রশ্ন!").
- Note: responses ARE grounded when a knowledge answer is found, but (1) driver follow-up appended to everything, (2) corpus fallback used when semantic recall misses.
- FIX candidates:
  - Only append driver question when confidence is low or topic genuinely open (not for knowledge-rich answers) — make follow-up conditional on topic gap.
  - Ensure _act_query/_act_query_what return grounded answers from trained corpus (verify retrieval covers trained concepts like ফর্স, নিউটন).
  - Confidence semantics: response confidence should reflect evidence (semantic facts found) — currently static (0.5 etc.)

### C. Confidence/Uncertainty wrong
- emotional_state.confidence=0.3 in production; act confidence static; uncertainty=0 because prediction error low? Verify evaluate phase.
- FIX: derive confidence from recall evidence: known facts / queried; uncertainty = 1-confidence.

### D. Memory Recall 6
- Frontend Memory Recall = state.working_memory_size (6) — working memory is ephemeral, so stays small. Could map to episodic memories (10) or semantic_facts (798). FIX: show semantic_facts or add dedicated memory_retrievals counter per turn.

## Files involved
- brain/core/brain.py: _phase_associate (line ~1300), _phase_act (~1522), _phase_evaluate, curiosity prompt
- brain/core/state.py: active_concepts, emotional_state fields
- brain/nlu/parser.py: entity extraction (target only for queries)
- Frontend page chunk (Vercel project misty-ai-web, no git link; edit via Vercel deploy)

## Fix plan (Phase 38)
1. _phase_associate: broaden activation (entities + recalled topic concepts + word-match + intent concepts), keep deterministic.
2. Confidence: evidence-based — combine recall hits, grounding evidence, prediction confidence into response confidence; uncertainty = 1-conf.
3. Conversation driver: conditional follow-up (only when response came from unknown/corpus-fallback or explicitly asking for more), stop appending to grounded answers; reduce generic phrases ("চমৎকার প্রশ্ন") — replace with varied natural ones or drop.
4. Frontend: Memory Recall → semantic memory size (798) or recall counter; Neurons Active already OK once backend fixed.
5. Tests: new phase38 tests; benchmark must stay 57/57.

## Implementation details for fixes (to preserve context)

### A. Activation fix (brain/core/brain.py _phase_associate)
Replace the "target entity only" gate with a broader multi-path activation:
1. target concept (existing path) — entities.target/name
2. ALL present entities (name, math_text keywords, any string entity) → activate matching concepts via graph.get_concept_by_name + word-match on concept names (case-insensitive, substring, both BN/EN)
3. recall hits: for each semantic fact in recall_data["semantic_facts"], activate its subject concept
4. intent-level concept: map IntentType to concept name (greeting→"greeting", math→"mathematics", correction→"correction"...) and activate if exists in graph
5. If still empty → activate up to 5 concepts by best word overlap of input tokens with concept names
Cap activation size (max ~12) to keep state readable. Keep hebbian wiring after.

### B. Confidence fix (_phase_act returns)
Instead of static confidences: evidence-based confidence = base by strategy (0.9 math exact, 0.85 semantic fact answer, 0.7 corpus fallback, 0.5 unknown) then adjusted by recall evidence count. In _phase_evaluate store. Keep act's returned confidence used by chat route already. Uncertainty in emotional_state computed in evaluate: uncertainty = 1 - confidence (was hardcoded 0).

### C. Conversation driver (Phase 24 follow-up appended everywhere)
In _phase_act after curiosity_question: append follow-up ONLY when:
- confidence < 0.6 (answer was weak/unknown) OR
- intent in {CONVERSATION, UNKNOWN, CONTINUATION} OR
- parse_result has no knowledge grounding (recall semantic_facts empty AND answer from corpus fallback)
Do NOT append to: math/physics exact answers, QUERY_WHO/WHAT answered from semantic facts.
Also audit variator corpus for "চমৎকার প্রশ্ন" style generic openers → replace with natural replies tied to input content.

### D. Frontend Memory Recall
Deployed page chunk: s = Object.keys(n.active_concepts).length; Memory Recall value uses n.working_memory_size. Options in page-*.js (Next.js, hash chunk page-35aa7474b80a4c19.js; css db64a3535a123a2a.css). Vercel project misty-ai-web (prj_rlHQm5CJ1QROITDww9r8ivfK3Rw2) — no git repo link; must fetch file, edit, redeploy via Vercel MCP deploy_to_vercel or file-level API (check vercel tool list for create_file_for_project / etc.).
Better: backend exposes memory_recall in /api/brain/state (add top-level key "memory_recall": semantic memory size + episodic count), frontend reads state.memory_recall with fallback.

### Backend new state field
get_state() (brain.py ~2688) add "memory_recall": self.semantic_memory.size + len(self.episodic ...) — check episodic API. chat route (chat.py ~198) includes active_concepts already.

### Verify commands
- PYTHONPATH=. python3 tests/benchmark_conversation.py (must 57/57)
- python3 -m pytest -q (840+)
- ruff check brain/ apps/ tools/ tests/ && ruff format --check brain/ apps/ tools/ tests/
- curl https://misty-brain.onrender.com/api/brain/state | active_concepts non-empty after chatting
- gh run list after push

## Implementation progress (update as I go)

### DONE
- `_phase_associate` (brain/core/brain.py ~1301): rewritten to multi-path activation: target entity + entity sweep (name/subject/taught/target keys) + recall candidates + intent candidates + word-overlap sweep (max 5 concepts, max total 12 activations).
- Added 4 helpers after `_neural_associate`: `_associate_entity_candidates` (@staticmethod), `_associate_recall_candidates`, `_associate_intent_candidates` (maps intent value → concept name; uses `_ASSOCIATE_INTENT_CONCEPTS` dict), `_associate_word_overlap_candidates`.
- Need: add module-level `_ACT_PRONOUNS = frozenset({...})` constant near `_current_token_set` (line 75): Bengali pronouns সে, তার, সেটা, এটা, ওটা, ওটা, এই, সেই, এ, ও, তারা + English it/its/him/her/he/she/this/that/these/those/them/their.
- IntentType values confirmed: name_declaration, relation_declaration, query_who, query_what, statement, teach, correction, continuation, greeting, math, physics, capability_query, recognition_query, conversation, unknown.

### TODO (in order)
1. Add `_ACT_PRONOUNS` frozenset constant in brain.py.
2. Run ruff + pytest + benchmark to verify activation fix alone.
3. Driver follow-up fix: In brain.py `elif driver_plan.needs_followup...` (line ~578 after edits) — change: append follow-up ONLY when (a) confidence < 0.6 and topic non-empty, or (b) intent in conversation/unknown/continuation/correction, or (c) driver plan empathy kind. Skip for grounded knowledge answers (math/physics/QUERY answers with semantic facts). Simplest: in `_driver_plan`, pass `topic_facts` as-is; modify `plan_followup` in brain/dialogue/driver.py: line `shallow = (confidence < 0.6 or topic_facts == 0) and bool(topic)` — when topic_facts > 0 AND confidence >= 0.6, suppress needs_followup for non-empathy. Also the 'curious' user-state path always follows up — keep but limit with question_interval (already present).
4. Tone opener fix: brain/emotion/tone.py `_is_bengali(response)` decides BN/EN opener pool — for Bengali RESPONSES but user screenshot showed "চমৎকার প্রশ্ন!" for "কি খবর?" → _is_bengali works on response. Fix: high_interest op池 BN includes "চমৎকার প্রশ্ন!" — replace pool BN with neutral ones: "শুনে ভালো লাগল।", "এটা ভেবে দেখি।", "আসুন ভেবে দেখি।"; EN: "Let's think this through.", "Here's what I make of it.", "Let me think." Keep enthusiasm semantics but drop the sycophancy. Also tone.py line 153: `pool = _ENTHUSIASTIC_OPENERS_BN if _is_bengali(response) else _ENTHUSIASTIC_OPENERS_EN` — for Bengali user text but English response (name declaration bug screenshot 5), BN response check wrong → use user_text: `_is_bengali(user_text or response)`.
5. Uncertainty = 0 bug: brain.py ~516 uncertainty=max(0, 1-confidence) — production showed 0% because act confidence was high (0.9+ for weak answers?). Actually production showed uncertainty=0 with confidence 20% → check get_state emotional_state computation. Look at state.py / emotion state mapping — emotional_state in brain state may come from emotion.to_dict which decays uncertainty to 0. Check brain/core/brain.py get_state() and how emotional_state is populated (search "emotional_state" in brain.py).
6. Memory Recall fix: add "memory_recall" field to get_state() (brain.py ~2740 after edits) = self.semantic_memory.size + episodic size; update chat.py route BrainState model + response mapping (apps/api/routes/chat.py line ~198); optionally brain_stream.py too. Frontend chunk (page-35aa7474b80a4c19.js): value n.working_memory_size → n.memory_recall or fallback.
7. Add tests: tests/test_phase38_brain_activity.py — verify active_concepts non-empty for greetings, conversation, statements, correction, math; verify benchmark unchanged; verify driver doesn't append follow-up to grounded math answers.
8. Deploy: backend auto deploys on main push (Render linked to repo). Frontend: Vercel misty-ai-web (prj_rlHQm5CJ1QROITDww9r8ivfK3Rw2, team_GAiX7z0VlEsPZTxxVMX10AbD) — fetch deployed chunk JS, patch working_memory_size→memory_recall, redeploy via vercel MCP.
9. Verify: curl https://misty-brain.onrender.com/api/brain/state active_concepts non-empty + memory_recall field; smoke; push; CI green.

## Status snapshot (as of latest session)

### Activation fix — DONE & VERIFIED locally
- brain.py `_phase_associate` multi-path activation working. Test output:
  'ভাল'→active 1 [teaching], 'কি খবর?'→[conversation], 'নিউটনের দ্বিতীয় সূত্র কি?'→5 concepts incl নিউটনের দ্বিতীয় সূত্র।
- `_ACT_PRONOUNS` frozenset added at top (Bengali+English pronouns).
- `_resolve_activation_name`: exact match → semantic-memory alias predicate mapping → canonical graph concept.
- `_associate_word_overlap_candidates` + alias sweep.
- `_associate_intent_candidates` lazily registers missing intent concepts (conversation, teaching, misty...) with type "IntentConcept".
- NOTE: `_ASSOCIATE_INTENT_REGISTERED` is a CLASS-level set shared across Brain instances (fine for tests; acceptable).

### Driver follow-up fix — DONE in brain/dialogue/driver.py
- plan_followup now: only expansion when has_grounding (topic_facts>0 or has_related) AND (has_related or topic_facts>0); clarification offer only when not response; curious state with response → idle.
- Verified locally: 'কি খবর?'→ends "আপনার কি খবর?" (genuine); 'ভাল', 'কর্মক্ষেত্র ভাই', 'Okay' → no more canned follow-ups.

### Tone fix — TODO
- brain/emotion/tone.py line 29-38: _ENTHUSIASTIC_OPENERS_BN=["চমৎকার প্রশ্ন!","খুব ভালো প্রশ্ন করেছেন!","এটা আমারও পছন্দের আলোচনা।"] — replace with neutral BN openers: "এটা নিয়ে ভেবে দেখি।", "আসুন দেখি।", "বুঝেছি।"; EN: "Let's think this through.", "Let me look into that.", "Here's what I make of it."
- Line 147: `_is_bengali(response)` → should be `_is_bengali(user_text)` (otherwise Bengali user + English response → wrong pool; caused screenshot "That's a topic I enjoy discussing." + English fallback for name declaration).
- high_interest triggers when interest>0.7 AND curiosity>0.7 — production curiosity=0.97 → almost always enthusiastic. Also consider suppressing opener for closure turns (handled upstream in brain.py line ~591: `_closure_turn` skips opener — OK).

### Uncertainty = 0 bug — TODO
- Production brain state emotional_state.uncertainty showed 0% even with confidence 10-20%. Check brain.py get_state() — how emotional_state computed (search "emotional_state" in brain/core/brain.py ~2740 region) and brain/emotion/state.py EmotionalState.to_dict. Uncertainty may be computed as max(0, 1-confidence) but then decayed in emotion update (check brain/core/brain.py line ~1505 `self.emotion.update(...)` call and Uncertainty field derivation).

### Memory Recall / frontend — TODO
- Frontend chunk (misty-ai-web page-35aa7474b80a4c19.js) computes Memory Recall = `n.working_memory_size` from brain state JSON → must change backend key: BrainState needs `memory_recall` field; apps/api/routes/chat.py response mapping line ~198 uses `working_memory_size`; also apps/api/routes/brain_state.py (?) returns brain.state dict; update get_state() to include memory_recall = len(semantic facts)+episodic etc. Frontend: patch deployed JS via vercel MCP (team GAIx7z0VlEsPZTxxVMX10AbD, project prj_rlHQm5CJ1QROITDww9r8ivfK3Rw2, misty-ai-web, production deployment id 92668b07-84b8-4db0-94a0-8fbb344a87a0) — download chunk, replace key, redeploy.

### Benchmark 57/57, smoke ALL PASS after previous changes (verified before driver/tone edits; re-run after).

### Remaining TODO order
1. tone.py opener pool + _is_bengali(user_text) fix.
2. uncertainty fix (find source).
3. memory_recall state field (backend + frontend chunk patch).
4. tests/test_phase38_brain_activity.py (activation non-empty cases, driver grounding, benchmark unchanged).
5. ruff check+format brain/ apps/ tools/ tests/.
6. pytest full, benchmark 57/57, smoke.
7. push main; verify CI; Render auto-deploys; check production /api/brain/state active_concepts non-empty + memory_recall.
8. Frontend vercel redeploy chunk patch.

### Frontend API endpoints used by Vercel site
- POST /api/chat (misty-brain.onrender.com) → response JSON with conversation keys + BrainState fields.
- GET /api/brain/state → returns brain.state snapshot incl active_concepts, memory_recall (after fix).
- Frontend fetches: /api/brain/state every 3s; POST /api/chat on submit.
