"""In-process supplier latency / error metrics (FC Phase 2)."""
from __future__ import annotations

import statistics
import time
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional

from app.core.circuit_breaker import circuit_breaker


class _Sample:
    __slots__ = ("ts", "duration_ms", "ok")

    def __init__(self, duration_ms: int, ok: bool):
        self.ts = time.time()
        self.duration_ms = int(duration_ms)
        self.ok = bool(ok)


class SupplierMetrics:
    """Rolling window metrics per supplier (process-local; fine for single-instance pilot)."""

    def __init__(self, window_seconds: int = 3600, max_samples: int = 500):
        self.window_seconds = window_seconds
        self.max_samples = max_samples
        self._samples: Dict[str, Deque[_Sample]] = defaultdict(
            lambda: deque(maxlen=max_samples)
        )

    def record(self, supplier_code: str, duration_ms: int, *, ok: bool) -> None:
        self._samples[supplier_code].append(_Sample(duration_ms, ok))

    def _fresh(self, code: str) -> List[_Sample]:
        cutoff = time.time() - self.window_seconds
        return [s for s in self._samples.get(code, []) if s.ts >= cutoff]

    def snapshot(self, supplier_code: str) -> Dict[str, Any]:
        samples = self._fresh(supplier_code)
        durations = [s.duration_ms for s in samples]
        errors = sum(1 for s in samples if not s.ok)
        n = len(samples)
        p50 = p95 = None
        if durations:
            sorted_d = sorted(durations)
            p50 = sorted_d[min(len(sorted_d) - 1, int(0.50 * (len(sorted_d) - 1)))]
            p95 = sorted_d[min(len(sorted_d) - 1, int(0.95 * (len(sorted_d) - 1)))]
        return {
            "supplier_code": supplier_code,
            "window_seconds": self.window_seconds,
            "sample_count": n,
            "error_count": errors,
            "error_rate": round(errors / n, 4) if n else 0.0,
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "latency_avg_ms": int(statistics.mean(durations)) if durations else None,
            "circuit_state": circuit_breaker.state.get(supplier_code, "CLOSED"),
            "circuit_open": circuit_breaker.is_open(supplier_code),
            "circuit_failures": circuit_breaker.failures.get(supplier_code, 0),
            "manual_override": circuit_breaker.manual_override.get(supplier_code, False),
        }

    def all_snapshots(self, codes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        keys = codes or list(
            set(list(self._samples.keys()) + list(circuit_breaker.state.keys()))
        )
        # Always include known adapters if empty
        return [self.snapshot(c) for c in sorted(set(keys))]


supplier_metrics = SupplierMetrics()

# Last search offer counts (process-local) for admin strip
_last_offer_counts: Dict[str, int] = {}
_last_offer_counts_at: float = 0.0


def record_offer_counts(counts: Dict[str, int]) -> None:
    global _last_offer_counts, _last_offer_counts_at
    _last_offer_counts = dict(counts or {})
    _last_offer_counts_at = time.time()


def last_offer_counts() -> Dict[str, Any]:
    return {
        "supplier_counts": dict(_last_offer_counts),
        "captured_at": _last_offer_counts_at or None,
    }
