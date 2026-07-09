from __future__ import annotations

import logging
from collections import Counter
from threading import Lock
from typing import Any


logger = logging.getLogger("talent_advisor")
_metrics: Counter[str] = Counter()
_metrics_lock = Lock()


def record_metric(name: str, amount: int = 1) -> None:
    with _metrics_lock:
        _metrics[name] += amount


def metrics_snapshot() -> dict[str, int]:
    with _metrics_lock:
        return dict(_metrics)


def log_event(event: str, **fields: Any) -> None:
    logger.info("event=%s %s", event, " ".join(f"{key}={value}" for key, value in fields.items()))
