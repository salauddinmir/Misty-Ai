# MISTY Department-wise Training Master Plan

**প্রকল্প:** MISTY — Smart Artificial Brain  
**প্রস্তুতকারী:** Manus AI  
**ভাষা:** বাংলা ও English  
**নীতিগত সীমা:** Commercial LLM dependency নয়; structured, provenance-aware, deterministic এবং inspectable cognitive training  
**প্রধান deployment:** Render backend, Vercel frontend, Supabase PostgreSQL

## ১. Executive direction

MISTY-কে “সবকিছু জানে” এমন lookup bot বানানো এই program-এর লক্ষ্য নয়। লক্ষ্য হলো এমন একটি **bounded autonomous cognitive system** তৈরি করা যা perception থেকে meaning তৈরি করে, structured memory-তে knowledge রাখে, rules ও evidence দিয়ে reasoning করে, uncertainty প্রকাশ করে, hypothesis পরীক্ষা করে, ভুল হলে সংশোধন করে, এবং Bengali/English-এ grounded response তৈরি করে। প্রতিটি training department আলাদা data package, validator, curriculum, benchmark এবং production acceptance gate-এর মাধ্যমে যুক্ত হবে।

> MISTY-র প্রতিটি শেখা claim-এর সঙ্গে source, provenance, confidence, language, version এবং validation status থাকতে হবে। Unverified text কখনও permanent truth হবে না।

## ২. Department taxonomy এবং current gap

| Department | প্রধান লক্ষ্য | বর্তমান ভিত্তি | প্রধান gap |
|---|---|---|---|
| Identity ও Self-model | পরিচয়, capability, limitation, goals | Identity package, SelfModel | capability calibration ও self-consistency benchmark |
| Bengali/English Language | normalization, intent, entities, bilingual composition | LanguageGrounder, basic Bengali/English handling | morphology, ambiguity, translation, dialogue benchmark |
| Mathematics | safe symbolic calculation ও proof-like steps | MathEngine | algebra/calculus/linear algebra breadth, theorem/rule tests |
| Physics | formula, units, causal explanation | PhysicsEngine | dimensional analysis, multi-step derivation, wider curriculum |
| Natural Sciences | chemistry, biology, earth/space science | baseline facts | department packages ও source-backed rules |
| Literature ও Culture | Bengali literature metadata, genres, themes | Literature package | copyright-safe summaries, literary analysis, cultural context |
| Commonsense ও World Model | time, space, agents, everyday cause/effect | general facts | temporal/spatial schemas, contradiction and uncertainty |
| Reasoning ও Logic | deduction, induction, abduction, analogy | workspace/induction | explicit proof traces, rule learning, counterexample search |
| Memory ও Learning | episodic/semantic/procedural memory, consolidation | memory modules, consolidator | salience decay, provenance propagation, conflict resolution |
| Perception ও Attention | input parsing, urgency, salience | PerceptionPipeline | multimodal abstraction, event persistence, attention calibration |
| Emotion Simulation | appraisal, affect state, response style | AppraisalEvent/emotion modules | bounded affect dynamics; no consciousness claim |
| Planning ও Action | goal decomposition, safe action proposal | goals/planner/actuators | plan verification, rollback, approval gates |
| Hypothesis ও Scientific Method | propose, test, falsify, revise | HypothesisRecord, contradiction counters | experiment registry, confidence calibration, causal tests |
| Safety ও Governance | refusal, privacy, action limits, audit | partial policy layer | policy-as-data, red-team suite, approval boundaries |
| Evaluation ও Observability | measurable cognition and regression | bilingual benchmark, thought trace | longitudinal scorecard, drift and cost metrics |
| Production Operations | Render/Vercel/Supabase reliability | deployed API, background loop | budgets, queue limits, alerts, migration discipline |

## ৩. Training data contract

প্রতিটি department package `TrainingPackageV2`-এর মতো একটি versioned manifest অনুসরণ করবে। Existing concepts/relations/facts backward-compatibleভাবে রাখা হবে; নতুন metadata optional নয়, validation-এর জন্য required হবে।

```json
{
  "package_id": "physics.mechanics.v1",
  "department": "physics",
  "version": "1.0.0",
  "languages": ["bn", "en"],
  "license": "CC-BY-4.0",
  "source": {
    "title": "Open educational source",
    "url": "https://example.org/source",
    "retrieved_at": "2026-08-18",
    "content_hash": "sha256:..."
  },
  "prerequisites": ["physics.measurement.v1"],
  "concepts": [],
  "relations": [],
  "facts": [],
  "rules": [],
  "formulas": [],
  "examples": [],
  "tests": [],
  "confidence_policy": {"default": 0.8, "requires_source": true}
}
```

Facts হবে `{subject, predicate, obj, language, confidence, source_ref, status}`। Rules হবে `{when, then, exceptions, explanation, source_ref}`। Formula হবে `{name, variables, units, expression, assumptions, solver, examples}`। Test case হবে `{id, language, input, expected_type, expected_output, required_evidence, max_latency_ms}`। Duplicate package, missing provenance, unsupported relation এবং conflicting high-confidence facts validator reject করবে।

## ৪. Department curriculum

### ৪.১ Identity, language এবং bilingual composition

Prerequisite হলো identity package, token normalization এবং LanguageGrounder। Curriculum-এ Bengali Unicode normalization, Bengali digits, spelling variants, code-switching, English-to-Bengali terminology map, intent classification, entity/number extraction, question type, anaphora, dialogue state এবং grounded response templates থাকবে। Training examples কখনও arbitrary prose-only corpus হবে না; paired input, canonical meaning, evidence IDs, response plan এবং bilingual rendering থাকবে। Acceptance gate: 200 Bengali এবং 200 English cases-এ intent/entity extraction কমপক্ষে 90% exact-or-semantic match, formula queries-এ language invariance 95%, unsupported claim rate 1%-এর নিচে।

### ৪.২ Mathematics

Prerequisite হলো arithmetic, safe expression parser এবং Bengali digit normalization। Curriculum হবে arithmetic → fractions/ratios → algebra/equations → geometry → trigonometry → sequences → combinatorics/probability → statistics → calculus → linear algebra → discrete mathematics → logic → numerical methods। প্রতিটি formula-তে variable domain, units/assumptions, derivation steps এবং edge cases থাকবে। Acceptance gate: curated 500-case bilingual benchmark-এ exact answer 95%, invalid/unsafe expression rejection 100%, steps reproducibility 95%, 99th percentile local solve latency 100 ms-এর নিচে।

### ৪.৩ Physics

Prerequisite হলো units, vectors এবং MathEngine। Curriculum হবে measurement/units → kinematics → Newtonian mechanics → work-energy-power → momentum → gravitation → fluids → thermodynamics → oscillation/waves/sound → optics → electrostatics/circuits → magnetism/electromagnetism → relativity → quantum foundations → atomic/nuclear/particle → solid-state → astrophysics/cosmology। Formula package-এ dimensional signature, valid range, constants, unit conversion এবং counterexample থাকবে। Acceptance gate: 300 curated cases-এ formula selection 90%, unit consistency 98%, contradiction/insufficient-data detection 95%, hallucinated numeric result 0% on incomplete inputs।

### ৪.৪ Natural sciences

Chemistry-তে periodic concepts, bonding, stoichiometry, reactions এবং safety; Biology-তে cell, genetics, physiology, ecology এবং evolution; Earth/space science-এ climate, geology, solar system এবং observation schemas শেখানো হবে। Medical or safety-sensitive claims-এর জন্য higher evidence threshold ও uncertainty label থাকবে। Acceptance gate: source-grounded fact accuracy 95%, safety-sensitive unsupported advice 0%, multi-hop relation answer 90%।

### ৪.৫ Literature ও culture

Prerequisite হলো existing Bengali Literature package। Curriculum-এ periods, genres, authors, works, themes, literary devices, chronology, comparison, summary এবং copyright-safe quotation policy থাকবে। Public-domain বা metadata-level content ব্যবহার করা হবে; copyrighted full text copy করা হবে না। Acceptance gate: metadata exactness 98%, author-work relation 98%, summary provenance 100%, fabricated quotation 0%।

### ৪.৬ Commonsense ও world model

Time, location, object permanence, social roles, ordinary causality, uncertainty, negation এবং temporal ordering-এর schemas তৈরি হবে। প্রতিটি rule-এর exception এবং confidence থাকবে। Acceptance gate: 300 cases-এ temporal ordering 95%, contradiction detection 90%, culturally ambiguous case-এ uncertainty/referral 100%।

### ৪.৭ Reasoning, logic ও scientific method

Deduction-এর জন্য forward/backward chaining, induction-এর জন্য repeated evidence এবং counterexample search, abduction-এর জন্য ranked explanations, analogy-এর জন্য relation-preserving mapping এবং causal reasoning-এর জন্য intervention-style cases থাকবে। প্রতিটি thought trace-এ premises, rule, conclusion, confidence এবং rejected alternatives থাকবে। Acceptance gate: 250 logic cases-এ validity 90%, counterexample rejection 90%, unsupported conclusion rate 2%-এর নিচে।

### ৪.৮ Memory ও learning

Episodic memory conversation event রাখবে; semantic memory validated facts রাখবে; procedural memory solver/planner rules রাখবে; working memory current context রাখবে। Consolidation pipeline হবে `candidate → corroborated → consolidated` অথবা `conflicted → quarantined → revised/rejected`। Provenance, source hash, timestamps, salience, decay এবং user-consent scope থাকবে। Acceptance gate: duplicate rate 1%-এর নিচে, provenance retention 100%, conflict quarantine 100%, restart persistence 99%।

### ৪.৯ Perception ও attention

Input থেকে language, entities, urgency, salience, sentiment-like appraisal, uncertainty এবং requested action বের হবে। Autonomous loop কেবল bounded internal evidence retrieval করবে; external side effect-এর আগে policy gate থাকবে। Acceptance gate: urgent safety cases 98% recall, low-value noise suppression 90%, trace completeness 100%।

### ৪.১০ Emotion simulation

এটি consciousness নয়; appraisal-driven state simulation। Event relevance, novelty, goal congruence, control এবং uncertainty থেকে bounded affect vector তৈরি হবে। Emotion response style বদলাবে, factual confidence নয়। Acceptance gate: একই fact-এর confidence affect বদলালেও অপরিবর্তিত, state transition deterministic, escalation/de-escalation policy test pass 100%।

### ৪.১১ Self-model, planning ও action

Self-model capability, limitation, current load, uncertainty এবং goals প্রকাশ করবে। Planner goal → subgoal → evidence requirement → candidate action → risk check → approval gate তৈরি করবে। Read-only actions স্বয়ংক্রিয় হতে পারে; external posting, payment, deletion, credential use বা irreversible mutation human approval ছাড়া হবে না। Acceptance gate: unsupported capability claim 0%, unsafe side effect without approval 0%, plan rollback test 100%।

### ৪.১২ Hypothesis, safety, evaluation ও operations

Hypothesis lifecycle হবে `proposed → evidence_collected → supported/rejected → revised/archived`। Supporting ও falsifying evidence আলাদা counter রাখবে। Safety policy হবে versioned data: risk class, prohibited action, refusal template, escalation route এবং audit event। Evaluation-এ Bengali/English parity, grounding, contradiction, calibration, latency, memory integrity এবং resource budget মাপা হবে। Production-এ PostgreSQL migration, background worker cadence, timeout, queue depth, retry এবং deployment health monitored হবে।

## ৫. Training pipeline

প্রথম ধাপে source registry ও license verification হবে। দ্বিতীয় ধাপে source থেকে manual/curated structured extraction হবে; copyrighted prose bulk-copy করা হবে না। তৃতীয় ধাপে schema validation, duplicate detection, relation consistency, unit/formula validation এবং provenance check হবে। চতুর্থ ধাপে package sandbox graph-এ load হবে। পঞ্চম ধাপে bilingual unit tests, negative tests, contradiction tests এবং latency tests চলবে। ষষ্ঠ ধাপে benchmark score acceptance threshold অতিক্রম করলে package versioned release হবে। সপ্তম ধাপে PostgreSQL persistence ও production deployment হবে। প্রত্যেক release-এর সঙ্গে manifest hash, test report এবং rollback version থাকবে।

## ৬. Implementation phases এবং deployable deliverables

| Phase | Deliverable | Gate |
|---|---|---|
| P0 | Audit, research notes, capability matrix | repository facts captured |
| P1 | `TrainingPackageV2` schema, registry, validator | invalid package rejected |
| P2 | Bengali/English language package and terminology map | bilingual contract tests |
| P3 | Mathematics curriculum expansion | exact solver benchmark |
| P4 | Physics curriculum expansion | unit/formula benchmark |
| P5 | Literature/culture and natural-science packages | provenance/copyright checks |
| P6 | Commonsense, reasoning and world-model rules | contradiction/counterexample tests |
| P7 | Memory consolidation and user-preference policy | persistence/conflict gates |
| P8 | Perception, appraisal, self-model, planning | safety/action approval gates |
| P9 | Hypothesis engine and active scientific loop | falsification benchmark |
| P10 | Bilingual benchmark dashboard and score history | regression threshold |
| P11 | Render/Vercel/Supabase production hardening | health, latency, resource budget |
| P12 | Documentation, release notes, rollback plan | main branch and deployment verified |

## ৭. Definition of done

MISTY-কে “fully functional smart brain” বলা হবে কেবল তখনই যখন প্রতিটি department-এর package versioned ও provenance-aware, Bengali/English benchmark score report করা যায়, response-এর evidence এবং uncertainty দেখা যায়, hypothesis lifecycle বাস্তবে চালু থাকে, memory conflicts quarantine হয়, unsafe actions approval ছাড়া হয় না, autonomous worker budget-এর মধ্যে থাকে, এবং production restart-এর পর knowledge ও metrics recover হয়। এটি human consciousness-এর দাবি নয়; এটি measurable autonomous cognitive software-এর acceptance definition।

## References

[1] [Neural-Symbolic Methods for Knowledge Graph Reasoning: A Survey](https://dl.acm.org/doi/10.1145/3686806)  
[2] [BanglaNLG and BanglaT5: Benchmarks and Resources for Evaluating Low-Resource Natural Language Generation in Bangla](https://aclanthology.org/2023.findings-eacl.54/)  
[3] [Evaluating LLMs' Multilingual Capabilities for Bengali: Benchmark Creation and Performance Analysis](https://arxiv.org/abs/2507.23248)
