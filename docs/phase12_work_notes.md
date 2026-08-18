# Phase 12–14 Work Notes (continuation backlog)

## User request
Continue MISTY work without stopping; implement next backlog items; push each completed phase to `main` (not a new branch). Production stack: Render (backend, https://misty-brain.onrender.com), Vercel (frontend), Supabase PostgreSQL. No commercial LLM dependencies; Bengali + English; inspectable thinking.

## Continuation backlog (in priority order)
1. PostgreSQL-backed training package catalog + persistence (Phase 12) — DONE partially; schema + Database method + registry integration tests.
2. Automated benchmark generation from curriculum manifests (Phase 13).
3. Harden active hypothesis loop + consolidation integration (Phase 14).
4. Full regression + production smoke tests + deployment rollout (Phase 15).
5. Deliver continuation results + updated backlog (Phase 16).

## Key architectural facts
- DB: `apps/api/database.py` class `Database`; driver selected via `MISTY_DB_URL` env (postgres → asyncpg, else sqlite/aiosqlite). `execute`/`fetchall` driver-uniform; postgres uses `$n` placeholders with `statement_cache_size=0` (Supabase PgBouncer). `_lock` serializes postgres queries. `initialize()` applies `database/schema_postgres.sql` on connect.
- PostgreSQL schema: `database/schema_postgres.sql`; SQLite: `database/schema.sql`. Both use `CREATE TABLE IF NOT EXISTS`, text primary keys, REAL timestamps, JSON in TEXT columns, `CREATE INDEX IF NOT EXISTS`.
- Training registry: `brain/knowledge/registry.py` — `TrainingPackageV2` (package_id, version, department, languages, provenance/source, confidence, concepts/relations/facts), `validate_package`, `Registry.register/get/list` (in-memory, version history).
- Curricula: `brain/knowledge/curriculum.py` (language/mathematics/physics/literature), `brain/knowledge/cognitive_curriculum.py` (reasoning/commonsense/memory/perception/emotion_simulation/self_model_and_planning). Each manifest: prerequisites, units, benchmark_ids, acceptance dict.
- Evaluation: `brain/evaluation/bilingual.py` (BilingualBenchmark, BenchmarkCase with case_id/language/prompt/expected_fragments/minimum_confidence/required_claims; brain.process() returns dict with response/confidence/grounding), `brain/evaluation/training_report.py` (build_training_report, department thresholds).
- Safety: `brain/safety/policy.py` (Decision: ALLOW/QUARANTINE/REQUIRE_APPROVAL/REJECT; evaluate_learning/evaluate_action; provenance required; external side effects rejected by default).
- Brain: `brain/core/brain.py` — `process()`, `autonomous_reflection_tick()` with `last_autonomous_tick` outcome (`hypothesis_supported`), evidence retrieval from semantic memory, `get_state()` includes `last_autonomous_tick`.
- Chat: `apps/api/routes/chat.py` JSON `/api/chat` + SSE `/api/chat/stream`; persistence decoupled to background task (RUF006: keep task reference); response includes thought_trace/self_model/grounding/phase_timings_ms.
- Frontend: `apps/web` Next.js; observability: `CognitiveTrace` panel wired in `page.tsx` from latest assistant turn metadata.

## Current state (verified)
- Local regression: 434 tests passed (2 benign warnings).
- Production: health OK, JSON chat BN/EN 200 (~3.5s cold), SSE streaming works, git clean at main `7789326`.
- Prior commits this cycle: b5e8aa8 (cognitive curricula), 062dbd3 (safety gates), f1e0ea1 (training reports), 7789326 (docs report).

## Phase 12 implementation plan
- Add `training_packages` table to both schemas (package_id TEXT, version INTEGER, department TEXT, languages JSON TEXT, package_json JSONB/TEXT, provenance TEXT, created_at REAL, UNIQUE(package_id, version)); indexes on package_id, department.
- `Database.save_training_package(dict)` driver-uniform upsert; `fetch_training_packages(department=None)` → list of dicts (json parse package_json).
- Registry wrapper that loads from DB on startup (best-effort; memory still authoritative source of truth, DB durable catalog).
- Tests: in-memory DB path; postgres schema idempotency.
- Brain `get_state()` already exposes last_autonomous_tick; consider `/api/training/catalog` endpoint (read-only, auth-free but low-risk GET).

## Phase 12 progress (update)
- DONE: `database/schema.sql` ও `database/schema_postgres.sql`-এ `training_packages` table যোগ (package_id, version PK composite; postgres JSONB, sqlite TEXT; indexes বাদ দেওয়া হয়েছে simple রাখার জন্য).
- DONE: `apps/api/database.py`-এ `save_training_package` (driver-uniform upsert, $n placeholders postgres) ও `load_training_packages(department=None)`. Lint clean after fixes (Mapping import added, noqa removed, long line split).
- DONE: `tests/test_training_package_persistence.py` — 5 tests (save/load, version history, department filter, empty catalog, provenance). 3 passed.
- BUG (fixing now): `load_training_packages` department filter-এ SQL concat ভুল — WHERE ORDER-এর পরে পড়ছিল। Fix: base = SELECT...FROM training_packages; postgres: f"{base} WHERE department = $1 ORDER BY registered_at DESC", sqlite: same with ? — NOTE previous edit attempt failed because file was ruff-formatted (string quotes); use match to read exact text.
- NEXT: run tests again → full regression → commit/push → Phase 13 automated benchmark generation from curriculum manifests (`brain/knowledge/curriculum.py`, `cognitive_curriculum.py` have units/tests dicts; `brain/evaluation/bilingual.py` has BenchmarkCase/BilingualBenchmark with brain.process() input prompt→response/confidence/grounding).

## Phase 12 completion state (verified)
The SQLite WHERE-bug is fixed, `tests/test_training_package_persistence.py` 5 tests pass, full regression suite shows **439 tests passed, 2 warnings** (up from 434). Remaining Phase 12 scope: catalog API endpoint and main push.

## chat.py contract (read for endpoint integration)
`apps/api/routes/chat.py`: router with `POST /chat` (ChatResponse model incl. grounding) and `POST /chat/stream` SSE (status/thinking → token → done). `_process_chat_turn(request, body)` returns ChatResponse; persistence via `_persist_chat_state` background task keyed on `app_state`. Brain state via `request.app.state.brain`, `request.app.state.database`. Any new route must live in this router module and pass ChatResponse or a new plain dict endpoint. The registry (`brain/knowledge/registry.py`) is dependency-free in-memory only — persistence is documented as external, so the catalog endpoint reads via `database.load_training_packages()` using the brain-state database instance.

## Next steps (remaining)
1. Add read-only `GET /api/training/catalog` route returning package catalog (uses request.app.state.database, best-effort exception handling). Add a light test in tests/test_training_package_persistence.py or new file test_training_catalog_route.py using TestClient if FastAPI available.
2. Commit/push Phase 12 to main.
3. Phase 13: automated benchmark generation from curriculum manifests (`brain/evaluation/benchmark_generator.py` generating BenchmarkCases from curriculum units/tests dicts), integration with `bilingual.py` runner and `training_report.py`, tests.
4. Phase 14: harden active hypothesis loop — inner_loop tick budget, metrics, consolidation integration with last_autonomous_tick.
5. Phase 15: full regression + production smoke tests (health, JSON chat BN/EN, SSE) + Vercel check via vercel MCP list_deployments.
6. Phase 16: Bengali continuation report + updated backlog to user.

## Catalog route test hang diagnose (in progress)
test_catalog_empty_when_no_packages PASSES (~1.7s). test_catalog_returns_saved_packages HANGS — module-level env check shows no MISTY_DB_URL/postgres env vars set, so DRIVER="sqlite". The difference: second test does `asyncio.run(_seed())` (in-process Database.initialize + saves) then `client.get("/api/training/catalog")` — the route reads via request.app.state.database which is a DIFFERENT Database instance initialized by lifespan with sqlite:///home/ubuntu/Misty-Ai/data/misty_brain.db, but my seed wrote to sqlite:///test_catalog_route.db — those are different files so the round-trip could never work anyway. The HANG likely comes from aiosqlite connection left open OR client fixture teardown; more likely the module-level `client = TestClient(app)` enters lifespan at module import, and lifespan's app.state.database stays pointing at the default db. Since media tests pass fine with module-level client, my inline asyncio.run(seed) may conflict with the event loop TestClient uses (starlette uses its own loop via portal). FIX: skip the round-trip seed test entirely (route behavior covered by persistence unit tests + empty-case route test). Keep only the empty catalog route test. Alternative: seed the default db file used by lifespan before the request.

## Phase 13 status (automated benchmark generation)
DONE: `brain/evaluation/benchmark_generator.py` written. It imports `brain.knowledge.curriculum`/`cognitive_curriculum` (unused import removed at lint time if ruff complains), `brain.evaluation.bilingual.BenchmarkCase, default_bilingual_cases`. API: UNIT_CASE_SPECS (per-department UnitCaseSpec tuples), language_prompt_for_unit, cases_from_specs, generated_benchmark_cases, curriculum_cases(dept), all_acceptance_cases(), unit_coverage_map(). Covers departments: language, mathematics, physics, literature, reasoning, commonsense, memory, perception, emotion, self_model.
NEXT: write tests/test_benchmark_generator.py (coverage counts, determinism, case shape, curriculum_cases unknown dept returns empty, all_acceptance_cases includes default_bilingual_cases), ruff + full pytest (currently 441 passing), commit/push.
REMAINING PHASES: 14 harden active hypothesis loop (brain/cognition/inner_loop.py tick budget + metrics; brain/core/brain.py autonomous tick integration; tests), 15 production smoke tests (health JSON chat BN/EN SSE at misty-brain.onrender.com; verify Vercel via vercel MCP), 16 Bengali continuation report + backlog to user.
REPO facts: remote main = github salauddinmir/Misty-Ai, deploy: Render backend misty-brain.onrender.com, Vercel frontend. Docs dir holds phase12_work_notes.md (internal notes file - may skip committing or keep small), misty_department_training_master_plan_bn.md, misty_department_training_implementation_report_bn.md.

## Phase 14 status (DONE, committed 7554e9c to main)
DONE: (1) brain/learning/consolidation.py — MemoryConsolidator now has max_consolidations_per_cycle=8 (cycle breaks at cap), safety_gate_threshold=0.5 routes candidates through evaluate_learning; failures go to rejected_candidates (quarantine with decision/reason/audit_code); candidate provenance = content.get("source") only (no fallback, so missing source -> LEARN_NO_PROVENANCE reject); observations = content.get("observations",1)+consolidation_count. (2) brain/core/brain.py — autonomous_reflection_tick: max_evidence_per_tick=4 attribute, evidence selection capped by budget, last_autonomous_tick now includes tick_index, evidence_budget, elapsed_ms, quarantined_candidates (time imported as time_module). (3) tests/test_phase14_hypothesis_loop.py — 14 tests. (4) tests/test_learning_improvements.py sink test updated (activation 0.9, source seed, observations 3). Regression: 467 passed.

## Phase 15 remaining steps
1. Full pytest -q locally (expect 467).
2. Smoke tests against production Render backend https://misty-brain.onrender.com: /health, POST /api/chat (BN "তুমি কে?" / EN "Who are you?"), /api/chat/stream (SSE), GET /api/training/catalog, GET /api/brain/state (verify last_autonomous_tick metrics present).
3. Vercel deployment verify via vercel MCP: list_deployments (project misty-ai-web per context).
4. If any route needs fix, push and wait for Render redeploy (cold start ~50s).
5. Phase 16: Bengali continuation report (docs/misty_department_training_continuation_report_bn.md): phases 13-14 summary, test evidence, production status, updated backlog.

## Test count history
Phase 12: 441 -> Phase 13 (e991c1f): 453 -> Phase 14 (7554e9c): 467 (current main).
Repo: salauddinmir/Misty-Ai, main branch, all pushes direct to main.

## Phase 15 status (in progress)
DONE: regression 469 passed (test_brain_state_route.py 2 + test_training_catalog_route 2 + others). apps/api/routes/brain.py — BrainStateResponse now has last_autonomous_tick (None-safe {}); get_brain_state coerces None to {}. Commit 8dc7dbe pushed.
Smoke results so far: /health 200 {"status":"healthy"}; POST /api/chat BN 200 (correct identity: "আমি Misty - Smart Artificial Brain। আমাকে তৈরি করেছে Pixline Incorporate... Founder Salauddin Mir (Netvai)"); EN 200; /api/chat/stream 200 SSE with event: status thinking -> event: token -> event: done; /api/training/catalog 200 packages=0.
Vercel: team "tophyint-9993s-projects" (id team_GAiX7z0VlEsPZTxxVMX10AbD); projects: misty-ai (prj_bZoACfsgpF51Z6fpjMQlHOL0mOiL), misty-ai-web (prj_rlHQm5CJ1QROITDww9r8ivfK3Rw2). misty-ai-web production deployments READY (2026-08-17); misty-ai-web.vercel.app HTTP 200 (0.3s). NOTE: frontend production deployment last run 2026-08-17 — no new code pushed to apps/web this cycle, so frontend is as-designed.
REMAINING: re-run smoke_production.py (brain_state_tick_metrics should PASS now after redeploy; Render cold start ~1-2 min for new build; wait then curl /api/brain/state verify last_autonomous_tick non-empty). Then Phase 16 report.

## Phase 17 (user live-test findings — screenshots 2026-08-18)
User tested on Vercel frontend + standalone Misty AI Chat app. Gaps found:
1. "x² - 4 = 0, x =" → "I could not safely solve" — quadratic equation solver MISSING. math_engine._parse_linear_equation only handles linear; regex allows only 0-9xX (no ², no Bengali digits inside equation side).
2. "১৫ × ৭ কত?" → "আমি এই mathematical format-টি এখনো সমর্থন করি না" — brain.py line ~972 fallback path taken: normalized text has Bengali digits but _extract_expression fails because the math-engine result None → falls back to language fallback (not engine). Actually: ১৫×৭ → _normalize translates digits OK, looks_mathematical: regex \d\s*[+*/] won't match "১৫ × ৭" (× is between digits). After normalize: "15 * 7 কত?" — looks_mathematical marker "কত" matches. Then _extract_expression strips ² non-ascii chars and removes non-ascii; for "15 * 7 কত" regex [^0-9a-zA-Z_+*/().,- ] drops 'কত', leaving "15 * 7" — should parse... BUT order: _parse_linear_equation runs BEFORE expression extraction? No — linear eq runs in parser loop before extract, fullmatch on "[0-9xX+*-/.() ]+=" won't match "15 * 7 কত?" → None. Then extract_expression. Hmm — so why did user get fallback message? Because brain.py calls math engine BEFORE normalizing? Check brain.py around line 972 (the fallback message). Likely brain passes raw text without Bengali normalization, OR math engine path skipped due to 'language' routing. VERIFY by reproducing locally: brain.process("১৫ × ৭ কত?") and brain.process("x² - 4 = 0").
3. Casual Bengali "কি খবর", "ভালো ব্যাপার", "তুমি কি ভাবছো?" → only echoes "আমি আপনার কথাটি শুনলাম" — intent parser missing conversational intents. Fix: add simple greeting/feelings intents in brain/cognition/language.py (check what exists) returning contextual responses instead of the generic echo.

Fix plan:
- math_engine.py: (a) normalize input BEFORE anything incl. equation regex — move _normalize to solve; (b) add _parse_quadratic_equation (ax²+bx+c=0 solver with discriminant, Bengali x²/২/² handling); (c) _parse_linear_equation accept Bengali digits (already normalized now); (d) looks_mathematical marker list fine.
- brain.py line ~972 fallback: make sure fallback message suggests formats incl. Bengali examples.
- language.py: add intents for কি খবর/কেমন আছো/how are you/good/ভালো → friendly contextual replies.
- tests: test_math_engine_bengali_digits, test_quadratic (x²-4=0 → x = ±2), test_casual_intents.
- After: regression, commit+push main, re-verify production chat with BN math + equation.

## Phase 17 root-cause verification (LOCAL REPRO DONE)
Local repro on current main build:
- "১৫ × ৭ কত?" → returns "105" (0.98) — WORKS on current build; user screenshot was an older build. NO FIX NEEDED (maybe add test).
- "x² - 4 = 0" → "I could not safely solve" — CONFIRMED. Quadratic solver missing in math_engine.py. _parse_linear_equation (line 202) regex only [0-9xX+*-/.() ] — no ² or superscript handling; linear eq parser runs BEFORE _extract_expression in solve() parser loop (line 64-73), and _extract_expression strips non-ASCII so x² becomes x → fails anyway.
- "কি খবর" → generic echo — casual intents missing. Echo text likely in brain/cognition/language.py or brain/core/brain.py ("আমি আপনার কথাটি শুনলাম").
Plan confirmed: add _parse_quadratic_equation to MathEngine (discriminant, x = ±2 for x²-4=0), add casual conversational intents (কি খবর/কেমন আছো/how are you → friendly replies), add tests, regression, commit+push main.

## Phase 17 implementation details (read parser.py + math_engine.py lines above)

### Findings
- "১৫ × ৭ কত?" WORKS on current build (user screenshot = older build). Add regression test only.
- "x² - 4 = 0" fails: math_engine._parse_linear_equation regex class [0-9xX+*-/.() ] has no ²/²/²-style superscripts; linear eq parser runs before _extract_expression which strips ²→x then fails. NO quadratic parser exists.
- Casual intents missing: parser._bn_greeting_patterns = (হ্যালো|হাই|নমস্কার|আসসালামু|সালাম); "কি খবর"/"কেমন আছো"/"ভালো ব্যাপার"/"তুমি কি ভাবছো" → UNKNOWN → STATEMENT → echo via _act_statement (brain.py line ~1289).

### Fix plan (in brain/math_engine.py)
1. In solve(), run _parse_quadratic_equation BEFORE _parse_linear_equation in parser loop (parser list order brain/math_engine.py line 64-73).
2. _parse_quadratic_equation(text): normalize with _normalize (Bengali digits, × → *, ² → **2); regex to find equation pattern containing x and power or x² marker: e.g. r"([0-9xX+\-*().% ]+?)(?:=|=|=)([0-9xX+\-*().% ]+)" with superscript handled via normalize first (² → ²? no — normalize replaces "²"→... need to add "²":"**2" replacement in _normalize). Then compute a,b,c coefficients for ax**2+bx+c=0 (move RHS to LHS), discriminant d=b²-4ac:
   - d>0: x = (-b±√d)/2a → "x = v1 অথবা x = v2" (Bengali response "x = ±2")
   - d==0: x = -b/2a
   - d<0: "কোনো বাস্তব সমাধান নেই" (with complex note)
   - a==0: fall back to linear solve (a, b, c → bx+c=0).
3. Quadratic detection: after normalize, if "x" present and ("**2" in side or "x²" marker) → quadratic. Implement by parsing each side into polynomial terms: split on +/− at paren-free top level, term regex r"^([0-9.]*)\*?x(?:\*\*2|\^2|²)?|([0-9.]+)$".
4. Keep confidence 0.98, category "quadratic_equation", steps include formula.
5. Also improve _normalize: add "²":"**2", "³":"**3", "¹":"**1" and superscript digits ⁰-⁹ mapping.

### Fix plan (in brain/nlu/parser.py) — new CONVERSATION intent
1. Add IntentType.CONVERSATION = "conversation".
2. Add _bn_casual_patterns list:
   - re.compile(r"(কি খবর|কেমন আছো|কেমন আছ|কি খবরে|ভালো ব্যাপার|বেশ)", re.UNICODE) → covers কি খবর, ভালো ব্যাপার
   - re.compile(r"(তুমি কি ভাবছো|কি ভাবছো|কি করছো|কি করছ)", re.UNICODE) → "তুমি কি ভাবছো?"
   - English: re.compile(r"(how are you|how are things|what are you thinking|nice|that's good|that is good)", re.I)
3. Detect BEFORE name declarations but AFTER greetings (order inside _try_bengali: after _bn_capability, before _bn_greeting? better: greetings remain first; casual AFTER greetings).
4. In brain.py _phase_act routing (line ~860-960): add branch intent == CONVERSATION → _act_conversation(parse_result).
5. _act_conversation: pattern-match variants → friendly contextual replies in Bengali with English fallback:
   - কি খবর → "আমি ভালো আছি! সাম্প্রতিকে আমার working memory-তে ..." (mention salient entity or default "আমি নতুন জ্ঞান শিখছি") — keep deterministic (no invented prose): use salient entities from dialogue_context; fallback "আমি ভালো আছি। আমি মিস্টির নতুন অংশ শিখছি। আপনার কি খবর?"
   - কেমন আছো → similar
   - ভালো ব্যাপার → "ধন্যবাদ! আমি খুশি।" (short)
   - তুমি কি ভাবছো → report from self_model (brain has self_model attr): "আমি আমার নিজের চিন্তা নিয়ে ভাবছি — ..." — simple deterministic: "আমি আমার শেখা নিয়ে ভাবছি; আমার কৌতূহল এখন high।"
   Keep responses SHORT (1-2 sentences), deterministic, bilingual pair logic.
6. Update grounding in language.py? intent "conversation" → claims default fine.

### Tests (tests/test_phase17_live_gaps.py)
- test_bengali_arithmetic_15x7 → "105" in response
- test_quadratic_x2_minus_4 → response contains "x = 2" and "-2" (or ±2)
- test_quadratic_perfect_square (x² + 4x + 4 = 0 → x = -2)
- test_quadratic_no_real (x² + 1 = 0 → no real solution message)
- test_casual_ki_khobor → not echo "শুনলাম"; contains "ভালো আছি"
- test_casual_en_how_are_you → friendly reply, not echo
- test_casual_bhalo_byapar → ধন্যবাদ reply
- existing 469 regression must stay passing.

### Math engine _normalize note
Add to replacements: "²":"**2", superscript digit range ⁰-⁹→0-9 translation (make mapping). Ensure looks_mathematical also matches "x²" marker (currently marker "equation"/"সমীকরণ"; regex \d\s*[+*/%=] — x²-4=0 has = so bool re.search("...") will match "="? regex requires \d before operator — "x² - 4 = 0" has "4 = 0": \d\s*[...] matches "4 =". OK.

## Phase 17 progress snapshot (saved before compaction)
DONE so far: (1) math_engine.py — superscript normalization (_SUPERSCRIPT_DIGITS ⁰-⁹ → **0..**9; caret→**; x² works), _parse_quadratic_equation added before linear in parser loop, _split_terms + _polynomial_coefficients helpers. Verified: x²-4=0 → "x = 2, x = -2"; x²+4x+4=0 → -2; x²+1=0 → no real solution BN message; x²-5x+6=0 → 2,3; x^2+2x+1=0 → -1; 2x+4=10 → linear still works x=3. (2) brain/nlu/parser.py — IntentType.CONVERSATION added; _bn_casual_patterns (কি খবর|কি খবরে|কেমন আছো|কেমন আছ|ভালো ব্যাপার|বেশ হয়েছে; তুমি কি ভাবছো|কি ভাবছো|কি করছো|কি করছ) and _en_casual_patterns (how are you/how's it going/how are things; what are you thinking (about); that's good/that is good/nice/sounds good/cool); both paths return CONVERSATION intent (conf 0.85) before greeting check. (3) brain/core/brain.py PLAN phase — added plan "converse_friendly" for CONVERSATION; ACT routing branch added (response, confidence = self._act_conversation(parse_result)) — NOTE: the ACT-branch insert produced odd indentation (line ~932 "                elif" double-indented + blank line 928) — MUST check with ruff; fix if lint complains.
TODO next: add _act_conversation method to Brain class (deterministic, pattern-match raw_text lowercase: BN "কি খবর/কেমন আছ" → "আমি ভালো আছি, ধন্যবাদ! আমি মিস্টি — নতুন জ্ঞান শিখছি; আপনার কি খবর?"; "ভালো ব্যাপার/বেশ" → "ধন্যবাদ! আমি খুশি।"; "ভাবছো/করছো" → report self_model.summary short phrase e.g. "আমি আমার নিজের চিন্তা নিয়ে ভাবছি; আমার কৌতূহল এখনো উচ্চ।"; EN equivalents: how are you → "I am doing well, thank you! I am Misty — learning new knowledge; how about you?"; that's good/nice → "Thank you! I am glad."; what are you thinking → self_model report). Also add conversation priority 0.45 in PLAN priority map. Confidence ~0.85.
Then: tests/test_phase17_live_gaps.py (7 tests per plan above), full regression (expect 469+7), ruff, commit+push main, production smoke verify (curl POST /api/chat with x² - 4 = 0 এব "কি খবর"), delivery.
Note: user's app screenshots used the OLD build; our local repro showed ১৫×৭ worked already (current build). So no Bengali-arithmetic fix needed — just add test test_bengali_arithmetic_15x7 (expect "105" in response).
User-facing context: user tests via misty-ai-web.vercel.app এব standalone "Misty AI Chat" app (backend: misty-brain.onrender.com).

## Phase 18 — Knowledge-Inference Synthesis (user feedback: "শুধু save করা কথার উত্তর দিচ্ছে, ভাবছে না")
Date: 2026-08-19

### User-observed gaps (screenshots 2026-08-19)
- "আকাশের রঙ কি?" → "ইন্টেন্ট নির্ভুলভাবে parse করতে পারছি না" (canned failure)
- "বুঝলাম না", "কি ব্যাপার?" → same canned reply repeated
- "x² - 7 = 0" → "Unable to connect to MISTY brain" (Render cold start drop during deploy)
- User demand: Misty must SYNTHESIZE answers from stored concepts/rules, not only echo saved phrases — "যা ভাবে তৈরি করে সেখান থেকে উত্তর দেবে"।

### Design: InferenceSynthesizer (brain/knowledge/inference.py)
1. Query understanding: extract candidate concepts from question via token overlap with knowledge graph concepts + semantic memory facts (existing similarity helpers).
2. Rule application: iterate graph relations (is-a, has-property, part-of) and formulas, chain facts depth ≤ 3; record derivation chain (steps).
3. Confidence: product of premise confidences × rule strength; mark answer "নিশ্চিত (known)" vs "অনুমান (inference)" explicitly.
4. Fallback: compose partial relevant facts into transparent reasoning paragraph, honest uncertainty; NEVER repeat canned "parse করতে পারছি না"।
5. Commonsense world layer (brain/knowledge/commonsense.py): curated bilingual facts (sky-blue, water-wet, Bangladesh-Dhaka, day/night, seasons, rain/clouds) loaded as in-memory layer at Brain init via registry loader, source=SourceRef("commonsense_layer").
6. ACT routing: hook synthesis into PLAN/ACT language-fallback path (~line 1290 echo); grounding.claims += "inference_synthesis".

### Phase 19 cold start
- Render cold start: frontend "Unable to connect" during deploy window. Fix: lifespan boot warmup (preload brain once at startup, avoiding first-request JIT compile delay) + verify health before chat. Frontend fallback message acceptable.

### Production
- Backend https://misty-brain.onrender.com, Frontend https://misty-ai-web.vercel.app. Verify pattern: tests/verify_phase17_deploy.py (polling requests loop).

### brain/core/brain.py key facts (Phase 18 hook points, verified line numbers)
- `_act_unknown(parse_result)` line ~1219: BN canned "আমি আপনার কথাটি বুঝতে চেষ্টা করেছি... parse করতে পারিনি" (conf 0.35) + EN; stores working memory "unknown_input". THIS is the message user hates on "আকাশের রঙ কি?".
- `_act_statement` line ~1298: "আমি আপনার কথাটি শুনলাম{context_part}, কিন্তু এখনো এটি সম্পূর্ণ বুঝতে শিখিনি" (conf 0.5) — repeated on "বুঝলাম না", "কি ব্যাপার".
- `_act_query_what` line ~1270: target_name lookup; fallback "আমি এখনো X সম্পর্কে জানি না" (0.3).
- `self.semantic_memory.query(subject, predicate)` → list of facts (fact.obj etc); `self.concept_graph.get_concept_by_name(name)` → concept (.concept_type, .concept_id); `self.concept_graph.add_relation(source_id, target_id, relation_type)`; `self.dialogue_context.get_salient_entities()` → list.
- Self introduction lives in `_act_query_self` line 1246 (creator_of → Pixline/Salauddin Mir/Netvai answer).
- Phase 18 hook: in `_act_unknown`, before returning canned reply, call `InferenceSynthesizer.synthesize(raw_text)` which queries semantic_memory (all subjects) + commonsense layer; if derivation found → return synthesized answer w/ confidence + derivation_steps in thought_trace.

## Phase 18 progress (2026-08-19)
CREATED: brain/knowledge/commonsense.py (167 bilingual facts + QUESTION_PATTERNS 22 preds + register_commonsense_layer(brain)).
CREATED: brain/knowledge/inference.py (InferenceSynthesizer: synthesize(question, brain) → InferenceResult(answer, confidence, steps, is_derived, language, matched_predicate, subject, obj, chain_depth); inline _BN_STOP/_EN_STOP; 3-2-1 word span matching; predicate detection; direct lookup + 1-hop chain; confidence = product).
EDITED: brain/core/brain.py — imports InferenceSynthesizer + register_commonsense_layer; self.inference_synthesizer in __init__; register_commonsense_layer(self) at end of _inject_training_knowledge; _act_unknown synthesizes before canned reply; _act_statement synthesizes before generic echo; _act_query_what synthesizes before "আমি এখনো X সম্পর্কে জানি না".
EDITED: brain/core/state.py — thought_trace dict + add_thought(name, steps).
REMAINING: tests/test_phase18_inference.py, full pytest, ruff, commit+push. Then 18b (graceful unknown), 19 (Render cold start), 20 (BN report).

## Phase 18 debug status (updated)
Bugs fixed in inference.py: (1) _lookup arg collision fixed; (2) _tokenize now regex-based BN_WORD_RE [\u0980-\u09ff\u09d7]+|[A-Za-z0-9_]+ (matras kept); (3) _extract_concepts: exact span match → token-in-subject containment → BN suffix stripping (ের/কে/র/টি/টা); (4) _EN_STOP removed color/colour/made (were killing predicate tokens); (5) answer grammar: possessive ের attached only when subject lacks genitive ending; (6) EN answer phrasing "Based on my stored knowledge: the X of Y is Z".
Verified locally OK: আকাশের রঙ→নীল (0.95), বাংলাদেশের রাজধানী→ঢাকা, মধুর স্বাদ→মিষ্টি, আগুন→তাপ ও আলো, What is capital of India→New Delhi.
"কি ব্যাপার?" → None (graceful) — will hit _act_statement synthesis-fallback → canned echo; Phase 18b will add CONVERSATION patterns.
brain.process() returns dict {response, confidence, intent, thought_trace, ...} — tests updated.
Next: ruff clean (check again), pytest all, commit+push, Phase 18b, 19, 20.
