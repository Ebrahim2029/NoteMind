from __future__ import annotations

from typing import Dict, List

from core.services.session_service import SessionService
from utils.intents import extract_intent


class FakeRedis:
    def __init__(self):
        self.lists: Dict[str, List[str]] = {}
        self.exp: Dict[str, int] = {}

    # List ops
    def lpush(self, key, val):
        self.lists.setdefault(key, [])
        self.lists[key].insert(0, val)

    def ltrim(self, key, start, stop):
        arr = self.lists.get(key, [])
        self.lists[key] = arr[start : stop + 1] if arr else []

    def lrange(self, key, start, stop):
        arr = self.lists.get(key, [])
        if not arr:
            return []
        # emulate inclusive stop
        stop = min(stop, len(arr) - 1)
        return arr[start : stop + 1]

    def expire(self, key, ttl):
        self.exp[key] = ttl


def test_session_messages_and_intents():
    r = FakeRedis()
    svc = SessionService(redis=r)

    sid = "s-1"
    # Add >10 messages to test trimming to last 10
    for i in range(15):
        svc.add_message(sid, "user", f"m{i}")

    hist = svc.get_history(sid)
    assert len(hist) == 10
    assert hist[0]["content"] == "m5"     # oldest kept
    assert hist[-1]["content"] == "m14"   # newest

    # Intents
    intents = ["create_note", "search_notes", "general", "update_note"]
    for it in intents:
        svc.add_intent(sid, it)

    recent = svc.get_recent_intents(sid)
    # last 3 only, oldest→newest
    assert recent == ["search_notes", "general", "update_note"]


def test_intent_extractor():
    assert extract_intent("please create a note") == "create_note"
    assert extract_intent("find this") == "search_notes"
    assert extract_intent("random chatter") == "general"
