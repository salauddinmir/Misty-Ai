# Phase 36 work notes (state before compaction)

## Done
- `apps/api/routes/training.py` created:
  - POST /api/training/web_learn (router prefix="/api/training")
  - MISTY_TRAINING_API_KEY env gate via X-Misty-Training-Key header; 401 when unset/wrong/missing; warning printed at import when unset
  - In-memory sliding-window rate limiter keyed by X-Forwarded-For else client.host; env MISTY_TRAINING_RATE_LIMIT=10, MISTY_TRAINING_RATE_WINDOW=60
  - _get_brain: request.app.state.brain (fallback request.brain attr)
  - validation: topics non-empty list of strings; topic_weights dict; JSON parse errors -> 400
- `brain/core/brain.py`: wired `self.web_learner = WebSearchLearner(self)` after GapAssessor (line ~154); import WebSearchLearner from brain.knowledge.web_learning (line 49, alphabetical)
- `apps/api/main.py`: `app.include_router(training_router, prefix="")` added after brain_router; import added
- `tests/test_phase36_training_api.py` created: 3 test classes (key gate, rate limit, validation). NOTE: test file has a messy duplication at bottom (class alias hack using __dict__) — LIKELY BROKEN, needs cleanup before running.

## TODO
1. Clean up test_phase36_training_api.py bottom duplication — classes must properly inherit unittest.TestCase. Then run:
   `cd /home/ubuntu/Misty-Ai && PYTHONPATH=. python3 -m pytest tests/test_phase36_training_api.py -q`
   (fastapi testclient needs: `sudo pip3 install httpx`? testclient uses httpx — check if installed)
2. ruff check apps/api/routes/training.py tests/test_phase36_training_api.py
3. Full gates: pytest -q (expect 790+), benchmark 57/57, smoke production
4. Commit + push Phase 36 to main, message like "Phase 36: authorized web-learning API route..."
5. Phase 37: post-learning self-assessment loop — auto re-run benchmark after batch ingestion, topic-wise scorecard update. Design notes in docs/phase33_work_notes.md (top-level TODO list for 33-37) and docs/misty_master_plan_bn.md Phase 37 section.
   - Phase 37 essentials: in web_learning.py ingest_batch or new hook, after learning -> self.gap_assessor.run (or benchmark) -> update scorecard; expose in report as "post_learning_assessment" dict {benchmark_score, gap_count, ...}. tests/test_phase37_self_loop.py expected by plan.
6. After Phase 37: full regression, CI lint, production smoke, Bengali completion report (docs/phase37_report_bn.md?), final push.

## Key env/commands
- pytest: PYTHONPATH=. python3 -m pytest -q
- benchmark: PYTHONPATH=. python3 tests/benchmark_conversation.py (57/57)
- smoke: python3 tests/smoke_production.py (Render https://misty-brain.onrender.com)
- lint: ruff check <files>
- CI files: .github/workflows/ci.yml — lint job scans brain/ apps/ tools/ tests/
- Git: repo /home/ubuntu/Misty-Ai, main branch, direct push works
- Phase 33 module: brain/learning/self_assessment.py (GapAssessor), brain.knowledge_gaps state key
- Phase 34 module: brain/learning/training_scorecard.py (TrainingVerifier + BenchmarkScorecard)
- Phase 35 module: brain/knowledge/web_learning.py (ingest_batch added)
