# Phase 37 discovery notes

CONVERSATION_BENCHMARK (brain/knowledge/corpus_conversation.py line 1048) has only 12 cases, NO "category" key (all None), keys: id, input, expected_output, source_ref. The CLI benchmark (tests/benchmark_conversation.py) defines CATEGORIES manually mapping id prefixes (conv_bn_greeting, conv_bn_empathy, conv_bn_angry_calm, conv_bn_unknown, conv_en_*...) to categories.

Decisions:
- In post_learning_loop.py: build a local _CASE_CATEGORY map from id prefix, mirroring benchmark_conversation.py's CATEGORIES. Remove the unused BENCHMARK_CATEGORIES import and the _TOPIC_CATEGORY_MAP (replaced by input-keyword filter only).
- GapAssessor.evaluate uses case.get("category", "unknown") -> entries.topic = case category (will be "unknown" unless I add category to selected cases!). Must attach category to each selected case before evaluate (add "category": _case_category(case) dict copy).
- brain.process returns dict with payload.response (from earlier traces) — keep that.
- WebSearchLearner has NO assessor attribute; attach post-learning hook: add `if getattr(self, "post_learning_assessor", None):` block at end of ingest_batch, merge assessment into teaching_report. Modify brain/knowledge/web_learning.py end of ingest_batch (before `return teaching_report`).
- brain/core/brain.py: wire PostLearningAssessor(self) as self.post_learning_assessor; call attach_to_learner(self.web_learner, self.post_learning_assessor) in init; also brain.gap_assessor already exists (Phase 33).
- Training route: web_learn response should include post_learning_assessment (already merged by ingest_batch hook — free).
- Tests: tests/test_phase37_post_learning.py — mock search; verify assessment in report, diffs, history, trend, baseline.
