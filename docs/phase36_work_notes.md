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

## UPDATE: Phase 36 DONE & PUSHED (commit 1d9f53e, main)
Files: apps/api/routes/training.py, brain/core/brain.py (self.web_learner = WebSearchLearner(self)), apps/api/main.py (include_router(training_router)), tests/test_phase36_training_api.py (9 tests). 829 tests pass, benchmark 57/57, smoke PASS.

## Phase 37 design (final phase of plan, small scope)
Master plan Phase 37 (docs/misty_master_plan_bn.md line ~156): "শেখানোর-পর-স্ব-মূল্যায়ন চক্র" — after each batch ingestion, auto re-run relevant benchmark cases, report answer diffs, update topic-wise scorecard. Success criteria: benchmark score demonstrably increasing after learning.

### APIs available to build on
- `brain.learning.self_assessment.GapAssessor(brain)`:
  - `evaluate(cases: Sequence[Dict[str,str]], max_cases=100) -> GapReport` (GapReport: total(), score(), to_dict(), GapEntry to_dict)
  - `review_quarantine(quarantine)`, `release_candidate(brain, candidate)`, `history() -> List[GapReport]`, `last_report()`, `gap_dicts()`
- `brain.learning.training_scorecard.BenchmarkScorecard(brain, cases)`:
  - needs cases param; ScorecardResult.overall_score(), to_dict(); CategoryScore.pass_rate()
  - TrainingBatchVerifier.verify(brain) -> List[PackageVerification]
- `tests/benchmark_conversation.py`: CATEGORIES dict, CONVERSATION_BENCHMARK from brain.knowledge.corpus_conversation; run as CLI; case format {"input": "..." or turns "||", "expected": "..."}, category keys; grading by expected-substring in final response.
- `brain.web_learner.ingest_batch(topics, topic_weights=None)` returns {topics, learned, quarantined, skipped, cross_topic_conflicts}

### Phase 37 implementation plan
1. New module `brain/learning/post_learning_loop.py`:
   - `PostLearningAssessor(brain)` — hooks: `assess_after_learning(topics, report)` returns dict {assessed_cases, before/after scores per topic-related benchmark subset, improvement, assessment_time}
   - Use GapAssessor.evaluate() on a filtered subset of CONVERSATION_BENCHMARK cases whose keywords relate to topics (simple keyword mapping + category filter)
   - Scorecard update via BenchmarkScorecard if possible; store history list of AssessmentRun on the assessor
2. Hook into `WebSearchLearner.ingest_batch`: after return, call brain's post-learning assessor (add self to WebSearchLearner or pass brain) — append `post_learning_assessment` to returned report. Keep it optional/try-except so ingest never fails.
3. `tests/test_phase37_post_learning.py`: assess after mock ingestion; improvement detected when mock facts make a case pass; history accumulates; API route report includes assessment.
4. Gates: pytest, ruff, benchmark 57/57, smoke; commit+push; write docs/phase37_report_bn.md (Bengali summary of whole plan completion: phases 23-37 done, metrics table).

## Remaining (Phase 8)
Full final regression, CI lint (check .github/workflows/ci.yml lint job), production smoke, Bengali completion report, final push.

## UPDATE: Phase 37 implementation (in progress, state snapshot)

### Done
- `brain/learning/post_learning_loop.py` created: PostLearningAssessor (history, assess_after_learning(topics), assess_baseline(), last_run(), trend()), AssessmentRun (improved, diffs(), to_dict()), _CaseFilter, _CASE_CATEGORY map by case id prefix (categories: greeting/context/emotion/unknown/teach_followup/continuation/math_physics/english/humor/closure/correction/general). Selected cases get "category" key added. _collect_answers: brain.process returns dict with top-level 'response'.
- `brain/knowledge/web_learning.py`: ingest_batch end — after teaching_report assembly, `if getattr(self, "post_learning_assessor", None): teaching_report.update(assessor.assess_after_learning(topics))` with try/except.
- `brain/core/brain.py`: import PostLearningAssessor (line ~55), in init after self.web_learner: `self.post_learning_assessor = PostLearningAssessor(self)`.
- `tests/test_phase37_post_learning.py` created (TestApiRouteIncludesAssessment creates own client WITHOUT MISTY_TRAINING_API_KEY env — need to set env in client; note: TestClient with module-level import of training router uses env set in setUp).
- API route /api/training/web_learn report will auto-include post_learning_assessment via hook (no route change needed).

### TODO next
1. Run tests/test_phase37_post_learning.py — verify all pass (check env key in TestApiRoute test).
2. Full gates: pytest -q, ruff, benchmark 57/57, smoke.
3. Commit+push Phase 37: "Phase 37: post-learning self-assessment loop..."
4. Write docs/phase37_report_bn.md — Bengali summary of phases 23-37 completion (use git log for metrics: tests 829+, benchmark 57/57, CI lint).
5. Phase 8: final gates + CI check (github workflow ci.yml lint), production smoke, final push.

### Key facts
- benchmark CLI: PYTHONPATH=. python3 tests/benchmark_conversation.py → 57/57
- regression: PYTHONPATH=. python3 -m pytest -q
- smoke: python3 tests/smoke_production.py
- Phase 36 done: commit 1d9f53e pushed; Phase 32: 431212a
- Render: https://misty-brain.onrender.com; Vercel: misty-ai-web.vercel.app

## Phase 37 near-complete state (save before compaction)

DONE and passing: brain/learning/post_learning_loop.py (PostLearningAssessor, AssessmentRun, _CaseFilter, _CASE_CATEGORY by case id prefix; score/total are PROPERTIES of GapReport), web_learning.py ingest_batch hook (sets post_learning_assessment=None on exception), brain.py wires self.post_learning_assessor = PostLearningAssessor(self) after web_learner. Tests: 11 pass in isolation.

REMAINING BUG: tests/test_phase37_post_learning.py::TestApiRouteIncludesAssessment::test_web_learn_report_includes_assessment fails in full suite (401) because training.py reads _TRAINING_KEY = os.getenv(...) AT IMPORT TIME and test_unset_key_refuses_everything (phase36) pops the env + reloaded module's key ends up None for my test's router too.

FIX PLAN (chosen): In TestApiRouteIncludesAssessment, use importlib.reload approach: set env + reload training module, mount reloaded router, clear _rate_windows. Or simpler: set env BEFORE training module import — but module already imported by other tests. So: in setUp: os.environ["MISTY_TRAINING_API_KEY"]="misty-secret-key-37"; module = importlib.reload(training_module); app include module.router; patcher for search; TestClient. Restore env after tearDown (reload again with original key).

Full gates so far: pytest 839 passed -1 (this test); benchmark 57/57 PASS; ruff all green; smoke timed out once (Render cold start) — retry later.

After fix: full pytest, ruff, benchmark, smoke (retry), then commit push Phase 37: message "Phase 37: post-learning self-assessment loop — automatic benchmark re-run after every batch ingestion, before/after answer diffs, topic scorecard history, ingest_batch + /api/training/web_learn hook". Then write docs/phase37_report_bn.md (Bengali completion report phases 23-37) and final CI check.

CI lint was failing on main historically (parser.py E501 etc) — my earlier commits fixed those so CI should now be green (commit 431212a fixed 5 parser E501 + test_phase18 F401; verify run # for Phase 37).
