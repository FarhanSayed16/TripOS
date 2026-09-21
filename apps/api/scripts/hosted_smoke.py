#!/usr/bin/env python3
"""
Hosted smoke runner (Sprint P / FIX-P27-01).

Usage:
  set TRIPOS_API_URL=https://your-api.onrender.com
  set TRIPOS_WEB_URL=https://your-app.vercel.app   # optional
  python scripts/hosted_smoke.py

Exit 0 only if required checks pass. Record results in docs/ops/HOSTED_SMOKE.md.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _get(url: str, timeout: float = 20.0) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


def main() -> int:
    api = (os.getenv("TRIPOS_API_URL") or "").rstrip("/")
    web = (os.getenv("TRIPOS_WEB_URL") or "").rstrip("/")
    if not api:
        print("FAIL: set TRIPOS_API_URL (e.g. https://tripos-api.onrender.com)")
        print("Hosted smoke is blocked until Render/Vercel URLs exist (see docs/ops/HOSTED_SMOKE.md).")
        return 2

    rows: list[tuple[str, bool, str]] = []

    code, body = _get(f"{api}/health")
    ok = code == 200
    rows.append(("API /health", ok, f"{code} {body[:120]}"))

    code, body = _get(f"{api}/ready")
    ready_ok = code == 200
    try:
        payload = json.loads(body) if body.strip().startswith("{") else {}
    except json.JSONDecodeError:
        payload = {}
    if ready_ok and isinstance(payload, dict):
        # Accept either explicit db flag or 200-only ready endpoints
        db_flag = payload.get("database") or payload.get("db")
        if db_flag is not None and str(db_flag).lower() in ("false", "down", "error"):
            ready_ok = False
    rows.append(("API /ready", ready_ok, f"{code} {body[:160]}"))

    if web:
        code, body = _get(web)
        rows.append(("Web home", code == 200, f"{code}"))
    else:
        rows.append(("Web home", False, "TRIPOS_WEB_URL not set — skip"))

    print("TripOS hosted smoke")
    print(f"API={api}")
    if web:
        print(f"WEB={web}")
    print("-" * 60)
    failed = 0
    for name, ok, detail in rows:
        mark = "PASS" if ok else "FAIL"
        if not ok and name != "Web home":
            failed += 1
        elif not ok and name == "Web home" and web:
            failed += 1
        print(f"[{mark}] {name}: {detail}")

    print("-" * 60)
    if failed:
        print(f"RESULT: {failed} required check(s) failed")
        return 1
    print("RESULT: required checks passed — tick docs/ops/HOSTED_SMOKE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
