

import random
import time
from functools import wraps
from typing import Callable, Type, Tuple

# نستخدم أخطاء psycopg2 بالاسم لتفادي الاستيراد الصعب وقت الاختبارات على بيئات مختلفة
TRANSIENT_SQLSTATE_PREFIXES = ("40P01", "40001")  # DeadlockDetected, SerializationFailure


def is_transient_db_error(exc: Exception) -> bool:
    """
    يحاول استخراج SQLSTATE من psycopg2 (إن وجد) للحكم هل الخطأ عابر.
    """
    # psycopg2: exc.pgcode يحمل SQLSTATE
    code = getattr(exc, "pgcode", None)
    if code and any(code.startswith(p) for p in TRANSIENT_SQLSTATE_PREFIXES):
        return True
    return False


def retry_on_transient(max_attempts: int = 4, base_delay_ms: int = 20) -> Callable:
    """
    غلاف إعادة المحاولة مع backoff أسي لأخطاء قواعد البيانات العابرة.
    - المحاولة التالية بعد: base_delay_ms * (2 ** (attempt-1))
    """
    def deco(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            attempt = 1
            while True:
                try:
                    return fn(*args, **kwargs)
                except Exception as e:  # noqa: BLE001
                    if attempt >= max_attempts or not is_transient_db_error(e):
                        raise
                    delay = (base_delay_ms * (2 ** (attempt - 1))) / 1000.0
                    time.sleep(delay)
                    attempt += 1
        return wrapper
    return deco

def retry_io(
    exceptions: tuple[Type[BaseException], ...] = (Exception,),
    attempts: int = 4,
    base_delay: float = 0.25,
    jitter: float = 0.2,
) -> Callable:
    """Exponential backoff with jitter."""
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_err = None
            for i in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as err:  # pragma: no cover (branches tested via behavior)
                    last_err = err
                    # exponential backoff + jitter
                    sleep_for = delay + random.uniform(0, jitter)
                    time.sleep(sleep_for)
                    delay *= 2
            assert last_err is not None
            raise last_err
        return wrapper
    return decorator