# MISTY Phase 1 Architecture Audit

## বর্তমান architecture

MISTY একটি LLM-independent Python cognitive runtime। `Brain.process()` একটি ordered cognitive cycle চালায়: observe, interpret, recall, reason, plan, appraise, evaluate, act, learn, consolidate। GlobalWorkspace বর্তমানে bounded events/evidence/hypotheses/appraisals রাখে। SelfModel identity, capabilities, goals, beliefs এবং uncertainty snapshot দেয়। LanguageGrounder response-এর grounding metadata তৈরি করে। Knowledge graph, semantic/episodic/procedural/working memory, goal manager, planner, inference, curiosity, induction, reinforcement এবং reflection subsystem ইতিমধ্যে runtime-এ wired আছে।

## যা বাস্তবে সম্পন্ন

- Deterministic Bengali/English NLU, mathematics এবং introductory physics solver আছে।
- Structured Bengali Literature package knowledge graph ও semantic memory initialization-এ inject হয়।
- Cognitive workspace, evidence records, hypothesis records, appraisal events এবং safe thought trace summary আছে।
- Self-model uncertainty update এবং performance reflection আছে।
- AutonomousInnerLoop bounded cadence, max tick duration, cancellation এবং tick-error isolation সমর্থন করে।
- PostgreSQL driver (`asyncpg`) এবং SQLite local-development fallback একই database API-তে আছে; Supabase PgBouncer-এর জন্য `statement_cache_size=0` ব্যবহৃত হয়।
- Chat response persistence এখন background task-এ decoupled; JSON ও SSE routes আছে।
- Frontend-এ CognitiveTrace panel source code-এ যুক্ত এবং production Next build সফল।
- সর্বশেষ repository state main branch-এ pushed; latest commits include `8e03c94`, `87b9ccb`, `9ca6fa5`, `bfaa7c3`।

## প্রধান gap ও ঝুঁকি

1. `autonomous_reflection_tick()` এখন মূলত current goal/uncertainty review করে একটি generic self-review hypothesis তৈরি করে। এটি নতুন external/internal evidence সংগ্রহ করে না, hypothesis-এর predictions execute করে না এবং falsification/consolidation result persist করে না।
2. `HypothesisRecord`-এর confidence update deterministic হলেও evidence independence, source reliability calibration, duplicate evidence, time decay, contradiction identity এবং audit history নেই।
3. `GlobalWorkspace.reset_cycle()` প্রতিটি user cycle-এ evidence/hypothesis history পরিষ্কার করে; long-term cognitive trace আলাদা durable event log-এ না গেলে autonomous learning-এর ইতিহাস হারাতে পারে।
4. Brain response payload-এ `thought_trace`, `self_model`, `grounding` এবং `phase_timings_ms` তৈরি হলেও `apps/api/routes/chat.py`-এর `ChatResponse` model ও `_process_chat_turn()` বর্তমানে মূলত grounding ফেরত দেয়। ফলে frontend types/panel আছে, কিন্তু API থেকে rich metadata end-to-end পৌঁছানোর contract সম্পূর্ণ নয়। এটি Phase 5 implementation-এর প্রথম কাজ হওয়া উচিত।
5. `apps/api/main.py` এবং `apps/api/database.py`-এর docstrings-এ SQLite wording আছে। Local fallback বৈধ হলেও production startup-এ `MISTY_DB_URL` অনুপস্থিত হলে silently SQLite-এ নেমে যেতে পারে। Production-এ fail-fast/explicit driver health check দরকার।
6. Database schema-তে hypotheses, evidence, contradictions, autonomy ticks, provenance এবং memory promotion audit-এর dedicated tables নেই। Episodes-এ JSON payload হিসেবে সবকিছু ঢোকালে queryability ও integrity কমে যাবে।
7. Single asyncpg connection এবং global lock correctness দেয়, কিন্তু autonomous worker, consolidation sink, chat persistence এবং sensor ingestion একসাথে write করলে queue/backpressure/priority policy দরকার।
8. Current test suite 408 passing হলেও autonomous learning-এর end-to-end acceptance tests, PostgreSQL integration tests, API rich metadata contract tests, long-running resource tests এবং bilingual benchmark coverage সীমিত।
9. Current emotion/appraisal state computational affective variables; subjective feeling নয়। Product claims ও UI copy-তে এই distinction স্পষ্ট রাখা দরকার।
10. No commercial LLM dependency বজায় আছে; external web evidence gathering ভবিষ্যতে যোগ করলে source allowlist, timeout, robots/terms compliance, provenance এবং untrusted-content isolation আবশ্যক।

## Architecture decision

পরবর্তী roadmap-এ MISTY-কে unrestricted autonomous agent না বানিয়ে budgeted cognitive research loop হিসেবে এগোনো হবে। প্রতিটি autonomous tick-এর জন্য bounded candidate selection, evidence retrieval, hypothesis test, confidence update, contradiction event, durable audit record এবং optional action proposal থাকবে। User-facing response কেবল evidence-backed result অথবা explicit uncertainty প্রকাশ করবে। External side effects human-approved বা policy-approved actuator boundary ছাড়া চালানো হবে না।

## Immediate technical priorities

1. Chat rich cognitive metadata API contract সম্পূর্ণ করা।
2. Durable cognitive event/hypothesis/evidence schema ও repository layer যোগ করা।
3. Autonomous tick state machine: select → gather → test → update → consolidate → observe metrics।
4. Contradiction-aware hypothesis ledger এবং provenance scoring।
5. PostgreSQL-required production startup guard ও health diagnostics।
6. Bengali/English autonomy benchmark এবং long-running resource-safety tests।
