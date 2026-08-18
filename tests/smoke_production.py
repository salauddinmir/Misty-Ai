"""Phase 15: production smoke tests against the Render backend.

Run with: python3 tests/smoke_production.py
Verifies: POST /api/chat (BN + EN), GET /api/training/catalog,
GET /api/brain/state (must include last_autonomous_tick metrics).
"""

import json
import sys
import time

import requests

BASE = "https://misty-brain.onrender.com"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    if not ok:
        FAILURES.append(name)


def main() -> int:
    # 1. JSON chat, Bengali
    start = time.monotonic()
    resp = requests.post(
        f"{BASE}/api/chat",
        json={"message": "তুমি কে?", "language": "bn"},
        timeout=120,
    )
    took = round((time.monotonic() - start) * 1000)
    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    text = (data.get("response") or data.get("reply") or str(data))[:160]
    check("chat_bn", resp.status_code == 200 and len(data) > 0, f"{resp.status_code} ({took}ms) body starts: {text!r}")
    if "thought_trace" in data:
        print("      thought_trace present in BN response")

    # 2. JSON chat, English
    start = time.monotonic()
    resp2 = requests.post(
        f"{BASE}/api/chat",
        json={"message": "Who are you? What are you capable of?", "language": "en"},
        timeout=120,
    )
    took2 = round((time.monotonic() - start) * 1000)
    data2 = resp2.json() if resp2.headers.get("content-type", "").startswith("application/json") else {}
    text2 = (data2.get("response") or data2.get("reply") or str(data2))[:160]
    check("chat_en", resp2.status_code == 200 and len(data2) > 0, f"{resp2.status_code} ({took2}ms) body starts: {text2!r}")

    # 3. SSE streaming
    resp3 = requests.post(
        f"{BASE}/api/chat/stream",
        json={"message": "2+2=?", "language": "en"},
        timeout=120,
    )
    stream_ok = resp3.status_code == 200 and "event" in (resp3.headers.get("content-type") or "")
    body = resp3.text
    done_present = "event: done" in body and '"status": "thinking"' in body
    tokens_present = "event: token" in body
    check(
        "chat_stream",
        stream_ok and done_present and tokens_present,
        f"{resp3.status_code} content-type={resp3.headers.get('content-type')}; events=thinking+token+done={done_present and tokens_present}",
    )

    # 4. Training catalog
    resp4 = requests.get(f"{BASE}/api/training/catalog", timeout=60)
    data4 = resp4.json() if resp4.status_code == 200 else {}
    check("training_catalog", resp4.status_code == 200 and isinstance(data4.get("packages"), list), f"{resp4.status_code} packages={len(data4.get('packages', []))}")

    # 5. Brain state with Phase-14 tick metrics
    resp5 = requests.get(f"{BASE}/api/brain/state", timeout=60)
    data5 = resp5.json() if resp5.status_code == 200 else {}
    # Walk one level deep: the top-level keys may wrap the brain snapshot.
    candidates = [data5.get("last_autonomous_tick") or {}]
    for _value in data5.values():
        if isinstance(_value, dict) and "last_autonomous_tick" in _value:
            candidates.append(_value["last_autonomous_tick"])
    candidates = [c for c in candidates if c]
    metric_keys = ("tick_index", "evidence_budget", "evidence_count", "elapsed_ms", "outcome")
    results = []
    for tick in candidates:
        results.append([k for k in metric_keys if k not in tick])
    missing = min(results, key=len)
    best_tick = next((c for c in candidates if len([k for k in metric_keys if k not in c]) == len(missing)), {})
    check(
        "brain_state_tick_metrics",
        resp5.status_code == 200 and not missing,
        f"status={resp5.status_code}; top-level keys={sorted(data5.keys())[:12]}; missing keys={missing}; tick={json.dumps(best_tick, ensure_ascii=False)[:300]}",
    )

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL SMOKE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
