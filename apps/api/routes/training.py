"""
Phase 36: authorized web-learning API route.

POST /api/training/web_learn
    Request: {"topics": [...], "topic_weights": {"topic": weight}}
    Response: batch learning report (learned / quarantined / skipped /
    cross_topic_conflicts) produced by
    brain.learning.web_learning.WebSearchLearner.ingest_batch.

Security:
- MISTY_TRAINING_API_KEY env gate: the request must carry the same key in
  the X-Misty-Training-Key header. No header / wrong key -> 401.
- Key must be non-empty (empty-string keys are refused at boot, printed as
  a warning) so a misconfigured deployment can never open an unrestricted
  route.
- Rate limiting: in-memory sliding window keyed by (route, client ip).
  Defaults: 10 requests per 60 seconds; MISTY_TRAINING_RATE_LIMIT and
  MISTY_TRAINING_RATE_WINDOW override.

The route is deliberately NOT added to any open CORS path: it is a
backend-administration endpoint and never called from the Vercel frontend.
"""

import os
import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/training")

# ---------------------------------------------------------------------------
# API-key gate
# ---------------------------------------------------------------------------
_TRAINING_KEY: str | None = os.getenv("MISTY_TRAINING_API_KEY", "").strip() or None

if _TRAINING_KEY is None:
    print(
        "WARNING: MISTY_TRAINING_API_KEY is not set — the "
        "/api/training/web_learn endpoint will refuse all requests "
        "(no valid key exists)."
    )

# ---------------------------------------------------------------------------
# In-memory rate limiting (sliding window per client)
# ---------------------------------------------------------------------------
_RATE_LIMIT: int = max(1, int(os.getenv("MISTY_TRAINING_RATE_LIMIT", "10")))
_RATE_WINDOW: float = max(1.0, float(os.getenv("MISTY_TRAINING_RATE_WINDOW", "60")))

_rate_windows: dict[str, deque[float]] = defaultdict(deque)


def _client_id(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip().split(":")[0].strip()
    peer = request.client
    return peer.host if peer else "unknown"


def _is_rate_limited(request: Request) -> bool:
    now = time.time()
    window = _rate_windows[_client_id(request)]
    cutoff = now - _RATE_WINDOW
    while window and window[0] <= cutoff:
        window.popleft()
    if len(window) >= _RATE_LIMIT:
        return True
    window.append(now)
    return False


# ---------------------------------------------------------------------------
# Web-learning endpoint
# ---------------------------------------------------------------------------
def _extract_topics(body: dict | None) -> list[str]:
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="body must be a JSON object")
    topics = body.get("topics")
    if not isinstance(topics, list) or not topics:
        raise HTTPException(status_code=400, detail="`topics` must be a non-empty list of strings")
    if not all(isinstance(t, str) and t.strip() for t in topics):
        raise HTTPException(status_code=400, detail="every topic must be a non-empty string")
    return [t.strip() for t in topics]


@router.post("/web_learn")
async def web_learn(request: Request) -> JSONResponse:
    """Authorized batch web-learning ingestion.

    Teaches Misty a batch of topics from deterministic search-backed
    ingestion, guarded by the training API key and rate limits.
    """
    if _TRAINING_KEY is None:
        raise HTTPException(status_code=401, detail="training API not configured on this deployment")
    header_key = request.headers.get("X-Misty-Training-Key", "")
    if not header_key or not header_key.strip():
        raise HTTPException(status_code=401, detail="missing X-Misty-Training-Key header")
    if not _keys_match(header_key.strip(), _TRAINING_KEY):
        raise HTTPException(status_code=401, detail="invalid training API key")
    if _is_rate_limited(request):
        raise HTTPException(
            status_code=429,
            detail=f"rate limit exceeded: {_RATE_LIMIT} requests per {_RATE_WINDOW:.0f}s",
        )

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON body") from None

    topics = _extract_topics(body)
    weights = body.get("topic_weights") if isinstance(body, dict) else None
    if weights is not None and not isinstance(weights, dict):
        raise HTTPException(status_code=400, detail="`topic_weights` must be an object of topic->number")
    weights = {k: float(v) for k, v in weights.items()} if weights else {}

    brain = _get_brain(request)
    if brain is None:
        raise HTTPException(status_code=503, detail="brain not ready")

    report = await brain.web_learner.ingest_batch(topics, topic_weights=weights or None)
    return JSONResponse(
        status_code=200,
        content={
            "status": "completed",
            "topics_requested": topics,
            **report,
        },
    )


def _keys_match(provided: str, expected: str) -> bool:
    """Constant-ish comparison to avoid trivial timing leakage."""
    if len(provided) != len(expected):
        return False
    return all(a == b for a, b in zip(provided, expected, strict=True))


def _get_brain(request: Request):
    """Resolve the Brain instance: route dependency injection first, then
    FastAPI app state (populated by the lifespan in apps/api/main.py)."""
    brain = getattr(request.app.state, "brain", None)
    if brain is None and hasattr(request, "brain"):
        brain = request.brain  # type: ignore[attr-defined]
    return brain


# ---------------------------------------------------------------------------
# Self-assessment-driven learning roadmap (Phase 39)
# ---------------------------------------------------------------------------
@router.get("/roadmap")
async def get_roadmap(request: Request) -> JSONResponse:
    """Return the latest self-assessment-driven learning roadmap.

    The roadmap is produced by the learning planner from the gap assessor's
    last self-assessment report. Read-only: no training key is required
    because no ingestion happens here. Returns
    {"learning_roadmap": {...}} — or an empty dict if no plan exists yet.
    """
    brain = _get_brain(request)
    if brain is None:
        raise HTTPException(status_code=503, detail="brain not ready")

    state = brain.get_state()
    roadmap = state.get("learning_roadmap")
    return JSONResponse(status_code=200, content={"learning_roadmap": roadmap or {}})


@router.post("/roadmap")
async def run_roadmap(request: Request) -> JSONResponse:
    """Trigger a gap-based planning cycle and ingest the planned topics.

    Body (all optional):
    - max_topics (int, default 5): how many topics the planner may pick.
    - boost_topics (list[str]): topic names promoted to the front of the
      plan before gap scoring ranks the rest.

    Security: same MISTY_TRAINING_API_KEY gate and rate limit as
    /api/training/web_learn — planning triggers real web ingestion, so it
    is treated as a write operation.
    """
    if _TRAINING_KEY is None:
        raise HTTPException(status_code=401, detail="training API not configured on this deployment")
    header_key = request.headers.get("X-Misty-Training-Key", "")
    if not header_key or not header_key.strip():
        raise HTTPException(status_code=401, detail="missing X-Misty-Training-Key header")
    if not _keys_match(header_key.strip(), _TRAINING_KEY):
        raise HTTPException(status_code=401, detail="invalid training API key")
    if _is_rate_limited(request):
        raise HTTPException(
            status_code=429,
            detail=f"rate limit exceeded: {_RATE_LIMIT} requests per {_RATE_WINDOW:.0f}s",
        )

    brain = _get_brain(request)
    if brain is None:
        raise HTTPException(status_code=503, detail="brain not ready")

    try:
        body = await request.json()
    except Exception:
        body = None

    kwargs: dict = {}
    if isinstance(body, dict):
        max_topics = body.get("max_topics")
        if max_topics is not None:
            if not isinstance(max_topics, int) or not (1 <= max_topics <= 20):
                raise HTTPException(status_code=400, detail="`max_topics` must be an int between 1 and 20")
            kwargs["max_topics"] = max_topics
        boost_topics = body.get("boost_topics")
        if boost_topics is not None:
            if not isinstance(boost_topics, list) or not all(isinstance(t, str) and t.strip() for t in boost_topics):
                raise HTTPException(status_code=400, detail="`boost_topics` must be a list of non-empty strings")
            kwargs["boost_topics"] = tuple(t.strip() for t in boost_topics)

    result = await brain.run_learning_roadmap(**kwargs)
    return JSONResponse(status_code=200, content=result)
