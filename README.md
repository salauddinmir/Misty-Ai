# MISTY - Artificial Cognitive System

MISTY is an experimental artificial cognitive system built **without any LLM dependency**. It combines a rule-based natural language understanding layer, a knowledge graph, working/episodic/semantic/procedural memory systems, an emotion engine, reinforcement learning, and a cognitive cycle (Observe → Interpret → Recall → Associate → Reason → Plan → Act → Evaluate → Learn → Consolidate).

> Note: Phase 1 neural simulation research (vectorized LIF populations, spiking encoding, brain regions) lives on the `phase-1-neural-core` branch. It is a research branch and has not yet been merged into `main`.

## Features

- **Bilingual NLU (Bengali + English)** — intent parsing via rule-based pattern matching
- **Knowledge graph** — NetworkX-backed concepts and typed relations with activation
- **4 memory systems** — working, episodic, semantic, procedural
- **Cognitive cycle** — full observe→learn loop with reward feedback
- **Emotion engine** — curiosity, confidence, frustration, satisfaction, etc.
- **REST API + WebSocket** — FastAPI with a streaming brain-activity endpoint
- **SQLite persistence** — concepts and relations survive server restarts

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
cd web
npm install
npm run dev   # http://localhost:3000
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send a message; the brain runs a full cognitive cycle |
| `/api/brain/*` | GET | Inspect concepts, memories, and brain state |
| `/ws/brain/activity` | WS | Real-time brain activity stream |
| `/health` | GET | Health check |

Example:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "আমার নাম Salauddin"}'
```

## Architecture

```
User Input
  |  rule-based NLU (Bengali/English)
  v
Cognitive Cycle: OBSERVE -> INTERPRET -> RECALL -> ASSOCIATE ->
                 REASON -> PLAN -> ACT -> EVALUATE -> LEARN -> CONSOLIDATE
  |
  +-- Knowledge Graph (concepts + relations, activation spreading)
  +-- Memory: working / episodic / semantic / procedural
  +-- Emotion Engine + Reinforcement Learner (Q-table)
  +-- SQLite persistence (concepts, relations, episodes, states)
  |
  v
Response + metadata (confidence, emotional state, processing time)
```

## Project Status

| Component | Status |
|-----------|--------|
| Cognitive cycle core | Implemented |
| Bengali/English NLU | Implemented (rule-based) |
| Knowledge graph + relations | Implemented + persisted |
| 4 memory systems | Implemented; boot-restore from SQLite |
| Emotion + RL | Basic implementation |
| Planner / reflection / consolidation | Basic implementation |
| Neural simulation (SNN) | Research branch `phase-1-neural-core` |
| Vision / audio / speech / hardware | Planned (see `docs/phase-plan.md`) |

## License

See `LICENSE` for details.
