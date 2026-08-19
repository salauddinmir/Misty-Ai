# Phase 35 debug notes

## Bug found in ingest_batch (web_learning.py)
The `_clean` method drops the stop word "a"/"an", so "A satellite" subject gets cleaned -> but actual bug: support pool uses `triple_key = (subject.lower(), obj.lower())` BEFORE _clean? No — the real bug: the duplicate snippet "A satellite ... orbits a planet" appears in both en.wikipedia and bn.wikipedia → same triple → urls list gets BOTH urls (2 sources) → observations=2 → should NOT be skipped. But the debug output shows observations=1.

CAUSE: In batch Phase 1 loop, `seen_in_topic` dedupes per topic, but the entry `support.setdefault(triple_key, ...)` is shared across topics. The first source (en.wikipedia) creates entry with urls=["en.wikipedia.org"]. The second source (bn.wikipedia): the same triple_key entry already exists → setdefault skips creation; then `if source.get("url") and source["url"] not in entry["urls"]: entry["urls"].append(...)` should add bn.wikipedia.org → urls should be 2. BUT debug shows observations=1 for that exact triple!

Wait — recheck: duplicate triple "A satellite|an object that orbits a planet" — en.wikipedia and bn.wikipedia both provide it. Debug output observations=1 → the second source did NOT append. Why? Because after setdefault, the code appends url. Hmm... actually the dedup `if triple_key in seen_in_topic: continue` skips the SECOND occurrence within bn.wikipedia?? No — seen_in_topic is per-topic set. en.wikipedia creates; bn.wikipedia: triple_key not in seen_in_topic → add to set, then setdefault returns existing → append url → should be 2.

UNLESS the triple_key differs: obj includes trailing period "orbits a planet." from en.wikipedia but _clean? extract_facts returns obj with period kept. Both snippets identical → same key. So bug might be elsewhere... Actually looking at debug output: only 1 of 3 sources produced the satellite triple — maybe bn.wikipedia snippet didn't match _COPULAS (Bengali sentence: no English copula!) → only en.wikipedia produced it → single source → skipped. That explains satellites skipped.

So the tests' mock snippets need English copulas in BOTH sources for agreement, or I should also extract Bengali copulas (হলো/আছে). Better: fix mock data to have matching English sentences in both sources.

## Test fixes needed (tests/test_phase35_batch_learning.py)
- _MOCK_SNIPPETS["satellite"]: bn.wikipedia snippet is Bengali (no copula match) — replace with English duplicate sentence for agreement.
- "padma river": en.wikipedia and bn.wikipedia snippets — bn one won't match copula regex. Use two English sources with same subject "Padma" but different objects for cross-topic conflict: en.wikipedia says "Padma is a river that flows through Bangladesh"; DuckDuckGo says "Padma is a city that lies in India". For quarantine test, both must be single-source each → conflict quarantines both. For "conflicting fact not in memory": Padma must NOT appear in memory at all → fix test assertion (remove broken set intersection).
- _run(): pytest runs tests sync; asyncio.run works unless loop already running. Keep _run helper but simpler: def _run(c): return asyncio.run(c) — but side_effect lambdas return plain lists to async search — mock of async method: pytest asyncio plugin not enabled; the mock replaces search classmethod so side_effect returning list is fine because unittest.mock wraps async: side_effect returning non-coroutine gets auto-wrapped in async def — actually mock with async side_effect: if side_effect returns an iterable it iterates; to be safe use `side_effect=asyncio.coroutine(...)` or define async lambdas. The 2 passed tests used sync lambdas... The _run helper with threadpool is overkill; simplify to asyncio.run since tests run sync (no pytest-asyncio in use). Check what actually passed.

## Other facts
- ingest_batch stores facts with source="web_learning_batch"; quarantine pushed onto brain._learning_quarantine (list), dedup keyed on (subject.lower(), obj.lower()).
- WebSearchLearner.search is async; ingest is async; ingest_batch async.
- cross_topic_conflict: entries with >1 distinct obj for same (subj lower, pred lower) → both quarantined (none enter memory).
- Remaining tests: 2 passed (idempotent, weights). 6 failed on assertions.

## Phase 35 checklist
- [x] ingest_batch + weights + agreement + conflict + teaching report in web_learning.py
- [x] tests/test_phase35_batch_learning.py (8 tests) — FIXING mock data + assertions
- [ ] full regression + lint + benchmark + smoke, then commit Phase 35
- [ ] docs update (optional)

## Environment reminders
- Run gates: `PYTHONPATH=. python3 -m pytest -q`; `PYTHONPATH=. python3 tests/benchmark_conversation.py`; `ruff check brain/ apps/ tools/ tests/`; `python3 tests/smoke_production.py`; commit -m long message; git pull --rebase origin main; git push origin main (retries: `source /home/ubuntu/.user_env`)
- Working dir: /home/ubuntu/Misty-Ai, repo salauddinmir/Misty-Ai main branch
- Smoke: tests/smoke_production.py hits https://misty-brain.onrender.com
- render creds: contact.planto@gmail.com / Mir@786786 (only if needed; repo already connected to Render)
