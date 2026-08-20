# Phase 46 State Notes — Persistent Fact Storage (save/reload across restarts)

## Task
Phase 46: persist semantic facts (with timestamps from Phase 44) + aging/consolidation audit logs
to DB (Postgres Supabase prod / SQLite dev), and cold-start reload into Brain.semantic_memory
and FactAger/ConsolidationEngine decisions.

## Persistence layer facts (apps/api/database.py)
- Class `Database`, driver detection from MISTY_DB_URL env -> DRIVER "postgres" or "sqlite".
- `async def execute(sql, params)` — postgres uses `$n` placeholders, sqlite uses `?`.
  postgres: async with self._lock -> await self._connection.execute(sql, *params)
  sqlite: await self._connection.execute(sql, params)
- `async def fetchall(sql, params)` — postgres uses `self._connection.fetch()`.
- `UPSERT_SQLITE` constant exists for sqlite upsert pattern.
- save_user_memory(user_id, payload) pattern: json.dumps payload dict into memory_json,
  ON CONFLICT (postgres) / INSERT OR REPLACE (sqlite) + await self._connection.commit() on sqlite.
- load_user_memory: fetch + json.loads.
- Schema applied in initialize(): Postgres executes schema_postgres.sql (jsonb, double precision);
  SQLite executes schema.sql (executescript + commit).
- DB lives in apps/api/database.py; Brain persistence sink wired earlier via consolidation sink.

## Schema files
- database/schema.sql (~110 lines), database/schema_postgres.sql — tables: concepts, relations,
  episodes, brain_states, procedures, training_packages, misty_user_memory (user_id, memory_kind,
  memory_key, memory_json, updated_at; UNIQUE(user_id, memory_kind, memory_key)).
- New Phase 46: add `misty_facts` table (both schemas):
  fact_key TEXT PK, subject TEXT, predicate TEXT, obj TEXT, confidence DOUBLE PRECISION/REAL,
  source TEXT, created_at DOUBLE PRECISION/REAL, accessed_at DOUBLE PRECISION/REAL.
- Optional `misty_audit_log` table: audit_kind TEXT (aging|consolidation|verification|correction),
  fact_key TEXT, action TEXT, payload JSONB/text, created_at.

## Key module facts
- brain/memory/semantic.py: SemanticFact(subject,predicate,obj,confidence,source,created_at,accessed_at);
  store_fact returns key; has query(), remove_fact(key), concept_associations, size.
  now_ts() helper = time.time() (overridable for tests via monkeypatch of now_ts).
- brain/learning/fact_aging.py: FactAger(brain).age_facts(now=...) returns summary;
  summary() dict; _decisions list of AgingDecision; _record appends; log capped 100.
- brain/learning/consolidation_sweep.py: ConsolidationEngine(brain).consolidation_sweep();
  summary(); _decisions of SweepDecision.
- Brain: self.semantic_memory, self.fact_ager, self.consolidation_engine, self._learning_quarantine.
- DB persistence wired via lifespan in apps/api/app.py (app.state.database = Database(); await .initialize()).
- Chat/memory routes already save per-user memory via app.state.database.

## Plan steps
1. Add misty_facts (+optional misty_audit_log) to both schema files.
2. apps/api/database.py: save_facts(payload) / load_facts() using json blob keyed by fact_key (like user memory pattern, simplest and robust), OR per-column table; prefer full table with upsert.
3. Also save audit log rows bounded (keep last N per kind) -> misty_audit_log with bounded insert.
4. Brain persistence hook: save semantic facts in autonomous_reflection_tick or on a save method;
   and reload on Brain construction via database.load_facts() if present (pass database to Brain?
   Brain currently has no DB; chat.py gets app.state.database; Brain() created in brain.py route).
   Simplest robust approach: save from reflection tick via Brain.get_state path OR from
   autonomous_reflection_tick call save_facts. Reload at startup from route layer (chat/brain routes)
   passing db to brain via Brain.load_facts(db_rows) classmethod-like setter.
5. Update docs/schema files; write tests/test_phase46_persistence.py (~12):
   save/load roundtrip both drivers, timestamps preserved, reload into semantic memory,
   audit log rows persisted, bounded log insert, protected facts roundtrip.
6. Gates: ruff check brain/ apps/ tools/ tests/ + ruff format --check; pytest -q;
   benchmark PYTHONPATH=. python3 tests/benchmark_conversation.py (57/57).
7. Commit/push main; wait CI ~230s; verify with .scripts/check_ci_jobs.sh (already exists in repo).
8. Write docs/phase46_completion_report_bn.md, commit, push, deliver result message.

## Env / commands
- cd /home/ubuntu/Misty-Ai; shell session verify1.
- Benchmark exit 0 if >=85%. Regression baseline 979 passed (phases 44+45).
- gh repo salauddinmir/Misty-Ai, branch main.
- Docs already delivered: docs/phase39_41_*, docs/phase42_43_*, docs/phase44_45_completion_report_bn.md
- CRITICAL: new Brain.get_state() keys must also be in apps/api/routes/brain.py BrainStateResponse.

## Progress update (current state)
DONE so far:
1. misty_facts + misty_audit_log tables appended to database/schema.sql (REAL, INTEGER PK) and database/schema_postgres.sql (DOUBLE PRECISION, BIGSERIAL).
2. apps/api/database.py: added _AUDIT_MAX_ROWS=4000; Iterable in typing imports; new methods save_facts(), load_facts(limit), save_audit_rows(rows) (with bounded DELETE keeping last 4000), load_audit_rows(kind=None, limit). Postgres $n placeholders w/ *params in execute; sqlite ? w/ tuple params. UPSERT_SQLITE used for facts.
3. apps/api/main.py: _restore_persistent_knowledge now uses database.load_facts() (restored_facts counter, timestamps set on fact.created_at/accessed_at), legacy episode scan kept as fallback only when no persisted_facts; logger updated. Added Phase 46 block in lifespan: _persist_facts() (saves all semantic facts + drains new audit rows via _new_audit_rows watermarks saved_audit_ids), _append_audit_row() helper (replays persisted rows into ager/_record AgingDecision and engine SweepDecision), _persisting_tick wrapper around brain.autonomous_reflection_tick scheduled via _safe_schedule after each tick, cold-start replay of load_audit_rows(limit=100), finally-block restores original tick + final await _persist_facts(). Imports: from typing Any, Dict, List.
4. brain/learning/fact_aging.py: cold-start anchor fix — days_old anchor = fact.created_at if created_at>0 else now (restored facts with 0 timestamp never age instantly).
5. tests/test_phase46_persistence.py written (~11 tests): roundtrip, upsert, timestamps across restarts, limit, empty noop, cold-start into semantic memory + aging sees restored birth time, audit save/load, kind filter, bounding, empty.

REMAINING:
- ruff format on main.py/database.py + lint brain/apps/tools/tests; ruff format --check all.
- pytest -q full regression (expect 979+11=~990).
- benchmark: PYTHONPATH=. python3 tests/benchmark_conversation.py (57/57).
- Commit/push main; CI wait ~230s; check with bash .scripts/check_ci_jobs.sh (or gh run list --repo salauddinmir/Misty-Ai --limit 1 --json headSha,status,conclusion — jq '.[0] | ...' array form).
- Write docs/phase46_completion_report_bn.md (Bengali report), commit, push, deliver result message with attachment.
- Report style: follow docs/phase44_45_completion_report_bn.md format (header with pixline/salauddin mirror/netvai, tables, quality gates section, next steps section).
- Note: smoke_production.py against https://misty-brain.onrender.com passes normally; run if time.

## Progress 2026-08-20 (after Phase 46 & 47)
- Phase 46 pushed (b8f5f3b), CI green; report 82e8a74. Regression 989, benchmark 57/57.
- Phase 47 DONE: apps/web/components/brain-monitor/MemoryHealthPanel.tsx created; types/index.ts BrainState got optional fact_aging/consolidation; page.tsx renders panel between BrainMonitor and CognitiveTrace; tsc + next build pass; pushed f7b2b35; CI green.
- Next: deliver Bengali report (docs/phase47_completion_report_bn.md) — commit + push + result message.
- Then likely Phase 48 (ONA reasoning layer) or Phase 49 (autonomous learning scheduler) — ask user next time.
