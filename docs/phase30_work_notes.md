# Phase 30 — Physics Deep Curriculum (WORK IN PROGRESS)

## Master plan requirements (docs/misty_master_plan_bn.md lines 94-100)
- Units: kinematics (velocity, acceleration, free fall), force & Newton's laws, energy & power, waves & sound, electricity & magnetism (Ohm's law, series/parallel circuits), optics (light/mirrors/lenses).
- Every formula documented in a TrainingPackageV2.
- Test criterion: 10+ bilingual test cases per unit matching numeric expectations.

## Current physics_engine.py (216 lines) — supports ONLY:
- velocity (distance/time), force (F=ma), work (W=Fs), kinetic energy (½mv²), momentum (mv), gravitational PE (mgh).
- Also exports PHYSICS_CONCEPTS (21 names), PHYSICS_RELATIONS, PHYSICS_FACTS (no source_ref — old pre-V2 format), physics_package().
- No BN digits translation, no markers for waves/sound/electricity/optics/power(powered), Ohm, focal length, free fall, equations of motion.

## Plan for Phase 30
1. Extend brain/physics_engine.py:
   - BN digit translation + unit words (m/s, s, kg, N, J, W, A, V, Ω/ohm, Hz, m) markers.
   - New parsers: free-fall (s = ½gt²), equations of motion (v=u+at, s=ut+½at², v²=u²+2as), power (P=W/t, P=VI), Ohm (V=IR), series R (R=R1+R2...), parallel R (1/R=1/R1+1/R2...), P=I²R, wave (v=fλ), sound speed basics, current/charge (I=Q/t), voltage/energy (V=W/Q), optics mirror/lens formula (1/f=1/v+1/u, M=-v/u) with 'focal length', 'mirror', 'lens' markers.
   - Add markers: wavelength/frequency/hertz/ohm/ohms/resistance/circuit/voltage/current/circuit series/parallel/আলো/focal/focal length/principal/reflect/refraction/lens/mirror/দূরত্ব/তরঙ্গ/ধ্বনি/বিদ্যুৎ/রোধ/ভোল্টেজ/তড়িৎপ্রবাহ/আলোক/ফোকাস/রশ্মি/গতিশক্তি etc.
   - Keep existing API unchanged (PhysicsResult, solve, PHYSICS_ENGINE, physics_package).
2. New file brain/knowledge/training_physics.py (mirror training_mathematics.py pattern EXACTLY):
   - PHYSICS_CONCEPTS list (concept dicts with name/type/lang/topic), PHYSICS_RELATIONS, PHYSICS_FACTS (with definition/সংজ্ঞা predicates), PHYSICS_FORMULAS, PHYSICS_RULES, PHYSICS_EXAMPLES, PHYSICS_TESTS (~15 tests BN+EN covering all 6 units).
   - PHYSICS_SYNONYMS alias map ("newton's second law"→"Newton's Second Law", "ohm's law"→"Ohm's Law", "wave speed"→"Wave", etc.).
   - Content hash (_CONTENT_HASH = sha256 of payload including all lists), PACKAGE_ID = "misty-physics-phase30", TrainingPackageV2 via physics_curriculum_package(), register_physics_curriculum(brain) called at Brain init in brain/core/brain.py.
   - All facts/rules/formulas/examples/tests MUST have source_ref (_RECORD_SOURCE helper, use _attach(PHYSICS_FACTS)).
   - Registry import: from brain.knowledge.registry import TrainingPackageV2, SourceRef, PackageRegistry, validate_package.
3. Wire brain/core/brain.py: import register_physics_curriculum (alphabetical order after training_mathematics), call at init after register_mathematics_curriculum.
4. Update math-engine's "looks_mathematical"-style gating: check physics_engine usage in brain.py (find how brain routes math vs physics questions — probably in NLU/math gate). Do NOT break existing behavior; add physics markers for "watt"/"ohm"/"resistance"/"circuit"/"frequency"/"wavelength" so physics engine gets invoked.
5. Tests: tests/test_phase30_physics.py — engine tests (~30 numeric cases: velocity v=d/t, acceleration, free fall 5s→122.5m, Ohm, series/parallel R, P=VI, v=fλ, mirror formula), package validation + registration, brain concept questions ("newton's second law কি?", "what is ohm's law?", "বিদ্যুৎ প্রবাহ কী?"). Mirror test structure of test_phase29.
6. Brain must answer concept questions: ensure _act_query_what definition lookup finds physics facts (alias synonyms cover phrasal targets).
7. Quality gate: pytest -q (expect ~700+ passed), ruff check on changed files (line-length=120; BN unicode RUF001 allowed via noqa RUF001 on file header like training_mathematics.py does — check head of that file), benchmark 57/57, smoke ALL PASSED, test file 10x stability.
8. Commit + push to main (NEW commit, not amend).

## Key patterns (from Phase 29)
- training_mathematics.py: _RECORD_SOURCE = SourceRef(...); _attach(lst)=[dict(x, source_ref=_RECORD_SOURCE) for x in lst]; payload = json.dumps(SYNONYMS)+CONCEPTS+RELATIONS+FACTS+FORMULAS+RULES+EXAMPLES+TESTS concatenated; _CONTENT_HASH="sha256:"+hashlib.sha256(_PAYLOAD.encode()).hexdigest()
- register function: PackageRegistry().register(pkg); store MATH_SYNONYMS alias facts (aliases first, then canonical); then MATH_FACTS; returns count. Brain init calls after register_conversation_corpus.
- Content-hash must NOT include timestamps (retrieved_at) in payload!
- ruff: I001 fixable via ruff --fix --select I001; RUF001 via noqa on header; RUF005 avoid list concat via * unpack in call args; keep lines ≤120.
- Run commands: python3 -m pytest -q; PYTHONPATH=. python3 tests/benchmark_conversation.py; python3 tests/smoke_production.py; ruff check <files>.
- Physics routing: find where brain.py invokes PhysicsEngine (grep PHYSICS_ENGINE) to add new markers; check brain._act_query or similar math-gate function for physics marker list.

## Phase 31 preview (next): Bengali literature package (Tagore/Nazrul/Jibanananda), 15+ tests. Use the same TrainingPackageV2 pattern in brain/knowledge/training_literature.py. Only confirmed facts (Nobel 1913, Gitanjali, Sanchayita, Bidrohi, Gitanjali author etc.) — from established sources.

## Phase 30 FINAL FIXES (ALL APPLIED) — pre-commit status
All 7 failing tests FIXED. Root causes:
1. test_topics_covered used topics "mechanics"/"gravitation"; actual PHYSICS_FACTS topics: ("kinematics","forces","energy","waves_sound","electricity","optics").
2. BN concept name typo "ওহমের সূতr" in test_register_into_brain → explicit \u0993\u09b9\u09ae\u09c7\u09b0 \u09b8\u09c2\u09a4\u09cd\u09b0.
3. physics_engine.py line 109: BN wave literals MISSING ং্ (9cd) — "তরঙগ"(9a4 9b0 999 997) vs correct তরঙগ (9a4 9b0 999 9cd 997); same for কম্পাঙক. Replaced with \u escapes.
4. physics_engine.py line 193: \b boundary fails around BN পতন → added `or "\u09aa\u09a4\u09a8" in lowered` and added fallen/freely to ASCII group.
5. brain.py ~line 1859: TYPO predicate "সূতr" in _definition_or_concept + alias predicate list (actual facts use "সূতr" = \u09b8\u09c2\u09a4\u09b0). Fixed both lists.
6. inference.py: possessive concept names ("Ohm's Law" tokenizes ["ohm","law"]) never matched stored subject "ohm's law ...". FIX: _EN_STOP adds "s"; _extract_concepts builds _poss_norm normalized map (strip "'s", drop "s" tokens, collapse spaces) → original subject; used for span matching.
7. E501 long lines: BN probe strings moved to module constants (_BN_FALL_3, _BN_OHM_12_4, _BN_SERIES_6_3, _BN_PARALLEL_6_3, _BN_WAVE_50_4); noqa RUF001 headers on training_physics.py, physics_engine.py, test file.

STATUS: 66/66 phase30 tests PASS; 63/63 phase29 PASS; 720/720 regression PASS; benchmark 57/57 = 100%; ruff on phase files = clean; NEXT: smoke_production.py, stability re-run, commit+push Phase 30 to main, then Phase 31 (Bengali literature: brain/knowledge/training_literature.py — Tagore/Nazrul/Jibanananda).

## Phase 30 LINT FINAL ROUND
- All 7 test failures FIXED and tests pass (66/66, 720/720 full regression, benchmark 57/57=100%, smoke ALL PASSED).
- E501 long lines fixed in brain/physics_engine.py (wave/fall/work branches → _is_wave/_is_fall/_is_force vars; parallel-R steps split; capability obj shortened) and brain/knowledge/training_physics.py (5 obj strings shortened; BN test JSON split to 2 lines; 4 PHYSICS_TESTS entries split).
- tests/test_phase30_physics.py: BN phrase constants split to 2 lines (SERIES/PARALLEL), noqa RUF001 header removed (no RUF001 chars now in tests file).
- REMAINING: ruff final check on the 5 files, then full test run, then:
  git add -A; git commit -m "Phase 30: full bilingual physics curriculum + engine extensions..."; git pull --rebase origin main; git push origin main.
- THEN Phase 31: brain/knowledge/training_literature.py (Bengali literature: Tagore/Nazrul/Jibanananda) — same TrainingPackageV2 pattern; facts must be verified established facts (Gitanjali, Nobel 1913, Bidrohi by Nazrul, Jibanananda's Bonolota Sen etc.). After: tests/test_phase31_literature.py, lint, regression, benchmark, commit+push.
- Phases 32-37: social-cultural knowledge; self-assessment (reflection); full training batch + scorecard; batch web-learning; authorized web-learning API route POST /api/training/web_learn; post-learning self-assessment.
