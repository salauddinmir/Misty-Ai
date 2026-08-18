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
