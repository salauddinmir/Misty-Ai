# MISTY Autonomous Smart Brain — Master Roadmap

**Project:** MISTY — Smart Artificial Brain  
**Organization:** Pixline Incorporate  
**Founder:** Salauddin Mir (Netvai)  
**Architecture constraint:** No commercial LLM dependency; Bengali ও English support; PostgreSQL production; Render backend; Vercel frontend; Supabase database.

> **Engineering promise:** MISTY-কে “মানুষের মতো consciousness” বলা হবে না। লক্ষ্য হলো একটি measurable, persistent, inspectable, bilingual এবং bounded autonomous cognitive system তৈরি করা, যে evidence, uncertainty, hypothesis, memory এবং policy budget-এর ভিত্তিতে কাজ করবে।

## Executive diagnosis

MISTY বর্তমানে structured knowledge, deterministic reasoning, cognitive workspace, self-model, grounding, memory subsystems, autonomous reflection foundation এবং production chat infrastructure অর্জন করেছে। বর্তমান maturity হলো **L5–L6 foundation**। Smart brain-এর পরবর্তী অগ্রগতি নির্ভর করবে generic reflection-কে closed-loop active cognition-এ রূপান্তরের উপর: uncertainty target নির্বাচন, evidence gathering, prediction, test, falsification, contradiction handling, reversible consolidation এবং benchmarked improvement।

## Phase map

| Phase | Focus | Primary output | Completion gate |
|---|---|---|---|
| 0–12 | Existing foundation ও production hardening | Stable cognitive runtime | বর্তমান baseline: 408 tests, Render/Vercel healthy |
| 13 | Contract and persistence foundation | Rich API metadata, typed cognitive audit schema, PostgreSQL migration | API contract ও migration tests pass |
| 14 | Active inner loop | Candidate selector, evidence providers, prediction/error cycle | bounded autonomous tick measurable |
| 15 | Hypothesis laboratory | proposal, test, falsification, contradiction ledger | curated positive/negative cases pass |
| 16 | Memory consolidation | tentative/promoted/quarantined memory lifecycle | restart, rollback, provenance pass |
| 17 | Bilingual learning | Bengali/English paired corpus ও benchmark runner | parity gap threshold pass |
| 18 | Self-model and user adaptation | scoped preferences, capability calibration, uncertainty | preference decay/correction pass |
| 19 | Governed autonomy | budgets, permissions, safe actions, audit and recovery | no unauthorized side effects |
| 20 | Observability and production operations | dashboard, metrics, alerts, replay | soak/resource tests pass |
| 21+ | Broad competence | mathematics, physics, literature, science, multimodality | domain-specific acceptance gates |

## Phase 13 — Contract এবং durable cognitive ledger

প্রথমে `Brain.process()`-এর rich output (`thought_trace`, `self_model`, `cognitive_workspace`, `grounding`, `phase_timings_ms`) FastAPI `ChatResponse` model-এ সম্পূর্ণ ফেরত দিতে হবে। JSON ও SSE done event-এ একই versioned contract থাকতে হবে। এরপর PostgreSQL-এ `autonomy_ticks`, `hypotheses`, `evidence`, `contradictions`, `memory_candidates`, `memory_promotions` এবং `cognitive_events` tables যোগ করতে হবে। প্রত্যেক record-এ ID, source, confidence, timestamps, scope, status এবং provenance থাকবে। Writes idempotent হবে; duplicate retry-তে duplicate truth তৈরি হবে না।

**Deliverables:** migration SQL, database methods, Pydantic response models, API tests, restart restore test, Bengali documentation।

## Phase 14 — Active autonomous inner loop

Inner loop-এর প্রতি tick প্রথমে brain state থেকে unresolved goal, high uncertainty অথবা stale prediction নির্বাচন করবে। Candidate selector salience, uncertainty, expected information gain, freshness এবং cost ব্যবহার করে একটি bounded internal question বেছে নেবে। Evidence provider registry প্রথমে internal sources ব্যবহার করবে: semantic memory, episodic memory, concept graph, procedural rules, prior cognitive traces এবং benchmark fixtures। External retrieval প্রথম release-এ read-only allowlist, timeout, size limit এবং provenance ছাড়া চালু হবে না।

Tick state machine হবে: `select → retrieve → predict → test → score_error → update_workspace → queue_memory → persist_audit`। কোনো valid evidence না থাকলে outcome হবে `no_evidence`, fabricated fact নয়। প্রতিটি tick সর্বোচ্চ time budget, evidence count এবং mutation count মানবে।

## Phase 15 — Hypothesis laboratory

Hypothesis কেবল statement নয়; তার premises, predictions, expected observations, test method, evidence references, confidence prior, confidence posterior, contradiction count, status এবং revision lineage থাকবে। Test adapters domain অনুযায়ী ভাগ হবে: arithmetic/formula evaluator, graph relation check, semantic fact consistency, dialogue preference check এবং deterministic replay।

একটি negative test hypothesis-কে reject বা revise করবে। Supportive evidence পেলেই confidence বাড়বে না; source independence, reliability এবং contradiction penalty বিবেচনা করতে হবে। একই evidence বারবার confidence বাড়াবে না। Conflicting records durable contradiction ledger-এ যাবে; user-facing answer-এ unresolved conflict প্রকাশ করা হবে।

## Phase 16 — Memory consolidation এবং governance

সব নতুন learning প্রথমে tentative episode/candidate হবে। Promotion-এর জন্য minimum provenance, repeated or independent support, contradiction scan, confidence threshold এবং scope declaration লাগবে। Promoted memory-রও expiry/decay এবং correction path থাকবে। Quarantined memory recall-এ low-priority evidence হিসেবে আসবে, truth হিসেবে নয়। User-provided preferences আলাদা scoped namespace-এ থাকবে; একজন user-এর preference অন্য user-এর knowledge হবে না। Sensitive content-এর retention policy ও deletion path থাকবে।

## Phase 17 — Bengali/English learning ও benchmark

একই capability-এর Bengali ও English paired cases তৈরি হবে। Benchmark categories হবে identity, facts, math, physics, literature, coreference, multi-turn memory, uncertainty, contradiction, hypothesis testing, grounding, latency এবং safety। প্রত্যেক case-এ expected answer constraints, acceptable evidence, allowed uncertainty range এবং prohibited claims থাকবে। Report শুধু accuracy নয়; unsupported claim rate, evidence coverage, calibration error, contradiction detection, memory retention এবং P95 latency দেখাবে।

## Phase 18 — Self-model, preference এবং metacognition

SelfModel-এ capability claims evidence-backed হবে। MISTY কোনো domain-এ benchmark fail করলে capability confidence কমবে এবং answer policy clarification চাইবে। User preference hypothesis language, response length, preferred name এবং interaction style-এর মতো low-risk scoped attributes নিয়ে কাজ করবে। Preference repeated evidence না পেলে decay করবে এবং direct correction-এ immediately revise হবে।

## Phase 19 — Governed autonomy এবং actuator safety

Autonomy তিন tier-এ থাকবে: internal computation, reversible memory mutation এবং external side effect। প্রথম দুই tier budgetedভাবে automatic হতে পারে। External message, account action, sensor/actuator command বা irreversible mutation policy approval ছাড়া চলবে না। প্রতিটি action-এর authority, target, expected effect, rollback এবং expiry থাকবে। Untrusted webpage/file instruction কখনও policy হিসেবে গ্রহণ করা যাবে না।

## Phase 20 — Observability এবং operations

Dashboard-এ latest cognitive cycle, autonomous tick history, hypothesis status, evidence provenance, contradiction count, memory promotions, queue depth, tick duration, database latency, error rate এবং resource budget দেখা যাবে। Render-এ health endpoint-এ database driver, autonomy status, last tick, last error এবং queue metrics-এর sanitized summary থাকবে। Sensitive content health response-এ যাবে না। Structured logs correlation ID সহ হবে।

Production controls হিসেবে `MISTY_AUTONOMY_ENABLED`, interval, max tick duration, per-hour tick quota, evidence quota, write quota, shutdown drain timeout এবং circuit breaker থাকবে। 24-hour soak, restart recovery, duplicate retry এবং database outage simulation release gate-এর অংশ হবে।

## Phase 21+ — Domain expansion

Mathematics ও Physics package-কে algebra, geometry, calculus, probability, statistics, mechanics, electromagnetism, thermodynamics এবং scientific method-এর পৃথক verified modules-এ ভাগ করতে হবে। Bengali literature package-এ source metadata, author/work chronology, genre relation এবং quotation provenance যোগ হবে। প্রতিটি domain package training নয়, বরং versioned knowledge artifact হিসেবে release হবে এবং benchmark fixture দিয়ে যাচাই হবে।

## Priority backlog

| Priority | Work item | Depends on | Release value |
|---|---|---|---|
| P0 | API rich metadata contract fix | none | frontend সত্যিকারের trace দেখাবে |
| P0 | PostgreSQL cognitive ledger migration | schema review | durable autonomy ও audit |
| P0 | Active inner-loop selector/provider interface | ledger | reflection থেকে cognition |
| P1 | Prediction/error এবং falsification adapters | selector | hypothesis testing |
| P1 | Contradiction ledger ও revision lineage | hypothesis records | ভুল knowledge control |
| P1 | Memory promotion/quarantine policy | provenance | safe learning |
| P1 | Bengali/English benchmark runner | response contract | measurable improvement |
| P2 | Preference model এবং self-calibration | benchmark | personalization |
| P2 | Autonomy dashboard ও operational metrics | ledger | inspectability |
| P2 | External read-only evidence provider | safety policy | controlled world grounding |
| P3 | Approved actuators and multimodal memory | governance | embodied capability |

## Release gates

কোনো phase “complete” হবে না যতক্ষণ implementation, tests, migration, replay fixture, documentation এবং rollback strategy একসাথে না থাকে। Production release-এর আগে সব tests pass, schema migration idempotent, JSON/SSE contract consistent, no unauthorized side effect, P95 latency budget-এর মধ্যে এবং autonomous worker shutdown clean হতে হবে।

## Success definition

MISTY তখনই production-grade autonomous smart brain-এর কাছাকাছি ধরা হবে যখন সে নিজের uncertainty থেকে bounded question নির্বাচন করতে পারে, internal/provenanced evidence সংগ্রহ করতে পারে, falsifiable hypothesis পরীক্ষা করতে পারে, contradiction লুকায় না, memory reversibleভাবে consolidate করে, Bengali ও English-এ calibrated grounded output দেয়, এবং সব cognitive mutation audit/replay করা যায়।

## References

[1]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9292365/ "Extended active inference: Constructing predictive cognition beyond skulls"
[2]: https://arxiv.org/html/2512.23343v1 "AI Meets Brain: A Unified Survey on Memory Systems from Cognitive Neuroscience to Autonomous Agents"
[3]: https://arxiv.org/abs/2606.30306 "Always-OnAgents: A Survey of Persistent Memory, State, and Governance in LLM Agents"
[4]: https://arxiv.org/html/2507.21504v1 "Evaluation and Benchmarking of LLM Agents: A Survey"
