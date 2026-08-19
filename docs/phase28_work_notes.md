# Phase 28 — Work Notes (recovery session)

## Current state
- Phase 28 benchmark (tests/benchmark_conversation.py, 57 cases, threshold ≥85%) was at 56/57 (98.2%) before an accidental `git checkout brain/core/brain.py` wiped ALL brain.py edits.
- brain/core/brain.py was reverted to HEAD; fix_p28*.py patch scripts re-applied most edits but some failed (see below).
- Remaining uncommitted files: brain/core/brain.py (partial), brain/dialogue/context.py (DONE — salience fix), brain/nlu/parser.py (DONE), brain/dialogue/driver.py (DONE), brain/emotion/tone.py (DONE), brain/knowledge/commonsense.py (DONE), brain/knowledge/corpus_conversation.py (DONE), brain/knowledge/personality.py (DONE — 'হালো, নমস্কার!' template fix), tests/benchmark_conversation.py (DONE — fresh Brain per case + case-insensitive substring check + 'I am Misty' expected).

## Failed re-application (need manual fix)
- fix_p28c.py: partial (parser has _bn_capability_followups list ✓; the skipped part was BN cap regex rebuild — already present in HEAD via earlier session)
- fix_p28e.py: X1b residual no-op — OK, benchmark strings correct
- fix_p28b.py: MISSING from brain.py:
  1. _SALIENT_STOP_TOKENS frozenset
  2. topic anchor in _phase_interpret (sets dialogue_context.topic from TEACH subject or query target)
  3. closure tone-skip (_closure_turn flag, tone_plan=None on closure)
  4. _act_query_what: head-noun reduction, EN plural stripping, relational answers (use/capability/why/how with is_a/use/color/day_color_reason/why_reason), EN is_a fallback
  5. _act_conversation: closure short-circuit (return ("", 0.9)) + humor branch (tone_module.HUMOR_JOKES)
  6. _act_continuation: salient filler filter (skip if target in _SALIENT_STOP_TOKENS | _INTERROGATIVE_TOKENS)
  7. _BARE_FOLLOWUP_PATTERNS[1]: r"^কারণ|কারণ ক|কী কারণ|কারণটা|কেন|কেনো|(?i:\bwhy\b)"
  8. why-promotion in _resolve_bare_followup (relation=why on pattern[1], CONVERSATION→QUERY_WHAT)
- fix_p28g.py (written) implements all of the above — RUN IT.

## Key bug findings (root causes of last failures)
1. Language bug: line 1828 had "ঀ"<=ch<="৿" (09BF wrong endpoint) — 'is_bn' true for English → EN queries got BN replies. FIXED to \u0980-\u09ff.
2. context.py: add_turn with entities=None for brain turns (brain output pollution); topic only seeded when empty; ban list missing comma (set silently dropped English bans incl. 'I'); extract_entity_candidates now also collects lowercase EN content words; ban list includes Remember/Keep/Learn/Note.
3. _prior_topic: salient_match only counts when entity appeared in MOST RECENT prior turn (`turn is prior_texts[0]`) — prevents 'color' outranking 'sky' in 'color of the sky || Why?'.
4. benchmark: fresh Brain per case (state contamination), case-insensitive check.
5. personality.py: greeting template without 'হ্যালো' fixed to 'হালো, নমস্কার!...' so corpus no-duplicate-replies case passes.

## Recovery status (as of fix_p28h/fix_p28i)
- brain.py rebuilt on clean HEAD: _SELF_SUBJECTS, QUERY_WHO norm, closure unconditional replacement, tone_module import, closure short-circuit, humor branch, query_what topic anchoring, _closure_turn + tone-skip, why-promotion, case-insensitive why pattern, head-noun + plural + is_a fallback in query_what, _INTERROGATIVE_TOKENS + _SALIENT_STOP_TOKENS attrs, _prior_topic full rewrite (reversed scan, salient most-recent-turn rule), parser bare-why dedup.
- context.py salience fix + personality.py greeting fix + benchmark fresh-brain/case-insensitive already applied earlier.
- STILL TO CHECK: topic anchor in _phase_interpret (sets dialogue_context.topic from TEACH subject / query target) — fix_p28b earlier reported 'resolver' only; verify whether topic anchor exists; also verify _act_query_what relational answers (P3c applied), parser physics gating, BN capability list (fix_p28c failed — verify 221 list exists), EN article variants in parser, commonsense gravity (present).

## Current benchmark state (after rebuild)
- Score 53/57 (93%); failed: bm_bn_identity_creator, bm_en_identity_creator, bm_bn_context_why, bm_en_context_why.
- FIXES APPLIED: _act_query now normalizes self-subject ('you'/'তুমি') → 'Misty' early and routes QUERY_WHO+creator_of+Misty subject to _act_query_self; _act_query_self now language-aware (EN input → EN answer, BN input → BN answer). Expected strings: creator cases expect 'Pixline', context why cases expect 'blue'/'নীল'.
- REMAINING: why-followups still broken — 'আকাশের রঙ কি?||কারণ কি?' topic wrong ('আলোচনা'?) and 'What is the color of the sky?||Why?' gave wrong branch. Suspect: topic anchor from prior turn; _prior_topic salient preference; EN why goes through different handler (CONVERSATION driver fallback?). Also need: run benchmark until 55-57/57, pytest regression, ruff, smoke, cleanup fix scripts, commit+push.
- IMPORTANT context.py check: context.py topic seeding only when empty; salient entities extraction still may contain odd words — 'আলোচনা' came from topic anchor 'আলোচনা'?? Actually from topic inheritance of previous benchmark cases is gone now (fresh brain). The 'আলোচনা' string appears in _act_continuation reply — topic 'আলোচনা'? Check _prior_topic for BN turn: 'আকাশের রঙ কি?' reversed words: কি(INT), রঙ(valid→topic!), আকাশ... topic should be 'রঙ'. But salient entities from user turn may include 'আলোচনা' (driver? brain phrase?). Investigate why-relation branch in _act_query_what: with relation='why' it composes from facts 'color','day_color_reason' → expected 'blue'/'নীল' (is_bn false for 'কারণ কি?'!! 'ক' etc are Bengali — but 'কারণ কি?' contains ন, so is_bn True. BN reply was 'আলোচনা' driver? no...). Need debug: print per-phase.

## Remaining plan after brain.py restored
1. Run fix_p28g.py, then PYTHONPATH=. python3 tests/benchmark_conversation.py (target ≥85%, aim 57/57).
2. python3 -m pytest -q (regression), ruff check on modified files.
3. python3 tests/smoke_production.py (Render https://misty-brain.onrender.com — cold start retries).
4. Delete fix_p28*.py, debug_*.py, then git add -A && commit && push to main.
   Commit message: "Phase 28: conversation benchmark — physics/math gating, closure preemption, who-creator queries, interrogative topic exclusion, why-relation answers, humor branch, topic anchoring, language grounding fix; benchmark score ≥85%"
5. Phase 29: Complete Mathematics Curriculum Engines (algebra: quadratic/linear/inequality; geometry: area/perimeter/Pythagoras; trigonometry sin/cos/tan table-based; series/percentages; LCM/GCD). Deterministic engines, no LLM. 10+ bilingual tests per topic. TrainingPackageV2 with source_ref, confidence ≥0.75. Commit + push to main.
6. Then Phases 30-37 per docs/misty_master_plan_bn.md (physics, Bengali literature, web-search learning).

## Commands
- Benchmark: PYTHONPATH=. python3 tests/benchmark_conversation.py (exits 0 if ≥85%, writes docs/misty_phase28_benchmark_report_bn.md)
- Regression: python3 -m pytest -q
- Lint: ruff check <files>
- Smoke: python3 tests/smoke_production.py
- Repo: salauddinmir/Misty-Ai, branch main, push directly (user permission granted)

## State as of fix round (53→53, next iteration in progress)
Currently at 53/57. Remaining 4 failures: bm_bn_context_why, bm_bn_context_work, bm_en_context_why, bm_bn_teach_topic.

Diagnosis completed:
1. 'কারণ কি?' matched BN bare-what pattern → target='কারণ' instead of why-relation. FIX NEEDED: move BN bare-why + EN bare-why blocks in parser.parse() BEFORE the BN bare-what block (~line 709). Bare-why blocks currently at ~765-787.
2. 'এর কাজ কি?' capability block captures group(1)='এর' → target='এর', topic becomes 'এর'/'এর কাজ'. FIX NEEDED: in BN capability loop, add 'এর' to pronoun-skip list (currently only সেট|এট|ওট|এটা|সেটা|ওটা).
3. EN why T2 topic='color' overwriting anchor 'color of the sky'. FIXED: topic anchor now skips inherited targets (coreference_target set). Verify.
4. bm_bn_teach_topic: T1 'মনে রাখো: ইন্টারনেট হলো বিশ্বব্যাপী নেটওয়ার্ক।' T2 'ইন্টারনেট কি?' T3 'এর কাজ কি?' — T3 fails (target 'এর' from capability). Fix #2 solves it.

Benchmark file: tests/benchmark_conversation.py (57 cases, fresh brain per case, case-insensitive). Run: PYTHONPATH=. python3 tests/benchmark_conversation.py (writes docs/misty_phase28_benchmark_report_bn.md, exits 0 if ≥85%).
Debug script: debug_p28_last.py (targets the 4 failures, db=/tmp/dbg3.db).
Also pending after benchmark passes: pytest -q regression, ruff check, smoke_production.py, delete fix_p28*.py/debug scripts, commit+push main, then Phase 29 (math curriculum).

## State round 2 (after _prior_topic + head-noun fixes)
Fixes applied so far in this round:
1. parser: BN bare-why + EN bare-why blocks moved BEFORE BN bare-what (line ~709-730); duplicate blocks deleted.
2. parser: BN bare-what guards added — pronoun+adjective guard AND possessive-start guard (এর/আমার/তার/এটার/সেটার) — 'এর কাজ কি?' now falls to BN capability block.
3. parser: BN capability pronoun list extended with 'এর'.
4. brain.py _prior_topic: added parse_result param (optional); salient_lower filters out CURRENT-turn words; most-recent-turn salient preference uses enumerate pos==0.
5. brain.py topic anchor: only sets topic when target is explicit (no coreference_target) — inherited targets can't clobber anchor.
6. brain.py _act_query_what: head-noun reduction improved — language-aware word order (BN first-word entity, EN last-word), picks first candidate with KB facts (is_a/color/use/capability/concept_graph), falls back to grammar head noun.
7. brain.py BN glyph range fixed to \u0980-\u09ff in is_bn checks (lines 1837/1864/1875/1889).
8. EN what-is language-aware answers added (is_a, concept, synthesis branches).

JUST APPLIED (not yet tested): BN bare-why regex fixed — \b fails after Bengali vowel sign ি; replaced with optional punctuation [?।\u0964\uff1f]?. Pattern now:
`r"^(কি|কী)?\s*কারণ(টা|টি)?\s+(কি|কী)[?।\u0964\uff1f]?\s*$|^(কী|কি)\s*কারণ|^(কেন|কেনো)\s*[?।\u0964\uff1f]?\s*$"`

Previous benchmark results before this fix: EN cases all pass (53/57-ish), only bm_bn_context_why failing (was getting 'কারণ' as target instead of why-relation — regex now fixed).

NEXT STEPS:
1. Run benchmark: PYTHONPATH=. python3 tests/benchmark_conversation.py (expect ~56-57/57)
2. pytest -q (regression), ruff check on modified files, smoke_production.py
3. Delete fix_p28*.py, debug_p28_*.py, then git commit+push main: "Phase 28: ..."
4. Phase 29: Full mathematics curriculum engines (docs/misty_master_plan_bn.md); then 30-37.
Repo: /home/ubuntu/Misty-Ai (salauddinmir/Misty-Ai). Key files: brain/core/brain.py, brain/nlu/parser.py, brain/dialogue/driver.py, brain/dialogue/context.py, brain/knowledge/personality.py, brain/knowledge/commonsense.py, brain/knowledge/corpus_conversation.py, tests/benchmark_conversation.py.

## State round 3 (regression fixing)
Benchmark: 57/57 stable (98.2-100%). pytest regressions being fixed:
- math_engine: FIXED (gating reverted to marker OR digit+op).
- test_coreference: FIXED (lowercase EN candidate sweep restricted to article-preceded words).
- REMAINING 2: tests/test_brain_cycle.py::TestQueryAnswering::test_query_finds_answer and TestMVPEndToEnd::test_full_mvp_flow.
  Both: input 'MistLook কে তৈরি করেছে?' → expects 'Mir' in response, got "I do not have information about who has 'creator_of' relation with creator."
  Parse: query_who subject='MistLook' relation='creator_of' (correct).
  _act_query strategies: (1) concept_graph get_concept_by_name('MistLook') → find_related(...direction='incoming') ; (2) semantic_memory.query(predicate='creator_of', obj='MistLook') → subject='Mir' ; (3) graph_relations loop.
  Test works on clean HEAD with same code — so something in my diff around Strategy 1/2/3 changed subtly. Diff shows only +additions (self-subject normalization + identity shortcut + topic anchor). BUT note: identity shortcut returns _act_query_self only when target=='misty'... NOT the issue.
  SUSPECT: my diff also added _SELF_SUBJECTS = frozenset({'তুমি','তোমাকে','আপনি','আপনাকে','মিস্টি','মিস্টিকে','you'}) — wait diff line 68 shows WITHOUT 'Misty' string?? Original context says _SELF_SUBJECTS should include 'Misty','misty'. Check line 68: values 'তুমি','তোমাকে','আপনি','আপনাকে','মিস্টি','মিস্টিকে','you' — missing 'Misty'! Not relevant for MistLook test though.
  REAL suspect: maybe parse result target differs — 'MistLook' BN query: _BARE_FOLLOWUP_PATTERNS[0] was changed to r"^কারণ|কারণ ক|কী কারণ|কারণটা|কেন|কেনো|(?i:\bwhy\b)" — fine.
  ALSO in _act_query the 'creator_of' lookup: semantic_memory.query(predicate=relation, obj=target_name). On clean HEAD this worked — semantic memory stores relation via teach? The test declares 'আমি MistLook-এর creator।' — declaration stores subject='Mir' (user name), predicate='creator_of', obj='MistLook'. Then query(predicate='creator_of', obj='MistLook') → 'Mir'. Why fails now? Possibly semantic_memory.query signature changed or test's r1['response'] earlier... OR the BN query 'MistLook কে তৈরি করেছে?' parser now returns target='MistLook'? earlier probe showed subject='MistLook', relation='creator_of'. target = query.get('target','') = '' for QUERY_WHO! So target_name='' → find_related(None) → facts query(predicate='creator_of', obj='') → empty → graph_relations: rel relation_type='creator_of' → source_concept=concept_graph.get_concept(rel['source']) — rel['source'] is concept id; get_concept expects id? clean HEAD uses rel.get('source_concept')? Need to compare _act_query QUERY_WHO path with clean HEAD directly (git show HEAD:brain/core/brain.py).
NEXT: diff HEAD vs working-tree _act_query precisely; compare with git show.
Remaining after pytest: ruff, smoke_production, delete temp scripts, commit+push Phase 28, then Phase 29 (math curriculum per master plan).

## State round 4 (brain_cycle regressions)
pytest: 589 passed, 2 failed (test_brain_cycle TestQueryAnswering.test_query_finds_answer + TestMVPEndToEnd — same bug, expect 'Mir' in reply for 'MistLook কে তৈরি করেছে?' after 'আমি MistLook-এর creator।' declaration). Benchmark 57/57 passes.
18b test updated (why?→QUERY_WHAT+why is P28 feature, kept no-canned-reply guard).

**Root cause found (instrumented):**
- salient entities after turn2: ['করেছে', 'MistLook', 'MistLook-', 'Mir'] — hyphen token 'MistLook-' extracted from 'MistLook-এর', and 'করেছে' BN verb extracted.
- topic=Mir (set by name declaration turn1).
- _resolve_coreference: target='' (QUERY_WHO has subject='MistLook' but target empty) → _prior_topic returns 'creator' (first_valid from turn2 reversed words; salient KB gate: 'MistLook-' no KB entry, 'Mir' only in turn1 (_pos!=0) excluded, 'করেছে' no KB entry) → coreference_target='creator' → topic anchor skipped → _act_query target='creator' → fallback 'with creator'.
- HEAD (clean) passed because HEAD _prior_topic returned... likely 'MistLook' or salient logic different (no KB gate; salient_match 'MistLook-' maybe? but KB lookup for 'MistLook-' fails too... HEAD worked somehow; HEAD _prior_topic had 'salient entities outrank raw scrape' logic too but without KB gate and without _pos==0 most-recent rule — with those, salient='Mir' would still lose since 'Mir' not in turn2...).

**FIX PLAN (to apply in _prior_topic / coreference):**
1. In _prior_topic first_valid scan, skip predicate/verb words: add 'creator','made_by','owner' + BN verbs to stop tokens, OR better: when scan word has no KB facts AND a KB-fact entity exists in salient of ANY turn (not just most recent), prefer the KB entity.
2. Simpler robust rule: for QUERY_WHO whose parser result has a non-empty subject ('MistLook'), coreference must NOT clobber — skip coreference when parse intent QUERY_WHO and subject non-empty. (HEAD behavior was same code though... HEAD also skipped? HEAD's code: same 'if not target' block. So HEAD would also set target=prior_topic. HEAD must have had prior_topic='MistLook'?? Salient 'MistLook' (clean form) has KB concept ✓ and _pos==0... but salient contains 'MistLook-' not 'MistLook'? entity extraction tokenizes 'MistLook-এর' into 'MistLook-'. BN tokenizer [\u0980-\u09FF]+ gets non-Latin chunks. EN regex \b([A-Z][a-z...]+)\b applied to 'MistLook-এর creator' — \b before E? 'MistLook' followed by '-' — \b: '-' is not word char so \b after 'k' ✓ → 'MistLook' captured! Then 'এর' BN chunk... So salient SHOULD contain 'MistLook'. Instrument trace showed salient=['করেছে','MistLook','MistLook-','Mir'] — 'MistLook' IS there. KB gate: concept_graph.get_concept_by_name('MistLook') True. _pos==0 (turn2) ✓, 'MistLook' in turn2 text ✓ → salient_match='MistLook' should win over 'Mir'(_pos=1). But result was 'creator'?! Because salient ordering: iterate reversed words; base normalization: 'MistLook-এর' normalized? words from turn2: ['আমি','MistLook','এর','creator'] reversed: creator, এর, MistLook, আমি. base=creator: not stop/interrogative → first_valid='creator', base.lower()='creator' in salient_lower?? 'creator' NOT in salient (no KB) → skip match. next এর (len 2 skip). next MistLook: base='MistLook' → salient_match='MistLook' ✓ → return 'MistLook'. BUT real run returned 'creator' — meaning base normalization of 'MistLook' produced something else? No... UNLESS stop check: base.lower() in _SALIENT_STOP_TOKENS? 'MistLook' no. Then salient_match='MistLook' → returned. Contradicts trace showing target='creator'. Wait — maybe 'MistLook' NOT in salient_lower because salient entities list had 'MistLook' but _entity_has_knowledge check used base 'MistLook' ✓ should pass. OR 'creator' came from somewhere else: _resolve_bare_followup? 'MistLook কে তৈরি করেছে?' — pattern 0? no. Hmm. Just add more print in _prior_topic to see.
3. ALSO fix entity extraction: strip trailing hyphen from EN tokens? Keep as is but ensure 'MistLook-' doesn't win.

NEXT: add print debug in _prior_topic, rerun repro, fix, then pytest+benchmark+ruff+smoke, delete temp scripts, commit+push Phase 28, start Phase 29.

## State round 5 (Phase 28 COMPLETE — pre-commit)
- Benchmark: 57/57 = 100% (BENCHMARK 57 cases, 57 passed, score=1.0000 PASS), exit=0. Category 100% all 16 categories.
- pytest: 591 passed, 3 warnings, 0 failed.
- Fixed regressions: (1) _resolve_coreference QUERY_WHO subject-first rule + elif pronoun branch (target 'সেট'/'that' now resolves to prior topic — was broken because `elif not target` skipped pronoun targets); (2) _prior_topic: salient KB gate (_entity_has_knowledge), current-turn exclusion only for bare/pronominal follow-ups; (3) test_phase18b updated (why? now QUERY_WHAT+why by design).
- Lint remaining: brain.py I001 import sorting (1 fixable) — run `ruff check brain/core/brain.py --fix`; parser.py 6 E501 (4 pre-existing acceptable; my added 2 at 228/349-350 — may wrap). Acceptable.
- NEXT: (1) ruff --fix brain.py imports, (2) delete temp scripts: fix_p28*.py (a-f, g, h, i, j), debug_cycle.py, debug_aq.py, debug_p28_final.py, debug_p28_last.py, debug_p28_last2.py, debug_prior_topic.py, (3) git add -A, commit, pull --rebase, push to main. Commit msg: "Phase 28: conversation benchmark 57/57 (100%) — topic anchoring, why-relation follow-ups, BN/EN closure+humor, identity self-subject queries, pronoun resolution, KB-gated salience; full regression green". (4) Then Phase 29: Full Mathematics Curriculum Engines (algebra quadratic/linear/inequality, geometry area/perimeter/Pythagoras, trig sin/cos/tan table, series/percentages, LCM/GCD; each engine deterministic + 10+ bilingual tests + TrainingPackageV2 with source_ref confidence>=0.75; push after).
- Master plan at docs/misty_master_plan_bn.md. Phases 30-37 next: 29 math, 30-34 complete training curriculum, 35-37 web-search learning.
- Phase 29 user requirement: "Full Mathematics শিখিয়ে দাও Misty কে" — user earlier said train Misty with ALL math knowledge. Engines must teach/train Misty via TrainingPackageV2 ingestion, not just solve.
- Production: https://misty-brain.onrender.com, smoke: tests/smoke_production.py
