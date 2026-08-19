# MISTY — Hybrid Cognitive Research System

MISTY is an **LLM-independent hybrid symbolic/neural cognitive research system**. Its default runtime is deterministic and symbolic: rule-based Bengali/English language parsing, a knowledge graph, working/episodic/semantic/procedural memory, bounded cognitive-workspace records, goals, affective state signals, and an inspectable Observe → Interpret → Recall → Associate → Reason → Plan → Act → Evaluate → Learn → Consolidate cycle.

An optional spiking-neural simulation can contribute association activity when `Brain(use_neural_sim=True)` is selected. It is **off by default** in the API and is an experimental simulation path, not a claim of biological equivalence, consciousness, or human-level cognition.

## Features

- **Bengali + English NLU** — deterministic intent and entity parsing
- **Knowledge graph** — NetworkX-backed concepts, typed relations, and spreading activation
- **Four memory models** — working, episodic, semantic, and procedural
- **Causal cognitive cycle** — recalled evidence and reasoning feed planning and action metadata
- **Inspectable grounding** — response provenance, workspace evidence, self-model summary, and phase timings
- **Deterministic math and physics engines** — bounded supported problem formats
- **Optional neural simulation** — vectorized LIF populations and experimental neural association, default-off
- **FastAPI + Next.js** — JSON/SSE chat APIs and a cognitive-trace frontend
- **Persistence** — concepts, relations, semantic-fact episodes, procedures, and brain-state snapshots
- **Prototype interfaces** — media feature extraction, voice, sensors, and safety-gated actuator bridges

## Quick Start

```bash
# 1. Clone and install dependencies
git clone https://github.com/salauddinmir/Misty-Ai.git
cd Misty-Ai
pip install -r requirements.txt

# 2. Run tests
PYTHONPATH=. pytest tests/

# 3. Start the API server (port 8000)
PYTHONPATH=. uvicorn apps.api.main:app --reload

# 4. Start the frontend (in another terminal)
cd apps/web
npm ci
npm run dev   # http://localhost:3000
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/chat` | POST | Run a text input through the cognitive cycle and return response/trace metadata |
| `/api/chat/stream` | POST | Stream cognitive status and response text |
| `/api/chat/media` | POST | Prototype image/audio feature-extraction gateway; it does not perform general visual or speech understanding |
| `/api/brain/*` | GET | Inspect concepts, memories, and brain state |
| `/api/sensors/*` | various | Transport-neutral sensor prototype APIs |
| `/api/actuators/*` | various | Safety-gated actuator bridge APIs; dry-run is the intended research default |
| `/ws/brain/activity` | WS | Brain-activity event stream |
| `/health` | GET | Runtime readiness status |

Example:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "আমার নাম Salauddin"}'
```

## Architecture

```text
Input
  │
  ├─ deterministic Bengali/English NLU
  ▼
OBSERVE → INTERPRET → RECALL → ASSOCIATE → REASON
        → PLAN → ACT → EVALUATE → LEARN → CONSOLIDATE
  │
  ├─ cognitive workspace and provenance-carrying evidence
  ├─ knowledge graph and memory systems
  ├─ goals, world model, appraisal, reflection, and deterministic engines
  └─ optional/default-off spiking-neural association simulation
  ▼
Response + confidence + grounding + safe trace metadata
```

The project is a research platform for testing explicit cognitive mechanisms. Progress should be evaluated through reproducible behavior, provenance, uncertainty calibration, persistence, safety, and symbolic-vs-neural ablations—not anthropomorphic or human-level claims.

## Project Status

| Component | Status |
|---|---|
| Cognitive cycle core | Implemented; actively being integrated and validated |
| Bengali/English NLU | Implemented (rule-based, bounded coverage) |
| Knowledge graph + relations | Implemented with persistence |
| Memory models | Implemented; persistence coverage varies by memory type |
| Emotion/appraisal and reinforcement learning | Basic computational state models |
| Planning, reflection, consolidation | Basic research implementations |
| Neural simulation (SNN) | Merged, experimental, optional, default-off |
| Image/audio/voice/sensor/hardware | Prototype interfaces, not general perception or human-equivalent control |
