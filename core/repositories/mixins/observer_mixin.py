"""
ObserverMixin: emit an outbox event after a successful commit.

Expected attributes/methods on the repository:
- self._build_event(op: str, payload: dict) -> dict
- self._outbox_emit(event: dict) -> None
"""



from typing import Dict


class ObserverMixin:
    def _after_commit(self) -> None:
        # No-op by default; repositories will call _outbox_emit inside their write methods
        pass

    def _outbox_emit(self, event: Dict) -> None:
        # Repositories should override or wire this to utils.outbox.emit_event
        pass
