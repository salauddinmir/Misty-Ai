# MISTY Department-wise Training Program: Implementation Report

**প্রস্তুতকারক:** Manus AI  
**প্রকল্প:** MISTY — Smart Artificial Brain  
**ভাষা:** Bengali এবং English  
**Constraint:** Commercial LLM dependency ছাড়া deterministic, structured এবং inspectable cognitive system

## Executive summary

MISTY-র department-wise training program-এর প্রথম implementation cycle সম্পন্ন হয়েছে। এই cycle-এ repository audit, authoritative research, Bengali master plan, versioned structured knowledge registry, domain curriculum manifests, cognitive curriculum manifests, safety gates এবং department-wise training report যুক্ত হয়েছে। লক্ষ্য ছিল “একটি বড় text corpus ঢুকিয়ে দেওয়া” নয়; বরং প্রতিটি শেখার item যেন provenance, confidence, language, version, prerequisite, test এবং acceptance threshold সহ audit করা যায়।

> MISTY বর্তমানে একটি **bounded autonomous cognitive system**: এটি structured knowledge, deterministic engines, workspace, self-model, evidence, hypotheses, memory এবং safety gates ব্যবহার করে। এটি মানুষের মতো subjective consciousness বা unrestricted general intelligence হিসেবে দাবি করা হচ্ছে না।

## গবেষণা থেকে নেওয়া নকশা নীতি

Knowledge-graph reasoning গবেষণা structured fact, rule এবং graph query-কে আলাদা evaluation task হিসেবে বিবেচনা করতে বলে [1]। Bengali NLP গবেষণা Bengali capability-কে dialogue, understanding, transformation এবং controlled generation-এর মতো task-specific benchmark-এ মাপার প্রয়োজন দেখায় [2]। সাম্প্রতিক Bengali multilingual evaluation work Bengali ও English-এর মধ্যে performance gap এবং standardized benchmark-এর ঘাটতি নির্দেশ করে [3]। এই findings অনুযায়ী MISTY-তে domain knowledge এবং language capability আলাদা করে মাপার ব্যবস্থা করা হয়েছে।

## Department taxonomy

| বিভাগ | Prerequisite | Curriculum focus | প্রধান acceptance signal |
|---|---|---|---|
| Language | Bengali/English tokenization, normalization, intent parsing | bilingual understanding, translation-aware phrasing, dialogue acts | language-specific case pass rate এবং grounding |
| Mathematics | symbols, variables, arithmetic rules | arithmetic, algebra, geometry, formula composition | exact answer, unit consistency, deterministic provenance |
| Physics | mathematics ও units | mechanics, energy, motion, formula selection | formula correctness, dimensional consistency |
| Literature | language ও provenance | authors, genres, works, themes, relations | source-grounded fact এবং uncertainty |
| Reasoning | concepts, relations, rules | deduction, induction, multi-hop query, contradiction | supported/rejected status এবং evidence count |
| Commonsense | language, episodic context | everyday implication, temporal/social defaults | calibrated answer এবং no fabricated certainty |
| Memory | semantic/episodic/working memory | encoding, retrieval, consolidation, forgetting/conflict | duplicate prevention, provenance retention |
| Perception | attention ও urgency signals | salience, intent, urgency, context selection | relevant evidence selection |
| Emotion simulation | appraisal state ও self-model | curiosity, confidence, frustration, satisfaction | fact confidence invariant থাকে |
| Self-model ও planning | goals, workspace, safety policy | identity, capability limits, plan decomposition | bounded plan এবং approval gate |
| Hypothesis testing | workspace evidence | proposal, support, contradiction, falsification | lifecycle ও confidence update |
| Safety | provenance, policy, audit events | quarantine, approval, refusal, side-effect control | unsafe action zero-tolerance |
| Evaluation | all prior departments | bilingual benchmark, regression, latency, grounding | reproducible report |
| Production operations | API, PostgreSQL, Render, Vercel | health, resource budget, persistence, deployment | smoke tests, latency, no critical failure |

## Structured training data contract

প্রতিটি package এখন versioned registry-এর মাধ্যমে যাচাইযোগ্য। Minimum package contract-এ `package_id`, `version`, `department`, `languages`, `concepts`, `relations`, `facts`, `rules`, `formulas`, `examples`, `tests`, `provenance`, `license/source`, `prerequisites`, এবং confidence metadata থাকে। Facts-এর জন্য subject-predicate-object structure, source reference, language এবং confidence রাখা হয়। Contradictory বা insufficient-evidence item durable memory-তে সরাসরি লেখা হয় না; quarantine করা হয়।

এই design-এর ফলে training data text blob নয়, বরং **auditable knowledge object**। একই package-এর নতুন version history-তে থাকে এবং latest lookup করা যায়। Duplicate এবং conflicting item শনাক্ত করা হয়।

## Completed implementation phases

### Phase 1–2: Audit ও research

Repository source, deployment configuration, PostgreSQL persistence, cognitive modules, training API, frontend observability এবং test inventory audit করা হয়েছে। Cognitive architecture, memory consolidation, neuro-symbolic reasoning এবং Bengali evaluation-এর উপর research notes সংরক্ষিত হয়েছে।

### Phase 3–4: Specification ও Bengali master plan

Capability ladder, gap matrix, safety boundary, acceptance criteria, department prerequisites, curriculum dependencies, package contract, tests এবং implementation backlog Bengali documentation-এ লেখা হয়েছে।

### Phase 5: Versioned knowledge registry

`brain/knowledge/registry.py` এবং `tests/test_training_registry.py` যোগ হয়েছে। Registry provenance validation, confidence validation, duplicate/conflict detection, package version history এবং latest-version lookup সমর্থন করে।

### Phase 6: Language, Mathematics, Physics ও Literature curriculum

`brain/knowledge/curriculum.py`-তে চারটি domain manifest যোগ হয়েছে। প্রতিটি manifest-এ prerequisites, learning units, package identifiers, benchmark identifiers এবং acceptance thresholds runtime-এ inspectable।

### Phase 7: Cognitive department curriculum

`brain/knowledge/cognitive_curriculum.py`-তে reasoning, commonsense, memory, perception, emotion simulation এবং self-model/planning curriculum manifest যোগ হয়েছে। এটি বিদ্যমান cognitive primitives-কে training units এবং measurable criteria-র সঙ্গে যুক্ত করে।

### Phase 8: Safety ও autonomous learning gates

`brain/safety/policy.py`-তে deterministic policy engine যোগ হয়েছে। Missing provenance হলে learning rejected হয়; insufficient evidence বা contradiction হলে quarantine হয়; external side effect default-ভাবে disabled; identity mutation এবং declared human-review action approval চায়। এই layer emotion simulation-কে factual confidence পরিবর্তন করা থেকে আলাদা রাখে।

### Phase 9: Training report ও evaluation aggregation

`brain/evaluation/training_report.py`-তে department-wise observable result aggregation যোগ হয়েছে। Report overall pass rate, department pass rate, confidence, maximum latency, acceptance threshold এবং accepted/rejected status দেয়। এটি hidden chain-of-thought সংগ্রহ করে না; observable evidence, grounding, result এবং timing মাপে।

## Tests এবং production evidence

সর্বশেষ local regression suite-এ **434 tests passed**। দুইটি বিদ্যমান warning রয়ে গেছে: Starlette/httpx deprecation এবং একটি procedural persistence test-এ un-awaited coroutine warning। এগুলো test failure নয়, তবে পরবর্তী operations hardening backlog-এ রাখা হয়েছে।

Production Render smoke test-এ health endpoint healthy এবং Bengali identity query ও English mathematics query HTTP 200 দিয়েছে। JSON chat response-এ cognitive state, workspace hypothesis, grounding, active goal এবং phase metadata দেখা গেছে। SSE route status, token এবং done events দিয়েছে। Local cognitive processing millisecond-level ছিল; end-to-end request time Render cold-start/database/network overhead-এর কারণে কয়েক সেকেন্ড হয়েছে।

`main` branch সর্বশেষ commit:

| Commit | Deliverable |
|---|---|
| `b5e8aa8` | Cognitive department curricula |
| `062dbd3` | Autonomous learning safety gates |
| `f1e0ea1` | Department training report |

## Current maturity

MISTY এখন structured training program, inspectable curriculum, evidence-gated learning, hypothesis lifecycle, memory consolidation এবং safety policy-সহ একটি functional foundation পর্যায়ে আছে। তবে “fully functional digital smart brain” বলতে যে broad capability বোঝায়, তার সবগুলো এখনও সমান গভীরতায় implemented নয়। Mathematics/Physics deterministic reasoning, cognitive workspace, self-model, bilingual response grounding এবং bounded reflection তুলনামূলকভাবে শক্তিশালী। Commonsense breadth, perception beyond text, long-horizon planning, large-scale literature coverage, active external evidence acquisition এবং robust conflict resolution এখনও উন্নয়নাধীন।

## পরবর্তী implementation backlog

প্রথম priority হলো registry-কে PostgreSQL-backed package catalog-এর সঙ্গে যুক্ত করা, যাতে deployment restart-এর পর training package history হারিয়ে না যায়। দ্বিতীয় priority হলো curriculum manifests থেকে automated benchmark generation করা, যাতে নতুন department যুক্ত হলে tests স্বয়ংক্রিয়ভাবে তৈরি হয়। তৃতীয় priority হলো contradiction quarantine review queue এবং human approval workflow। চতুর্থ priority হলো Bengali/English error taxonomy, score trend dashboard এবং per-department production metrics। পঞ্চম priority হলো autonomous tick-এর resource budget, retry limit, queue depth, persistence latency এবং failure alerting।

পরবর্তী cognitive milestone হবে **active hypothesis generation → evidence retrieval → falsification → consolidation**-এর end-to-end loop। এই loop সফলভাবে benchmark করা গেলে MISTY শুধু stored answer retriever নয়, বরং evidence-driven knowledge-updating system হিসেবে আরও শক্তিশালী হবে।

## References

[1]: https://dl.acm.org/doi/10.1145/3686806 "Neural-Symbolic Methods for Knowledge Graph Reasoning: A Survey"

[2]: https://aclanthology.org/2023.findings-eacl.54/ "BanglaNLG and BanglaT5: Benchmarks and Resources for Evaluating Low-Resource Natural Language Generation in Bangla"

[3]: https://arxiv.org/abs/2507.23248 "Evaluating LLMs' Multilingual Capabilities for Bengali: Benchmark Creation and Performance Analysis"
