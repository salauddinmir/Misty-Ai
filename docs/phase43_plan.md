# Phase 43 — Personal Recall Integration in Conversation Responses

Goal: make Misty's replies directly grounded in what she remembers about the
person she is talking to — the remembered facts + recent episodes that overlap
the current query become part of the RECALL evidence for that turn.

Design:
1. `brain/core/brain.py`:
   - `process(text_input, user_id=None)` passes user_id into `_run_cycle`.
   - `_run_cycle` stores `self.current_user_id` (default "anon") and passes it
     into `_phase_recall` via a new internal helper `_phase_personal_recall`.
   - `_phase_recall` (existing) keeps semantic/episode/graph logic intact; the
     personal context is added as `recalled["personal_context"]` with:
     - fact_matches: remembered self-claims overlapping query tokens
     - episode_matches: recent episodes whose text overlaps query tokens
     - preferred_language: bn | en | unknown
   - No response text is generated here — the existing answer composer already
     uses recall evidence; personal context joins the same workspace broadcast
     as personal evidence (kind: personal_fact / personal_episode) so the
     tone/dialogue layers can use it in later phases.
2. `apps/api/routes/chat.py`:
   - ChatResponse gets `personal_recall: dict | None = None`.
   - `_process_chat_turn` copies `recall_result.data.get("personal_context")`
     into the response.
3. `apps/api/routes/brain.py` state model: add `current_user_id` string field.
4. Tests: ~10 in tests/test_phase43_personal_recall.py (no user_id→anon,
   fact match in recall, episode match, language not required, broadcast
   evidence ids, chat response field, brain state field, non-interference).
Wiring rules honored:
- Every get_state field → BrainStateResponse model (user_id field)
- ruff format, CI lint, benchmark 57/57, smoke, push to main, report after.
