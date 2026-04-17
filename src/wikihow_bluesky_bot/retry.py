from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_with_backoff(
    operation: Callable[[], T],
    *,
    retries: int,
    base_delay_seconds: float,
    retryable: Callable[[Exception], bool],
) -> T:
    if retries < 1:
        raise ValueError("retries must be >= 1")

    for attempt in range(1, retries + 1):
        try:
            return operation()
        except Exception as exc:
            if attempt == retries or not retryable(exc):
                raise
            exponent: int = attempt - 1
            multiplier = 1.0
            for _ in range(exponent):
                multiplier *= 2.0
            delay: float = (base_delay_seconds * multiplier) + 0.25
            time.sleep(delay)

    raise RuntimeError("unreachable")
