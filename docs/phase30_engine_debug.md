# Phase 30 physics engine — state notes (post fixes)

## Engine changes made (uncommitted, all applied to brain/physics_engine.py)
1. _BN_DIGITS Bengali digit translation at start of solve().
2. New token markers added: ohm, ওহম, resistance, রোধ, series, সমবায, parallel,
   সমান্তরাল, wave, তরঙগ, frequency, কম্পাঙক, circuit, বর্তনী, fall, পতন, voltage, current.
   (Note: terminal renders সমবায/তরঙগ/কম্পাঙক ambiguously; file verified correct
   via codepoint checks — marker list is fine.)
3. New branches added AFTER potential-energy branch: free fall (s=1/2gt²),
   series R (before ohm), parallel R (before ohm), ohm I=V/R (stricter trigger:
   ohm/ওহম/voltage/"v "/ভোল্ট), power (P=V*I if volt present else P=W/t),
   wave speed v=fλ (before velocity gate in intent).
4. Velocity branch now skips when wave/frequency/তরঙগ/কম্পাঙক in text.
5. Work branch moved BEFORE force branch ("work done by force..." → work).
6. MISTY capability fact + PhysicsEngine "solves" fact added to PHYSICS_FACTS.

## Branch order in solve():
velocity → force → kinetic → momentum → potential → free-fall → series →
parallel → ohm → power → wave → fallback.

## Verified passing engine cases (PYTHONPATH=. python3 /tmp/probe_phys.py):
- velocity 200m/10s = 20 ✓; BN ২০০মি/১০সে ✓
- force 5kg×2 = 10 N ✓; kinetic ½×2×9 = 9 J ✓; momentum 6 ✓
- work 10×4 = 40 J ✓; potential 2×9.8×10 = 196 J ✓
- free fall 5s = 122.5 m ✓ (after \bfreely? fix)
- ohm 12V/4ohm = 3 A ✓; series 6+3 = 9 ✓; parallel 6∥3 = 2 ✓
- power 12V×5A = 60 W ✓; wave 50Hz×4m = 200 m/s ✓ (after ordering fix)

## REMAINING PHASE 30 WORK
1. brain/knowledge/training_physics.py — COMPLETE package file written
   (concepts, synonyms, relations, facts, formulas, rules, examples, tests,
   hash, physics_curriculum_package(), register_physics_curriculum). Need to
   verify PHYSICS_TESTS entries match actual engine outputs, then:
2. Wire into brain/core/brain.py: import register_physics_curriculum, call at
   Brain init after register_mathematics_curriculum (check physics routing in
   brain.process already exists — physics_engine gating in brain.py likely
   already calls PHYSICS_ENGINE).
3. tests/test_phase30_physics.py (mirror test_phase29_mathematics.py):
   package validation, registry, engine solves all PHYSICS_TESTS, brain concept
   questions (BN+EN), register idempotency.
4. pytest regression (baseline 654 passed), ruff, benchmark 57/57, smoke,
   then commit+push to main with meaningful message.
5. Phases 31 (Bengali literature), 32 (social-cultural), 33 (self-assessment),
   34 (training batch + scorecard), 35-37 (web learning) follow.

## Key lessons from Phase 29 (for 30 tests)
- Brain concept-question tests must tolerate variator template variants; safest
  assertion: lowered answer not containing "not learned"/"শিখিনি" AND containing
  a keyword from the curriculum fact.
- Brain stores math facts via curriculum at init; definition-fact lookups for
  "what is X?" use the alias expansion in _act_query_what (subject alias tokens).
  For physics, MATH_SYNONYMS-style PHYSICS_SYNONYMS was added to the physics
  package (verify present).
- ruff: RUF001 false positives on Bengali words → use noqa: RUF001 on those
  lines; line-length 120.
- Benchmark: PYTHONPATH=. python3 tests/benchmark_conversation.py (57 cases).
- Regression: python3 -m pytest -q. Smoke: python3 tests/smoke_production.py.

## Current state (latest)
Engine tests passing 15/16 except BN "১২ ভোল্ট ও ৪ ওহমে তডিৎ প্রবাহ" → None.
Root cause identified:
- "ওহম" substring IS in "ওহমে" (inflected), but _has_marker token regex
  negative lookahead (?![\w\u0980-\u09FF]) rejects because following char "ে"
  (U+09c7) is Bengali. "ভোল্ট" matches fine (followed by space).
- Gate in solve(): attempted a broken generator expression:
  `any(self._has_marker(...) for marker in self._markers
       if all("\u0980" <= c <= "\u09FF" for c in marker)
       or self._has_marker(lowered, marker) for marker in self._markers)`
  — syntax parses but semantics wrong (nested loop, first 'if' is filter).
- Correct fix: add _BN_TOKEN flag or simpler: new helper
  _marker_present(lowered, marker): use substring `in` for BN-only markers,
  token regex for ASCII markers. Replace the any(...) gate.

## Test command
PYTHONPATH=. python3 /tmp/probe_phys2.py  (16 cases, expects 16/16)
PYTHONPATH=. python3 /tmp/probe_bn.py      (BN ohm single case)

## After engine 16/16: write tests/test_phase30_physics.py, wire brain.py
(register_physics_curriculum after mathematics one), run pytest/ruff/benchmark/
smoke, commit+push main. training_physics.py already written (verify exists).

## State update (test file written)
- Engine 16/16 PASS (/tmp/probe_phys2.py covers the case set).
- brain/core/brain.py wired: import register_physics_curriculum + call at init after mathematics (lines ~45-46, ~272-274).
- physics_curriculum_package() validates OK (misty-physics-phase30).
- tests/test_phase30_physics.py WRITTEN (mirrors test_phase29).

### KNOWN BUGS in test file to fix before running:
1. test_register_into_brain: `brain.concept_graph.get_concept_by_name("ওহমের সূতr")` — typo, correct: "ওহমের সূত্র" check actual fact: PHYSICS_CONCEPTS has "ওহমের সূতr"? File shows: {"name": "ওহমের সূত্র", "type": "পদার্থবিজ্ঞান সূত্র", "lang": "bn"} — the terminal renders 'র' oddly; verify file bytes before removing. Safer: use "Newton's Second Law" (already there) and "ওহমের সূত্র" with exact codepoints from file via script.
2. test_free_fall_bengali: "অতিক্রন্ত" typo → "অতিক্রন্ত"? Correct: "মুক্তপতনে ৩ সেকেন্ডে অতিডিগ্রম্য হয়া দূরত্ব"? Use simpler: "৩ সেকেন্ডে মুক্তপতনে পড়া দূরত্ব".
3. test_wave_bengali: "৫০ হার্জ কম্পাঙক ও ৪ মি তরঙগের বেগ" — hasura-less typo (ঙ). Correct: "৫০ হার্জ কম্পাঙক"? — verify bytes vs PHYSICS_FACTS/CONCEPTS. Use simple: "তরঙগ"→"তরঙগ"? File fact subject "তরঙগ"? CONCEPTS has "তরঙগ"? (line 89 shows তরঙগ = 0x9a4 0x9b0 0x999 0x9cd 0x997 = তরঙগ with ঙ্গ? actually 0x999=ঙ. File uses তরঙগ (ঙ without hasura!). Engine marker "তরঙগ" uses codepoints [9a4 9b0 999 9cd 997] = same! OK. Frequency marker কম্পাঙক? File: [995 9ae 9cd 9aa 9be 999 9cd 995] = কম্পাঙক — ঙ্গ again without second ব. So in test use EXACT strings copied from file (or just use English). Simplest: use English for wave BN test OR copy exact strings via python script reading PHYSICS_CONCEPTS.

### Run sequence after fixes:
python3 -m pytest tests/test_phase30_physics.py -q (fix until green; run 5x for stability)
then full: python3 -m pytest -q (expect 654+), ruff check tests/test_phase30_physics.py brain/physics_engine.py brain/core/brain.py brain/knowledge/training_physics.py (fix), PYTHONPATH=. python3 tests/benchmark_conversation.py (57/57), python3 tests/smoke_production.py
Commit message: "Phase 30: full bilingual physics curriculum — mechanics/kinematics, energy, gravitation, electricity, waves, optics; PhysicsEngine free-fall/series-parallel/Ohm/power/wave solvers, BN digit support, TrainingPackageV2 registry with provenance; regression green"
Then Phases 31-37.

### Phase 31-37 (from master plan docs/misty_master_plan_bn.md):
31 Bengali literature (Tagore/Nazrul/Jibanananda knowledge package), 32 social-cultural (Bangladesh/India), 33 self-assessment (gap detection), 34 full training batch + scorecard report, 35 batch web-learning, 36 authorized web-learning API route, 37 post-learning self-assessment loop.

## Phase 30 state (updated)
- tests/test_phase30_physics.py: 59 pass, 7 fail.
- Remaining failures:
  1. test_topics_covered: facts topics are {electricity, optics, forces, kinematics, waves_sound, energy} — fix assertion to expect "forces" and "waves_sound" instead of "mechanics"/"gravitation".
  2. test_register_into_brain: concept "ওহমের সূতr" exact bytes = U+0993 U+09b9 U+09ae U+09c7 U+09b0 U+0020 U+09b8 U+09c2 U+09a4 U+09cd U+09b0 — verify fix applied (escape version used).
  3. test_free_fall_bengali: "৩ সেকেন্ডে মুক্তপতনে পড়া দূরত্ত্ব" → unsupported. Note: phrase had typotized "পড়া দূরত্ত্ব" (ড় = correct, ত্ত্ব? "দূরত্ব" uses U+09a4+U+09cd+U+09b0+U+09cd+U+09ac; file uses "দূরত্ত্ব" with ত্ত্ব?). Engine free-fall regex \b(free|fall|falling|পতন) — "মুক্তপতনে" contains পতন as substring — check: U+09aa U+09a4 U+09a8 — but "মুক্তপতনে" file word? My test string: \u09ae\u09c1\u0995\u09cd\u09a4\u09aa\u09a4\u09a8\u09c7 = ম+ু+ক্+ত+প+ত+ন+ে = মুক্তপতনে (missing র?) — CORRECT word is মুক্তপতনে: ম(9ae)ু(9c1)? no — correct: ম+ু+ক+্+ত+প+ত+ন+ে + র? মুক্তপতনে letters: মু(ম+ু) ক্ত(ক+্+ত) প(প) ত(ত) ন(ন) ে(ে) — "মুক্তপতনে" = ম U+09ae, ু U+09c1, ক্ U+0995+U+09cd, ত U+09a4, প U+09aa, ত U+09a4, ন U+09a8, ে U+09c7. My escapes: 09ae(m) 09c1(u) 0995(k) 09cd 09a4(t) 09aa(p) 09a4(t) 09a8(n) 09c7(e) — CORRECT = "মুক্তপতনে". But engine regex \b(free|fall|falling|পতন) — "পতন" in "মুক্তপতনে" substring TRUE. So why unsupported? Because numbers regex: "৩"→3, "সেকেন্ডে" no num, "মুক্তপতনে" no num, "পড়া দূরত্ত্ব" no num → numbers=[3.0] len>=1 TRUE. Wave branch: ("wave" in lowered or "frequency" in lowered or তরঙগ in lowered or কম্পাঙক in lowered) and len>=2 → FALSE (len=1). Velocity branch: markers velocity/বেগ/speed/দ্রুতি — none TRUE. Next branches... free fall check \b(free|fall|falling|পতন) TRUE → should return s=44.1! But result unsupported — meaning a PREVIOUS branch caught it: the missing_values check? numbers=[3.0] not empty. Hmm— "unsupported" returned only from final fallback or physics_help. Let me check branch order: velocity, force, work, ke, pe... "work" branch condition? My phrase contains "কাজ"? no. But "পড়া" contains? no. Actually maybe the "power" branch: "work in 5 s" style requires "work" word. Hmm. Debug: run probe with print of each branch condition.
  4. test_wave_bengali + test_wave_not_velocity: engine returned v=12.5 (velocity branch: "বেগ" marker at end!). Wave branch condition FALSE because my BN phrase uses "তরঙগের" — check escapes: 09a4 09b0 0999 09cd 0997 09c7 = তরঙগ+ে ✓ contains "তরঙগ"... BUT also "কম্পাঙক" — my phrase কম্পাঙক = 0995 09ae 09cd 09aa 09be 0999 09cd 0995 ✓. Both present → wave branch SHOULD fire. It didn't → wave branch condition is FALSE → one of the literals in the file's condition must NOT be "তরঙগ"/"কম্পাঙক" as I think! File line 109 uses তরঙগ = 9a4 9b0 999 9cd 997 (verified match with 'তরঙ' regex) — that IS correct তরঙগ. And my phrase: 09a4 09b0 0999 09cd 0997 — same. Wait! My phrase has তরঙগে(র): ...997 then 9c7 (ে). "তরঙগ" (9a4 9b0 999 9cd 997) in phrase TRUE. কম্পাঙক: 995 9ae 9cd 9aa 9be 999 9cd 995 in phrase TRUE. So condition ("wave" in lowered or "frequency" in lowered or X in lowered or Y in lowered) should be TRUE! But engine returned velocity! UNLESS "wave" branch condition is actually different — earlier grep showed "তরঙগ" in line 109 with bytes 9a4 9b0 999 9cd 997 — verified same. Wait — maybe my test phrase actually reached the velocity branch FIRST because velocity branch came BEFORE wave branch in solve()? grep said wave at line 107-115, velocity at 117+. Wave first! So if wave condition TRUE it would return 200. Result is 12.5 → condition FALSE → "wave"/"frequency"/X/Y all FALSE. X="তরঙগ" FALSE? But X bytes = same. ODD. UNLESS the grep-found তরঙগ at line 109 is different from marker tuple তরঙগ (line 65)... both verified same bytes. Maybe my test phrase's তরঙগ differs from my assumption — re-verify test file line 225 bytes।
  5. test_newton_second_law + test_ohms_law_definition: brain answers "not learned" fallback — the brain question resolution doesn't reach definition facts for these subjects. Either the synonym mapping isn't applied in _act_query_what (brain uses synonyms only from math package?) or the alias expansion needs PHYSICS_SYNONYMS support. Check brain.py alias expansion — it may only scan predicate 'definition'/'সংজ্ঞা'/'সূতr'/'formula' on query(subject=word) — synonyms like "ohm's law" would need the word token "law"? Subject "Ohm's Law": word "law" no facts, then alias expansion scans words of target "newton's second law"? -> words {"newton", "second", "law"} — query(subject="second") etc none. Add physics package synonyms support to alias expansion, OR simpler: add synonyms as a registry lookup in _act_query_what (import PHYSICS_SYNONYMS + MATH-like). Simplest: brain alias expansion: for each word in target, also try subjects containing word as substring.
- Physics package topics: electricity(14), optics(12), forces(12), kinematics(11), waves_sound(10), energy(8).
- Run sequence after fixes: pytest -q full (654+), ruff on changed files, benchmark 57/57, smoke, commit+push Phase 30.
