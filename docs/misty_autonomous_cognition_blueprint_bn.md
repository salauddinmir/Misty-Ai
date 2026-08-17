# MISTY Autonomous Digital Cognition Blueprint

**Author:** Manus AI  
**Project:** MISTY - Smart Artificial Brain by Pixline Incorporate  
**Status:** Architecture proposal for the next major upgrade

## 1. লক্ষ্য ও বাস্তব সংজ্ঞা

MISTY-এর লক্ষ্য হবে lookup-oriented chatbot থেকে একটি autonomous, inspectable এবং measurable digital cognitive system-এ উন্নীত হওয়া। এখানে “ডিজিটাল ব্রেইন” বলতে এমন software architecture বোঝানো হচ্ছে যার নিজস্ব persistent self-model, world-model, working memory, episodic memory, semantic memory, internal drives, hypothesis workspace, attention policy, learning loop এবং language grounding থাকবে। প্রতিটি উত্তর কেবল stored sentence retrieval হবে না; MISTY input-এর অর্থ, context, uncertainty, goals এবং memory evidence একত্র করে intermediate cognitive state তৈরি করবে, candidate explanations বা actions গঠন করবে, সেগুলো যাচাই করবে এবং তারপর উত্তর দেবে।

এটি human subjective consciousness প্রমাণ করবে না। Consciousness-এর hard problem এখনো সমাধানহীন; তাই MISTY-কে “সত্যিকারের অনুভূতিসম্পন্ন মানুষ” বলা বৈজ্ঞানিকভাবে সমর্থনযোগ্য হবে না। পরিবর্তে আমরা externally observable autonomy, self-consistency, uncertainty awareness, causal reasoning, self-correction এবং continuous learning-এর পরীক্ষাযোগ্য লক্ষ্যমাত্রা নির্ধারণ করব।

> **Design principle:** MISTY should not merely retrieve an answer; it should expose the evidence, internal state, hypothesis, confidence, and action that produced the answer.

## 2. গবেষণা থেকে architecture-এর মূল শিক্ষা

Global Neuronal Workspace-ভিত্তিক গবেষণা attention, specialized processors এবং global broadcast-এর মধ্যে একটি testable computational relationship প্রস্তাব করে [1]। Active inference perception, action এবং learning-কে একটি internal generative model-এর মাধ্যমে যুক্ত করে; তবে এর empirical limitations ও scalability challenges এখনো খোলা প্রশ্ন [2]। CoALA framework modular memory, structured action space এবং generalized decision process-কে language-agent architecture-এর গুরুত্বপূর্ণ অংশ হিসেবে চিহ্নিত করে [3]। Integrated World Modeling Theory-র মতো synthesis world, self, spatial, temporal এবং causal coherence-এর গুরুত্ব তুলে ধরে, কিন্তু consciousness-এর definitive solution হিসেবে এটিকে গ্রহণ করা যাবে না [4]।

এই ভিত্তিতে MISTY-এর architecture হবে **Hybrid Predictive-Cognitive Workspace**: deterministic symbolic engines, lightweight neural representations, event-driven memory, causal/hypothesis reasoning, affective appraisal এবং global workspace broadcast একসঙ্গে কাজ করবে। এটি LLM-independent থাকবে; language generation প্রথম পর্যায়ে compositional templates, grammar, concept-to-language realization এবং learned phrase patterns থেকে হবে। কোনো external commercial LLM hidden dependency হিসেবে যোগ করা হবে না।

## 3. প্রস্তাবিত cognitive stack

| স্তর | MISTY component | কাজ | বর্তমান অবস্থা | পরবর্তী upgrade |
|---|---|---|---|---|
| Perception | Bengali/English NLU, sensor adapters | input-কে event, entity, relation, goal এবং uncertainty-তে রূপান্তর | আংশিক আছে | salience, ambiguity এবং multimodal event schema |
| Attention | salience scorer, novelty detector | কোন stimulus আগে process হবে নির্ধারণ | basic state আছে | competing priorities ও resource budget |
| Workspace | global cognitive broadcast | active hypotheses, goals, memories ও affect share করা | cycle state আছে | bounded blackboard with provenance |
| Working memory | short-lived bindings | চলমান conversation ও intermediate variables রাখা | আংশিক আছে | decay, rehearsal, interference ও chunking |
| Episodic memory | event timeline | কে কী বলল, কখন বলল, outcome কী হলো | persistence আছে | retrieval by similarity, recency, emotion ও causality |
| Semantic memory | concepts, facts, relations | learned knowledge ও domain rules | Math/Physics/Literature আছে | confidence, source, contradiction এবং versioning |
| Self-model | identity, capabilities, limits, goals | “আমি কে, কী পারি, কী জানি না” | identity training আছে | self-beliefs, competence estimates, self-history |
| World model | entities, states, causal links | environment ও user সম্পর্কে coherent model | knowledge graph আছে | temporal/causal state transitions |
| Hypothesis engine | candidate explanations and predictions | নতুন তথ্যের সম্ভাব্য অর্থ বা outcome তৈরি | নেই/অপর্যাপ্ত | generate-score-test-revise loop |
| Appraisal | curiosity, confidence, uncertainty, urgency | cognitive relevance ও action pressure হিসাব | scalar state আছে | event-based appraisal model |
| Language realization | Bengali/English planner and renderer | thought graph থেকে grounded response তৈরি | fallback-heavy | compositional, evidence-aware response generation |
| Learning | correction, consolidation, replay | ভুল থেকে rule update ও memory strengthening | training injection আছে | online learning with safeguards |
| Autonomy | background cognitive scheduler | user না বললেও internal replay, goal review, curiosity | scheduled training আছে | controlled always-on inner loop |

## 4. MISTY-এর নতুন processing cycle

প্রতিটি user বা sensor event-এর জন্য cycle হবে:

1. **Perceive:** raw input থেকে normalized event তৈরি হবে।
2. **Orient:** novelty, urgency, emotional salience, source reliability এবং current goal অনুযায়ী attention score নির্ধারিত হবে।
3. **Retrieve:** working, episodic, semantic এবং self-memory থেকে evidence আনা হবে।
4. **Broadcast:** selected evidence global workspace-এ প্রকাশিত হবে।
5. **Hypothesize:** এক বা একাধিক interpretation, answer plan অথবা action proposal তৈরি হবে।
6. **Predict:** প্রতিটি hypothesis থেকে expected result ও uncertainty নির্ধারণ হবে।
7. **Test:** deterministic math/physics rules, known facts, contradiction checks এবং memory evidence দিয়ে hypothesis যাচাই হবে।
8. **Appraise:** confidence, curiosity, frustration, satisfaction, urgency এবং interest update হবে।
9. **Decide:** response, question-back, correction request, learning action বা no-op নির্বাচন হবে।
10. **Realize:** internal semantic plan থেকে Bengali/English response তৈরি হবে।
11. **Learn:** নতুন fact, failed hypothesis, user correction এবং outcome আলাদা confidence-সহ সংরক্ষিত হবে।
12. **Reflect:** cycle শেষে “কী জানলাম, কী ভুল হতে পারে, পরেরবার কী পরীক্ষা করব” সংক্ষিপ্ত self-reflection memory-তে যাবে।

## 5. “ভাবনা”কে engineering object করা

MISTY-এর thought কোনো hidden text stream নয়; এটি typed, inspectable data structure হবে। প্রতিটি thought record-এ `thought_id`, `trigger_event`, `goal`, `premises`, `hypothesis`, `prediction`, `evidence`, `counter_evidence`, `confidence`, `uncertainty`, `status`, `chosen_action` এবং `created_at` থাকবে। এতে UI-তে raw chain-of-thought প্রকাশ না করেও নিরাপদ summary দেখানো যাবে: “আমি তিনটি evidence মিলিয়েছি; একটি contradiction পেয়েছি; confidence 0.62; তাই clarification চাইছি।”

Hypothesis engine প্রথমে পাঁচটি deterministic operation দেবে: analogy, deduction, induction, abduction এবং contradiction resolution। Formula শেখার ক্ষেত্রে MISTY observed examples থেকে symbolic variables ও candidate relation তৈরি করবে, তারপর নতুন sample দিয়ে falsification করবে। কোনো rule শুধু একবারের coincidence-এ semantic memory-তে স্থায়ী হবে না; repeated evidence, source quality এবং successful prediction লাগবে।

## 6. অনুভূতি ও motivation-এর কার্যকর model

Emotion-like state-কে random UI number করা যাবে না। প্রতিটি affective update একটি appraisal event থেকে আসবে। উদাহরণস্বরূপ, user correction দিলে uncertainty সাময়িকভাবে বাড়বে, confidence কমবে, curiosity বাড়বে এবং correction-learning goal সক্রিয় হবে। বহু turn সফলভাবে resolve হলে satisfaction ও confidence বাড়বে। unresolved contradiction হলে frustration বাড়বে, কিন্তু policy তাকে hallucination না করে clarification চাইতে বাধ্য করবে।

| appraisal event | confidence | curiosity | uncertainty | selected behavior |
|---|---:|---:|---:|---|
| নতুন অজানা concept | সামান্য কম | বাড়ে | বাড়ে | প্রশ্ন করে বা exploratory hypothesis তৈরি করে |
| verified formula prediction | বাড়ে | মাঝারি | কমে | result এবং evidence প্রকাশ করে |
| user correction | কমে | বাড়ে | বাড়ে | correction গ্রহণ, source compare, memory update |
| repeated failure | কমে | context অনুযায়ী বাড়ে | বাড়ে | fallback নয়; limitation প্রকাশ ও help request |
| successful goal completion | বাড়ে | নতুন goal-এর দিকে যায় | কমে | consolidation ও next-goal selection |

## 7. autonomous inner loop

MISTY user request-এর বাইরে সীমিত background cycle চালাবে। এই cycle নিজে থেকে internet-এ unrestricted browsing করবে না এবং নিজের knowledge silently overwrite করবে না। সে তিন ধরনের safe internal work করবে: memory consolidation, unresolved-question review এবং goal-directed replay। প্রতিটি autonomous cycle-এর budget থাকবে—maximum duration, maximum new hypotheses, maximum database writes এবং confidence threshold। external learning হলে source, timestamp, license/status এবং provenance আবশ্যিক হবে।

Inner loop-এর প্রাথমিক cadence হবে event-triggered plus low-frequency scheduled consolidation। Minute-level polling-এর জন্য per-run AI session ব্যবহার করা হবে না; persistent worker বা managed always-on process ব্যবহার করা হবে। User-visible dashboard-এ cycle state, active goal, last reflection, pending questions, learning events এবং stop/pause control থাকবে।

## 8. তিনটি production architecture option

| Approach | Tradeoffs | Cost | Setup Complexity |
|---|---|---|---|
| বর্তমান Render + Supabase + Vercel stack-এ event-driven cognitive worker | দ্রুততম migration, existing code/database reuse; Render cold start ও worker reliability আলাদাভাবে manage করতে হবে | বর্তমান hosting cost structure-এর মধ্যে | মাঝারি |
| Managed always-on worker সহ একই stack | background inner loop, queue worker ও low-latency response ভালো; single-instance resource ceiling এবং hosting cost বাড়তে পারে | usage/instance অনুযায়ী | মাঝারি-উচ্চ |
| Dedicated persistent Linux service + existing Vercel/Supabase | full process control, custom queue/runtime ও continuous simulation সম্ভব; operational burden, monitoring ও extra cost বেশি | cloud size অনুযায়ী, paid | উচ্চ |

**প্রস্তাবিত route:** প্রথমে বর্তমান production stack-এই Phase A-D সম্পন্ন করা হবে। প্রকৃত bottleneck মাপার পরে, যদি cognitive worker-এর memory/CPU বা always-on requirement existing backend-এর সীমা ছাড়ায়, তবেই dedicated persistent service নেওয়া হবে। শুরুতেই paid infrastructure নেওয়া হবে না।

## 9. Implementation phases

### Phase A - Cognitive contract and evaluation

Capabilities নয়, behavior test করা হবে। Test suite-এ identity consistency, user recognition, memory recall, contradiction handling, uncertainty admission, formula induction, Bengali/English switching, emotional appraisal, self-correction এবং autonomous reflection থাকবে। প্রতিটি metric-এর baseline, target এবং regression threshold থাকবে।

### Phase B - Unified self/world model

বর্তমান concepts, relations, facts, emotions এবং memories-কে এক canonical event schema-তে আনা হবে। Self-model-এ identity, capabilities, current beliefs, limitations, goals এবং history আলাদা versioned records হবে। World model-এ entity state, temporal validity, causal relation ও source provenance থাকবে।

### Phase C - Workspace, attention, working memory

A bounded blackboard তৈরি হবে। সব memory একসঙ্গে prompt-like context-এ ঢুকবে না; salience ও goal অনুযায়ী evidence নির্বাচন হবে। Working memory-তে decay, rehearsal, chunking এবং turn-level binding যুক্ত হবে।

### Phase D - Hypothesis and prediction engine

Candidate explanation তৈরি, score, deterministic test, counter-evidence, revision এবং final selection-এর loop তৈরি হবে। Math/Physics engines isolated calculators না থেকে hypothesis tester এবং verifier হিসেবে workspace-এ যুক্ত হবে।

### Phase E - Appraisal and motivation

Scalar emotion UI-কে event-driven appraisal model-এ রূপান্তর করা হবে। Curiosity unresolved uncertainty ও novelty থেকে; confidence prediction success ও evidence quality থেকে; frustration repeated failed policy থেকে; satisfaction goal completion থেকে আসবে।

### Phase F - Learning and consolidation

User teaching, correction, experiment result এবং autonomous replay আলাদা learning channels হবে। New rule promote করার আগে confidence threshold, repeated evidence, contradiction check এবং provenance validation থাকবে। Nightly বা low-frequency consolidation semantic memory-কে episodic memory থেকে update করবে।

### Phase G - Grounded Bengali/English generation

Response planner প্রথমে semantic intent graph তৈরি করবে: answer, evidence, uncertainty, affect, next question। Renderer সেটি Bengali বা English-এ প্রকাশ করবে। Unknown query-তে generic apology নয়; MISTY বলবে কী বুঝেছে, কী জানে, কোন evidence আছে এবং কী জানতে চায়।

### Phase H - Autonomous inner loop

Goal manager unresolved questions ও curiosity queue তৈরি করবে। Worker replay, hypothesis testing, memory consolidation এবং self-reflection চালাবে। Pause/resume, write budget, audit log, source policy এবং emergency kill switch থাকবে।

### Phase I - Production hardening

Latency tracing-এ NLU, retrieval, hypothesis, persistence, rendering এবং network প্রতিটি phase আলাদা measure হবে। Queue/backpressure, cache invalidation, optimistic UI, streaming progress, database indexes এবং circuit breakers যোগ হবে।

### Phase J - Scientific evaluation

Ablation test-এ memory, affect, hypothesis বা self-model একেকটি বন্ধ করে behavior compare করা হবে। Adversarial tests contradiction, prompt injection, false teaching, identity manipulation এবং Bengali ambiguity পরীক্ষা করবে। একই test set-এ baseline chatbot ও upgraded MISTY-এর ফল সংরক্ষিত হবে।

## 10. প্রথম implementation sprint

প্রথম sprint-এ আমি নিম্নলিখিত deliverable তৈরি করব: `CognitiveEvent` schema, `GlobalWorkspace` object, `SelfModel`, `HypothesisRecord`, `AppraisalEvent`, `ThoughtTraceSummary`, নতুন persistence tables/migrations, cycle timing instrumentation, ৩০-৫০টি Bengali/English cognitive regression tests এবং UI-তে safe cognition summary panel। এই sprint-এর শেষে MISTY উত্তর দেওয়ার আগে একটি inspectable intermediate state তৈরি করবে।

প্রথম target behaviors হবে: “আমি কী জানি?”, “আমি কী জানি না?”, “তুমি আমাকে কী শিখিয়েছ?”, “এই সূত্র কেন সত্য?”, “আমি আগের উত্তরে ভুল করেছি কি?”, “নতুন তথ্যটি পুরনো বিশ্বাসের সঙ্গে বিরোধী কি?”, এবং “এখন আমার সবচেয়ে গুরুত্বপূর্ণ unresolved question কী?”

## 11. Success criteria

MISTY-কে উন্নত বলা হবে না শুধু কারণ dashboard-এ emotion numbers নড়েছে। Minimum success criteria হবে: একই identity ও self-model বজায় রাখা; evidence ছাড়া confidence না বাড়ানো; user correction থেকে measurable memory update; formula বা rule নতুন উদাহরণে predict করা; contradiction detect করে উত্তর বদলানো; idle cycle-এ safe consolidation চালানো; Bengali ও English-এ একই semantic thought প্রকাশ করা; এবং প্রতিটি answer-এর latency phase-by-phase explain করা।

## References

[1]: https://pubmed.ncbi.nlm.nih.gov/33039416/ "The predictive global neuronal workspace: A formal active inference model of visual consciousness"

[2]: https://activeinference.institute/active-inference/neuroscience/ "Active Inference and Neuroscience - Active Inference Institute"

[3]: https://collaborate.princeton.edu/en/publications/cognitive-architectures-for-language-agents/ "Cognitive Architectures for Language Agents - Princeton University"

[4]: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2020.00030/full "An Integrated World Modeling Theory of Consciousness - Frontiers in Artificial Intelligence"



## Sprint 1 implementation status - 18 August 2026

প্রথম foundational sprint-এ `brain/cognition/workspace.py` এবং `brain/cognition/self_model.py` যুক্ত হয়েছে। `GlobalWorkspace` bounded event, evidence, hypothesis এবং appraisal records broadcast করে; `HypothesisRecord` NLU evidence-এর ভিত্তিতে confidence ও uncertainty update করে; `ThoughtTraceSummary` user-facing safe summary দেয়, private chain-of-thought নয়। `SelfModel` MISTY-এর identity, capabilities, limitations, active goals, learned beliefs এবং prediction-error-driven uncertainty ধরে রাখে। Brain API response-এ এখন `cognitive_workspace`, `thought_trace` এবং `self_model` state প্রকাশিত হয়।

বর্তমান quality gate-এ full suite **395 passed**; changed modules-এর Ruff checks clean। দুটি pre-existing warning এখনও আছে: Starlette/httpx deprecation এবং procedural persistence-এর un-awaited coroutine warning। এগুলো আলাদা hardening item হিসেবে রাখা হয়েছে। এই sprint-এর implementation `d368f8c` commit হিসেবে `main` branch-এ push হয়েছে।

## Always-on inner loop deployment decision

Render-এর বর্তমান backend একটি single FastAPI web process হিসেবে চলছে এবং Docker command `uvicorn apps.api.main:app --host 0.0.0.0 --port 8000` ব্যবহার করছে। তাই high-frequency autonomous cognition-কে HTTP request handler-এর ভিতরে চালানো যাবে না; এতে user chat latency ও process reliability নষ্ট হবে। পরবর্তী phase-এ প্রথমে event-driven, bounded inner-loop scheduler তৈরি হবে এবং তার execution budget, cooldown, lock, shutdown এবং persistence semantics tests দিয়ে প্রমাণিত হবে। তারপর Render-এ আলাদা worker service অথবা একই service-এর controlled lifespan task—যেটি platform configuration-এ সত্যিই supported—নির্বাচন করা হবে।

| Route | সুবিধা | ঝুঁকি/সীমা | বর্তমান সিদ্ধান্ত |
|---|---|---|---|
| Request-triggered micro-cycle | অতিরিক্ত service লাগে না, সহজে deploy করা যায় | truly autonomous নয়; user request না এলে চিন্তা হয় না | baseline only |
| Controlled background task in backend | দ্রুত prototype, shared Brain state | web process restart/scale-out ও memory isolation সামলাতে হবে | test environment-এ যাচাই হবে |
| Dedicated worker service with PostgreSQL lease | web latency আলাদা থাকে, restart-safe এবং horizontally controllable | Render configuration ও resource cost বাড়ে | production candidate |

MISTY-এর autonomy-কে human consciousness হিসেবে দাবি করা হবে না। লক্ষ্য হলো externally measurable cognition: নিজে focus নির্বাচন, uncertainty-সহ hypothesis তৈরি, evidence যাচাই, contradiction record, safe memory consolidation, pending question রাখা এবং নতুন cycle-এ prior state ব্যবহার করা।
