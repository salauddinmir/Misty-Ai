# Phase 29 — Full Mathematics Curriculum Engines (work notes)

## Completed: Phase 28 (committed 1957cbe on main)
Benchmark 57/57 = 100%, pytest 591 passed, production smoke ALL PASSED (Render live at https://misty-brain.onrender.com).

## Phase 29 audit findings

### Existing math infrastructure
- `brain/math_engine.py` (522 lines): MathEngine deterministic solver. Parsers: combinatorics, statistics, geometry, quadratic, linear, sequence, + generic AST expression evaluator (sqrt/sin/cos/tan/log/factorial). Covers: percentages(?), powers, roots, linear equations, quadratics, sequences, geometry, combinatorics, probability, stats. `mathematics_package()` = thin facts (8 facts only: defines branches of math, capability).
- `brain/physics_engine.py` (216 lines): PhysicsEngine + `physics_package()` (concepts/relations/facts).
- `brain/knowledge/training.py`: TrainingPackage (v1) — combined_package() = identity + literature + math + physics facts injected at Brain.__init__ (brain/core/brain.py ~line 208).
- `brain/knowledge/registry.py`: TrainingPackageV2 dataclass (package_id, department, version, languages [bn/en], license, source=SourceRef(title,url,retrieved_at,content_hash sha256:), prerequisites, concepts, relations, facts, rules(when/then), formulas(name/expression), examples(input/output), tests(id/input/expected_output), confidence_policy(default 0.8, requires_source=True)). validate_package() strict. PackageRegistry class with register/get/list; PackageRegistry().register() in commonsense.py:451 for conversation corpus.
- Registry packages are visible via /training_catalog route (tests/test_training_catalog_route.py); smoke shows packages=0 currently.

### Design decisions for Phase 29
1. Create `brain/knowledge/training_mathematics.py` containing:
   - MATH_DEPT_SOURCE = SourceRef(title="Misty Mathematics Curriculum (Phase 29)", url="https://misty-brain.onrender.com", retrieved_at, content_hash=sha256: of file content computed at module load — commonsense.py shows pattern).
   - Bilingual facts (facts with subject/predicate/obj, language-annotated), formulas, rules, examples, tests for 6 departments: arithmetic basics (fractions/percentages/decimals), algebra (linear, quadratic, inequalities), geometry (area/perimeter/volume/Pythagoras/angles), trigonometry (sin/cos/tan of standard angles + identities), series/sequences (AP/GP, sums), LCM/GCD/number theory.
   - `mathematics_curriculum_package()` -> TrainingPackageV2; register() via PackageRegistry at module import (like commonsense).
2. Also enrich MATHEMATICS_FACTS in math_engine.py with per-topic concept definitions? (Optional, keep facts in v2 package.)
3. The math_engine already SOLVES these; Phase 29 is about TEACHING the curriculum: facts store formulas (e.g., "quadratic formula: x = (-b ± √(b²-4ac))/2a" as formula record), engine already computes answers. Add bilingual formula descriptions as facts so brain can EXPLAIN (query_what relational answers pull from semantic memory).
4. Tests: new file tests/test_phase29_mathematics.py with 10+ BN and 10+ EN cases per topic (solve outputs via MathEngine) + curriculum ingestion + registry validation + chat integration (brain answers math-concept questions like "quadratic formula কী?").
5. Keep all facts with confidence>=0.75 and source_ref (sha256:...) to pass validate_package.
6. content hash must match file hash. commonsense.py computes hash as sha256 of the concatenated corpus content; replicate that pattern. Check commonsense.py:440-460 for the exact pattern.

## Phase 29 remaining steps
1. Check commonsense.py hash pattern.
2. Build brain/knowledge/training_mathematics.py (6 topics × bilingual facts/formulas/examples/tests).
3. Build tests/test_phase29_mathematics.py.
4. Run pytest, ruff, benchmark, smoke; commit + push main.

## Implementation state (round 1)
- CREATED brain/knowledge/training_mathematics.py with MATH_CONCEPTS (bilingual), MATH_RELATIONS, MATH_FACTS (topics: arithmetic_pct, algebra, geometry, trigonometry, series, number_theory; each fact has lang + confidence; topic-concepts pre-attached with source_ref), MATH_FORMULAS, MATH_RULES, MATH_EXAMPLES, MATH_TESTS (15 tests), _CONTENT_HASH=sha256 of canonical JSON payload, mathematics_curriculum_package() -> TrainingPackageV2 (validates: default 0.8 policy, requires_source True, records carry source_ref), register_mathematics_curriculum(brain) that calls PackageRegistry().register() + creates concepts + adds semantic facts (query subject/predicate to avoid dup).
- PENDING: verify semantic_memory has add() method — grep brain/memory/semantic*.py; concept_graph.create_concept(name, concept_type=).
- TODO: integrate into Brain.__init__ via Phase-28 style registration (register_conversation_corpus pattern ~line commonsense 440-460). Add call in brain/core/brain.py near register_conversation_corpus (search "register_conversation_corpus" usage in brain.py).
- TODO: tests/test_phase29_mathematics.py — cover: package validation (PackageRegistry register succeeds), MathEngine solves the 15 test cases (lcm/gcd/pct/quad/pythagoras/area/circle/ap/gp/sin/tan/linear/sqrt/triangle), brain answers concept questions via chat ('quadratic formula কী?'/'what is the quadratic formula?') in BN/EN, registry listing includes package.
- math_engine supports: _parse_quadratic_equation, _parse_linear_equation, _parse_geometry, _parse_combinatorics, _parse_statistics, _parse_sequence + generic eval with sqrt/sin/cos/tan/factorial. Percentages? check _normalize — likely plain expressions only; test '15% of 300' may not parse via expression path — verify; if unsupported, engine returns None (fine; concept answers come from facts).
- LCM/GCD: check if math_engine has lcm/gcd parsing — probably NOT; my tests expect engine to solve. Verify; if missing, ADD lcm/gcd parsers to math_engine (Euclidean algorithm + 'lcm of a and b' pattern, both BN 'গ.সা.গু'/ 'ল.সা.গু'). That is part of Phase 29 engine work.
- After: pytest, ruff (no E501 in my new files; line len 120), benchmark 57/57, smoke, commit + push main.
- Commit message idea: "Phase 29: full bilingual mathematics curriculum — 6 topics (arithmetic/percentages, algebra, geometry, trigonometry, series, number theory), registry package with provenance, LCM/GCD/percentage engine support; regression green".

## Engine test status (latest probe)
Curriculum package VALIDATES & registers now (semantic facts 393 after init; registry list() works per-instance — Brain has NO registry attr; commonsense registers its package at line 451 of commonsense.py). MATH_FACTS must carry source_ref via _attach(); _topic_concepts already has it. Package: 77 concepts, 87 facts, 13 examples, 15 tests.

math_engine gains: _parse_number_theory (LCM/GCD en+bn markers ল.সা.গু/গ.সা.গু/লসাগু/গসাগু/hcf) + markers in looks_mathematical. BN LCM/GCD OK.

Engine test results for MATH_TESTS (15): 9 pass, 6 fail:
1. "lcm of 12 and 18" → None FAIL (looks_mathematical: 'lcm' marker present, but _normalize leaves 'lcm of 12 and 18'; _parse_number_theory runs on 'clean' which is fine — but _extract_expression? No, number_theory returns directly. WHY None? 'of'→'*' replaced in _normalize? NO, 'of' only replaced in _extract_expression. hmm — maybe looks_mathematical marker 'lcm' lowercased match 'lcm' ✓ and digit+op regex also fine. Number theory: numbers=[12,18], has_lcm=marker('lcm') ✓ → returns. But result None! UNLESS solve path: clean = 'lcm of 12 and 18' then... wait my probe: 'lcm of 12 and 18' → None but 'ল.সা.গু 15 ও 20' works! Diff: BN markers match. EN: lowered contains 'lcm' ✓... Ah wait looks_mathematical markers tuple contains "lcm"? YES (line markers). But result None — must trace. NOTE earlier probe BEFORE my _parse_number_theory addition returned None for lcm too, but that used old code. The current run: lcm fail, গ.সা.গু pass. So for 'lcm of 12 and 18' _parse_number_theory should match. Trace again.
2. "gcd of 12 and 18" → None FAIL (same)
3. "10th term of AP starting 3 with difference 4" → None FAIL (no parser; not in engine — fine, concept answer from facts instead; adjust MATH_TESTS to test engine only where supported OR document as knowledge-based)
4. "5th term of GP starting 2 with ratio 3" → None FAIL (same)
5. "sin(30 degrees)" → None FAIL (need deg→rad: sin(30°) maybe works; test 'sin(pi/6)')
6. x^2-5x+6=0 → 'unsupported'?? quadratic should solve! 'got: unsupported' = expression fallback error. Actually answer='unsupported'?! That came from _numeric_result? No — that's _evaluate error path: answer "I could not safely solve..." hmm printed 'unsupported' from exact field. Quadratic parser returned None (maybe "solve " prefix not stripped). Check.
NOTE: MATH_TESTS have no 'answer' key (dict lacks it) — my probe used .get('answer') default '' so PASS printed incorrectly for several (e.g. '45' showed PASS). Check actual test dict keys: inspect MATH_TESTS[0] keys.
7. "৩০০ এর ১৫%" → unsupported FAIL (normalize: ৩০০→300 via _BN_DIGITS ✓, '১৫%→15% ✓, but ' এর ' remains; _extract_expression keeps? '300 এর 15/100' — chars filtered: ' এর ' non-ascii removed in _extract regex [^0-9a-zA-Z...] → '300 15/100' → no operator between → invalid AST → error → unsupported. Accept or fix: treat 'এর' as '*'.
Plan: (a) trace lcm en; (b) quadratic 'solve' prefix; (c) BN percentage via 'এর'→'*'; (d) AP/GP & trig degrees: add trig parse for 'sin(N degrees)' with deg-to-rad for N in 0-360 with known exact values (30→0.5, 45→0.707..., 90→1); AP/GP: add _parse_progression for '10th term of AP starting 3 with difference 4' / '5th term of GP starting 2 with ratio 3'; (e) verify exact test dict keys in training_mathematics.py.

## COMPLETION STATUS (current)
- All engine fixes DONE: solve prefix, trig degrees, AP/GP progression, BN এর→*, hypotenuse, markers.
- tests/test_phase29_mathematics.py: 63 passed (package validation, MATH_TESTS all 15, phase29 features, brain concept questions).
- Full regression: 654 passed, 3 warnings.
- Benchmark: 57/57 = 100% PASS.
- TODO: ruff check, smoke_production.py, commit + push main, then Phase 30 (physics training expansion).
- Engine facts: quadratic → "x = 2, x = 3"; circle r=5 → "A=πr²=78.53981634, circumference = 31.41592654"; tan(45°) → "tan(45°) = 1"; hypotenuse 5,12 → "c=√(a²+b²)=13".
- Test expectations use numeric tolerance matching (0.01) because engine formats with 10g.
