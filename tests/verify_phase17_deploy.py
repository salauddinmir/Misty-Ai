"""Verify Phase 17 fixes on the Render production build.

Polls until the deployed build includes the quadratic fix (x² - 4 = 0
→ roots ±2) and the casual-conversation reply for "কি খবর". Render
auto-deploys on git push; builds take a few minutes.
"""

import json
import time

import requests

CHAT_URL = "https://misty-brain.onrender.com/api/chat"
QUADRATIC_QUERY = "x² - 4 = 0, x = ?"
CASUAL_QUERY = "কি খবর"


def probe(query: str, condition) -> tuple[bool, str]:
    for _ in range(45):
        try:
            response = requests.post(CHAT_URL, json={"message": query}, timeout=90).json().get("response", "")
            if condition(response):
                return True, response
        except Exception:
            pass
        time.sleep(20)
    return False, response


if __name__ == "__main__":
    quadratic_ok, quadratic_text = probe(QUADRATIC_QUERY, lambda t: "2" in t and "-2" in t)
    print(f"quadratic: {'OK' if quadratic_ok else 'PENDING/FAIL'} — {quadratic_text[:90]}")

    casual_ok, casual_text = probe(CASUAL_QUERY, lambda t: "আমি" in t and "ধন্যবাদ" in t)
    print(f"casual-bn: {'OK' if casual_ok else 'PENDING/FAIL'} — {casual_text[:90]}")

    if not (quadratic_ok and casual_ok):
        raise SystemExit(1)
    print(json.dumps({"quadratic": quadratic_text, "casual": casual_text}, ensure_ascii=False, indent=2))
