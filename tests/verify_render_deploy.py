"""Verify the new Render deployment serves Phase-14 metrics.

Render deploys automatically from the main branch; cold starts take ~1-2 min.
Once the new build is live, POST /api/chat warms the app and the autonomous
worker interval (300s default) eventually runs a tick. This script warms the
app, then repeatedly polls /api/brain/state until last_autonomous_tick carries
Phase-14 metrics (tick_index, evidence_budget, ...) or a timeout is reached.
"""

import sys
import time

import requests

BASE = "https://misty-brain.onrender.com"


def warm() -> None:
    requests.post(f"{BASE}/api/chat", json={"message": "স্বাগতম", "language": "bn"}, timeout=120)


def state() -> dict:
    resp = requests.get(f"{BASE}/api/brain/state", timeout=60)
    return resp.json() if resp.status_code == 200 else {"error": resp.status_code}


def metrics_present(payload: dict) -> bool:
    tick = payload.get("last_autonomous_tick")
    if not isinstance(tick, dict):
        return False
    return all(k in tick for k in ("tick_index", "evidence_budget", "elapsed_ms", "outcome"))


def main() -> int:
    print("Warming the app...")
    warm()
    deadline = time.monotonic() + 600  # allow up to 10 min for build + worker tick
    while time.monotonic() < deadline:
        payload = state()
        if metrics_present(payload):
            print("NEW DEPLOYMENT LIVE: Phase-14 tick metrics present.")
            print("last_autonomous_tick =", payload["last_autonomous_tick"])
            return 0
        print(f"  polling... last_autonomous_tick={payload.get('last_autonomous_tick')}")
        time.sleep(20)
        warm()  # keep the app awake and let ticks fire
    print("TIMEOUT: new deployment not verified within 10 minutes.")
    print("It may still be building on Render; re-run this script later.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
