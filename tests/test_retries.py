import types
import pytest

from utils.retries import retry_on_transient, is_transient_db_error


class DummyPsycopgError(Exception):
    def __init__(self, pgcode: str):
        super().__init__(pgcode)
        self.pgcode = pgcode


def test_is_transient_db_error():
    assert is_transient_db_error(DummyPsycopgError("40P01"))  # deadlock
    assert is_transient_db_error(DummyPsycopgError("40001"))  # serialization failure
    assert not is_transient_db_error(DummyPsycopgError("23505"))  # unique_violation


def test_retry_on_transient_succeeds_after_two_retries(monkeypatch):
    calls = {"n": 0}

    @retry_on_transient(max_attempts=3, base_delay_ms=1)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise DummyPsycopgError("40001")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_retry_on_transient_raises_non_transient():
    @retry_on_transient(max_attempts=2, base_delay_ms=1)
    def fn():
        raise DummyPsycopgError("23505")

    with pytest.raises(DummyPsycopgError):
        fn()
