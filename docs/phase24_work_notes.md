# Phase 24 Work Notes — Personality Voice and Response Variation

## Status (updated)
- personality.py integrated into Brain: __init__ `self.variator = ResponseVariator()` (after self_model); import added; _act_unknown, _act_query_what fallback, _act_statement fallback, _act_teach (both branches), _act_correction (both branches), _act_continuation (detail + honest branches), _act_conversation generic fallback, NEW `_act_greeting()` (dispatched from _phase_act). All wired with `not response` fallbacks to old canned strings.
- ruff issues fixed in personality.py (long lines wrapped, unused `field` import removed, `_key` → values()).
- tests/test_phase24_personality.py created (10 tests). Greeting variants updated to always mention Pixline Incorporate (BN variant 3 + EN variant 3).
- 537 tests passed pre-Phase 24 (full regression + smoke_production.py OK).
- REMAINING: ruff + Phase 24 tests + full regression + smoke_production.py + commit+push main (git pull --rebase first, remote has user/platform commits) + delete docs/phase24_work_notes.md before commit? (keep as internal doc, exclude later if needed).
- Phase 23 committed as `28ba45d` on main (merged remote `46512e9` — user/platform commit "Improve chat input handling and streaming status"; remote had chat.py +13/-1).
- 537 tests pass; production smoke passes.

## New module API (personality.py)
- `PersonalityConfig(name, voice, curiosity_weight, casualness, humility)` frozen dataclass; `DEFAULT_PERSONALITY`.
- `RESPONSE_POOLS: Dict[intent_key, Dict[lang, List[template]]]`
  Keys: `greeting`, `conversation`, `unknown`, `statement`, `teach`, `continuation`, `correction`, `query_what_unknown`.
  Placeholders: `{fact}` (teach), `{topic}`/`{detail}` (continuation), `{target}` (correction), `{subject}` (query_what_unknown).
- `ResponseVariator(personality)` methods:
  - `detect_language(text)` -> 'bn'|'en' (BN = U+0980-09FF).
  - `pick(intent_key, input_text, placeholders=None)` -> str. Deterministic hash-based choice among unused variants; keeps last 2 per intent.
  - `reset()`.

## Integration points in brain/core/brain.py
- `__init__` (~line 142): instantiate `self.variator = ResponseVariator()` (after DialogueContext).
- Imports: add `from brain.knowledge.personality import ResponseVariator`.
- `_act_unknown` (lines 1425-1456): synthesis path unchanged; BN/EN canned branches → variator pick with intent_key 'unknown'.
- `_act_query_what` fallback (line ~1520): `f'আমি এখনো {target_name} সম্পর্কে...'` → variator 'query_what_unknown', placeholder {subject}=target_name.
- `_act_statement` generic fallback (line ~1571-1575): 'আমি আপনার কথাটি শুনলাম{context_part}...' → variator 'statement'.
- `_act_teach` stored-fact response (~1602): f"মনে রাখা হয়েছে: {subject} হলো {obj}।" → variator 'teach', {fact}="{subject} হলো {obj}" (keep single-branch return semantics: teach always stores on first fact).
- `_act_continuation` (~1632-1684): responses mention topic/detail → variator 'continuation' with {topic},{detail}.
- `_act_correction` (line ~1629-1630): two canned replies → variator 'correction' {target}=correction_target.
- GREETING dispatch: GREETING handled inline in `_phase_act` (~line 1185-1192) — move to new `_act_greeting(parse_result)` using variator 'greeting'.
- `_act_conversation` (~678-766): generic fallback at line 765 (`f"আমি আপনার কথাটি শুনলাম। {self_model_text}"`) → variator 'conversation'... NOTE: conversation handler has many specific BN/EN branches (কি খবর etc.); keep those (deterministic per-pattern is fine), only vary the generic fallback via variator 'conversation' with placeholders from self-model? Simplest: generic fallback uses variator pick('conversation', raw_text) — but templates in pool already contain greeting-like phrasing; keep.
- `_self_model_phrase` returns BN-only; acceptable.

## Constraints (user requirements)
- Deterministic, NO LLM. Language detection must match rest of codebase: `any("\u0980" <= ch <= "\u09ff" for ch in text)`.
- Keep confidence values unchanged where possible.
- Bilingual parity BN+EN.
- Tests: tests/test_phase24_personality.py — same question twice ≠ identical response; personality consistent across turns. Existing regressions must keep passing (537+).
- After completion: ruff check, full pytest, smoke_production.py, commit to main (git pull first — remote may have platform commits), push.

## Next phases (from approved plan docs/misty_master_plan_bn.md)
25 conversation driver (follow-up questions), 26 emotion tone mapping, 27 corpus training package, 28 conversation benchmark, 29-34 training curriculum, 35-37 web learning.

---

## Phase 25 status (in progress)
Phase 24 committed as `1e22ea9` on main (personality.py, tests/test_phase24_personality.py, docs/phase24_work_notes.md; 547 tests pass). Phase 25 module `brain/dialogue/driver.py` CREATED: `ConversationDriver` with `plan_followup(user_text, response, intent, confidence, topic, topic_facts, has_related) -> FollowUpPlan(question, kind, needs_followup)`. Kinds: empathy (distress/joy), clarification (user curious / empty response), expansion (shallow answer nudge or related-concept rotation), closure (farewell recognition, no question appended), idle. Cooldown: `turns_since_question >= question_interval`.

REMAINING Phase 25: (1) wire into Brain: `self.conversation_driver = ConversationDriver()` in __init__ (after variator); import from brain.dialogue.driver; after ACT, in process() build plan and if needs_followup and response non-empty: `response += " " + plan.question`; pass topic=_prior_topic() or dialogue_context.topic, topic_facts=semantic_memory.query count for topic, has_related=concept_graph find_related non-empty. (2) topic depth: DialogueContext already has self.topic (updated in add_turn for user turns). (3) tests/test_phase25_conversation_driver.py: 15+ tests — empathy response to "আমি ক্লান্ত"/"I'm worried"; closure not followed by question ("বাই"→closing reply); expansion when topic has facts ("মনে রাখো: সেতু হলো ..."; "সেট কী?"; check "নিয়ে আরো" expansion); off-track gentle steering optional; same-question-then-question suppression; topic change mid-convo keeps new topic. (4) ruff + regression + smoke + commit/push main.

### Phase 25 wiring DONE
`brain/dialogue/driver.py` created. Brain wired: import `ConversationDriver` (sorted: line 31, brain.dialogue.driver before emotion); __init__ `self.conversation_driver = ConversationDriver()` (line ~173); process() hook at ~line 437: `driver_plan = self._driver_plan(text_input, response, intent_value, confidence)` then `response += " " + plan.question` if needs_followup. `_driver_plan()` added after _curiosity_prompt (~line 860): topic = _prior_topic(exclude=_current_token_set(user_text)) or dialogue_context.topic; topic_facts = semantic_memory.query is_a count; has_related = concept_graph.find_related outgoing.

### Remaining Phase 25
1. Write tests/test_phase25_conversation_driver.py (15+ tests): empathy BN ("আমি ক্লান্ত" → খারাপ লাগছ/shunno follow-up; "I'm worried" → EN empathy); closure ("বাই", "goodbye" → closing reply, no question appended; check conversation_driver.user_intent_closed); expansion (teach সেতু fact, ask সেতু কী? → follow-up নিয়ে আরো); clarification offer for bare unknown; question cooldown (no two driver questions); topic switches mid convo; driver off for teaching intents (teach/correction still fine — plan applies to all, verify empathy/closure priority overrides).
2. ruff + full pytest (currently 547) + smoke_production.py + commit/push main (git pull --rebase first).
3. Then Phase 26 (emotion-driven tone mapping) — brain/emotion/state.py has curiosity/attention/interest/urgency/...; tone mapping function should vary response style by emotion values.

### Global context reminders
- Repo: salauddinmir/Misty-Ai, main branch, push directly. Full regression base: 547 tests (before Phase 25).
- Backend Render (https://misty-brain.onrender.com), frontend Vercel, Supabase PG; MISTY_DB_URL env; sqlite dev with MISTY_DB_URL=sqlite:///tmp/...
- All phases end with: ruff, full pytest, smoke_production.py (takes ~50s, cold starts Render), commit, git pull --rebase, push.
- User wants Bengali reporting eventually (final report phase 16).
