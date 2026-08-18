# Phase 23+ Master Plan — Research Notes (গ্যাপ অ্যানালাইসিস)

## বর্তমান যা আছে (verified code)
- Brain core: process(), _run_cycle (observe→interpret→recall→associate→reason→plan→act→evaluate→learn→consolidate), 20+ IntentType.
- DialogueContext (brain/dialogue/context.py): max_history টার্ন, salient_entities, topic, coreference resolution (_resolve_coreference), last_user_turn, to_dict। প্রসঙ্গ-টপিক ক্যারি আছে — কিন্তু ACT লেভেলে (হ্যান্ডলারে) topic/previous-turn awareness ব্যবহার শুধু কিছু জায়গায় (QUERY_WHO coreference)।
- EpisodicMemory: store(recall_recent, recall_by_context, recall_by_content), valence-tagged, max 1000. WorkingMemory আছে।
- InferenceSynthesizer: synthesize() → derived answers w/ confidence; commonsense layer 187+ facts.
- WebSearchLearner: search(topic), ingest(topic, max_facts) → WebLearningResult (facts_learned, decisions). Agent-side, safety-gated.
- TrainingPackageV2 registry: concepts, relations, facts, rules, formulas, examples, tests + confidence_policy; PostgreSQL persistence (training_packages).
- 10 department manifests: language, mathematics, physics, literature + reasoning, commonsense, memory, perception, emotion_simulation, self_model_and_planning.
- Benchmark generator + BilingualBenchmark runner exists; benchmark test suite Phase 13.
- AutonomousInnerLoop worker + autonomous_reflection_tick (hypothesis loops, evidence budgets, consolidation budgets).
- 531 tests passing, production smoke PASS, Render+Vercel deployed, Supabase Postgres.

## গ্যাপ (Plan এ ধরতে হবে)
1. Conversation: (a) topic-aware replies — _act_conversation/_act_query handlers DialogueContext.topic ক্যারি করে না (এখনো mostly stateless per-handler); (b) no personality/voice consistency across turns; (c) no dialogue-act generation (follow-up question, topic change, humor, storytelling); (d) Bengali reply style fixed — no variation/persona.
2. Training completeness: physics engine limited (kinematics basic); literature package thin; no conversation corpus package; no question-answering benchmark coverage report in prod; autonomous tick learns but doesn't create new training packages.
3. Web-learning training: ingest() exists but (a) no batch mode; (b) no topic list curation from web; (c) nothing triggers web-learning at runtime or via /api route; (d) learned facts don't auto-feed benchmark re-run; (e) no "learning report" route.
4. Conversation corpus → TrainingPackageV2 format (concepts/facts/rules/examples/tests) is exactly what's needed; conversation_corpus training package = new department "conversation".

## Plan structure (user-requested)
- Part 1: Human-like conversation capability plan (6-7 phases)
- Part 2: Phase-wise complete training curriculum
- Part 3: Web-search learning + training it
- Each phase: goal, deliverables, test criteria, dependency, estimate
- Final: sequencing + approval checkpoint
