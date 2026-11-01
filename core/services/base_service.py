"""
BaseService: common wiring for services (timing, tracing hooks, Redis access).
"""



import time
from typing import Any, Callable, Optional


class BaseService:
    def __init__(self, redis=None):
        self.redis = redis

    def _timeit(self, label: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def deco(fn: Callable[..., Any]):
            def wrapper(*args, **kwargs):
                t0 = time.perf_counter()
                try:
                    return fn(*args, **kwargs)
                finally:
                    elapsed = (time.perf_counter() - t0) * 1000
                    # Replace with metrics counter/gauge
                    # e.g., metrics.observe(f"{label}_ms", elapsed)
                    _ = elapsed
            return wrapper
        return deco
