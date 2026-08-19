# Phase 33-37 Work Notes

## Current state (as of Phase 32 push, commit 431212a, main)
- Phases 23-32 COMPLETE and pushed. Regression 781 passed, benchmark 57/57=100%, lint green, production smoke green.
- Phase 32 added: brain/knowledge/training_culture.py (44 CULTURE_FACTS, ~50 CULTURE_CONCEPTS, 52 CULTURE_SYNONYMS, CULTURE_TESTS 25, register_culture_curriculum), tests/test_phase32_culture.py (18 tests).
- "রজধন" standardized spelling: 9b0 9be 99c 9a7 9a8 9c0 (NO া after ধ). test_phase18 and test_phase32 use this spelling.
- API endpoints verified in smoke: GET /api/brain/tick_metrics, chat BN/EN/stream, training_catalog.
- MISTY_DB_URL env; tests use temp SQLite via conftest.
- Render prod: https://misty-brain.onrender.com

## Master plan specs (docs/misty_master_plan_bn.md lines 118-162)

### Phase 33 — Autonomous Gap-Filling (self-assessment)
- Goal: Misty knows what it does NOT know.
- Work: Extend autonomous reflection tick — iterate benchmark cases, produce knowledge-gap list, re-check quarantine candidates, honestly say "I don't know" and ask to learn.
- Test: 8/10 benchmark cases correctly classified known-vs-unknown; gap list visible in tick metrics API.

### Phase 34 — Full training batch run + benchmark report
- Load all packages to production, full benchmark suite run, numeric progress report.
- Test: 550+ tests pass; prod smoke all pass; report published. (we have 781 passed already)

### Phase 35 — Batch Web Learning
- ingest_batch(topics, topic_weights); stricter multi-source agreement (2+ sources required); cross-topic conflict detection; teaching report (learned / quarantined / skipped).
- Test: 3-5 topic batch passes; conflicting-fact quarantine proven.

### Phase 36 — Web-learning API route
- POST /api/training/web_learn with API-key/token gate (no access from public chat — 403 proven); safety-gate before teaching; auto-recall refresh after; rate limit: fixed count per hour.

### Phase 37 — Post-learning self-assessment loop
- After each batch ingestion: auto re-run relevant benchmark cases; answer-diff report; topic-wise scorecard update; score must increase — proven report.

## Implementation design decisions (Phase 33)
- New file: brain/learning/self_assessment.py — GapAssessor class.
  - evaluate(brain, cases=None, max_cases=100): runs each benchmark case through brain.process; grades known/unknown/incorrect.
  - GapEntry: {topic, query, expected, actual, status: "known"|"unknown_honest"|"incorrect"|"missing"}
  - gap_report(): list of unresolved gaps; exposes via brain.state metrics + /api/brain/tick_metrics output key "knowledge_gaps".
  - Quarantine review: re-check brain.quarantine (if exists) candidates against current KB.
- Reflect on existing architecture: brain/core/brain.py Brain has state.tick_metrics; reflection engine exists? check brain/cognition/ and brain/learning/ for existing reflectors (ReflectionEngine?).
- Benchmark cases source: tests/benchmark_conversation.py BENCHMARK_CASES (importable).
- Gate: pytest new file tests/test_phase33_self_assessment.py — 10+ tests; tick metrics JSON contains "knowledge_gaps" key.

## Remaining phases after 33: 34 (scorecard report docs/), 35 (ingest_batch in web_learning.py), 36 (api route apps/api/training.py or similar + rate limiter), 37 (auto benchmark re-run hook).

## Repo facts
- GH repo: salauddinmir/Misty-Ai, push to main. Commit style: long descriptive message.
- CI: .github/workflows/ci.yml — ruff check brain/ apps/ tools/ tests/ + ruff format --check. Keep lint green!
- Smoke: tests/smoke_production.py against Render.
- Benchmark: PYTHONPATH=. python3 tests/benchmark_conversation.py (exit 0 if >=85%).
