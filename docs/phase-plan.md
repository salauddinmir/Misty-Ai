# MISTY — Phase-wise Development Plan

This document summarizes the current audit state and lays out the remaining work
phase by phase. It aligns with the 10-phase development sequence defined in the
project vision: Brain → Vision → Audio → Association/Learning → World Model →
Goals/Planning → Speech → Virtual Body → Hardware Sensors → Physical Robot.

## 0. Current State (Audit Summary — Aug 2026)

| Area | Status |
|------|--------|
| Cognitive cycle (10 phases) | Implemented, tested end-to-end |
| Bengali + English NLU | Rule-based parser; interrogative-guard bug fixed |
| Knowledge graph (NetworkX) | Implemented; relations now persisted |
| 4 memory systems | Implemented; boot-restore from SQLite added |
| Emotion + reinforcement learner | Basic Q-table over intents |
| Neural simulation (SNN research) | Complete on `phase-1-neural-core` branch; **not merged to main** |
| REST API + WebSocket + frontend | Working; 85 tests passing |
| Vision / audio / speech / tools / hardware | Not implemented |

Fixed in this audit pass: NLU interrogative bug ("আমার নাম কি?" no longer captured as a name),
contextual unknown-input fallback, episodic memory wiring in the LEARN phase, relation
persistence, and boot-time knowledge restore so learned knowledge survives restarts.

## Phase 1 — Brain Hardening & Neural Merge (now)

1. **Merge `phase-1-neural-core` into `main`** behind the `use_neural_sim` flag,
   then write tests exercising the neural runtime (population dynamics, encoding,
   inhibition regions).
2. **Hybrid mode**: route high-confidence NLU intents through the knowledge graph
   while ambiguous inputs fall through to the spiking simulator for pattern match.
3. **Consolidation ↔ DB**: make `brain/learning/consolidation.py` flush important
   episodes to SQLite on a timer (batch writes, not per-cycle).
4. **Procedural memory retrieval**: wire `brain/memory/procedural.py` into REASON so
   stored if-then procedures actually influence answers.
5. CI: GitHub Actions workflow (`pytest` + lint) on every push.

## Phase 2 — Vision (সংবেদন ইনপুট)

1. Camera/capture module (`brain/sensory/vision.py`): frame grab via OpenCV.
2. Vector encoder (CNN or pretrained ViT via torch; or ONNX for no-LLM edge).
3. `VisualConcept` nodes in the knowledge graph (grounded concepts: person, object, scene).
4. Vision→language bridging: bind visual features to existing concept names
   (e.g., a detected face activates the "Salauddin" concept).

## Phase 3 — Audio (শ্রবণ ও ভাষা)

1. Microphone capture + VAD (`brain/sensory/audio.py`).
2. Speech-to-text (Whisper-small / faster-whisper locally).
3. Audio events as episodic memories with valence (tone analysis via basic MFCC features).

## Phase 4 — Association & Learning Depth

1. Hebbian weight updates on co-activated concepts (strengthen edges that fire together).
2. Recency/frequency/emotional-weighted recall scoring in `brain/graph/activation.py`.
3. Curiosity-driven exploration: low-activation concept search prompts questions.

## Phase 5 — World Model

1. Structured state representation: entities, locations, time, causal links.
2. Prediction module: after each cycle, predict next likely user intent and compare
   (prediction error feeds the learner).
3. Counterfactual scratchpad for "what-if" queries.

## Phase 6 — Goals & Planning

1. Hierarchical goal decomposition (planner/ already scaffolded).
2. Multi-step tool-use plans: e.g., "find info → ask → save".
3. Progress tracking + goal pruning in LEARN/CONSOLIDATE.

## Phase 7 — Speech (বাচন)

1. TTS (offline, e.g., Piper) for Bengali + English responses.
2. Voice conversation loop: STT → brain → TTS (full duplex via WebSocket).

## Phase 8 — Virtual Body

1. Embodied avatar in the web frontend: expressions driven by `emotional_state`.
2. Animation states: thinking, surprised, happy, confused — mapped to emotion values.

## Phase 9 — Hardware Sensors

1. Raspberry Pi agent: GPIO sensors (motion, sound, light) → brain events.
2. Low-bandwidth event channel to the core brain over MQTT/WebSocket.

## Phase 10 — Physical Robot

1. Motor control (wheels/arms) driven by planner actions.
2. Safety layer: emergency stop, distance bounds.
3. Integration test: perception → cognition → action loop at >2 Hz.

## Milestones & Success Criteria

| Milestone | Criteria |
|-----------|----------|
| M1 (Phase 1 done) | Neural sim merged; 100+ tests; CI green; consolidation persists to DB |
| M2 (Phase 2–3) | Brain reacts to a live camera frame and a spoken Bengali sentence |
| M3 (Phase 4–6) | Learned associations measurably change recall ordering; multi-step plans execute |
| M4 (Phase 7–8) | Full voice conversation; avatar mirrors emotion state |
| M5 (Phase 9–10) | Sensor events reach brain <500 ms; robot completes a simple instructed task |
