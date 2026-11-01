"""
Super-light intent extractor.

Heuristic rules that map a user message to a coarse intent:
- "create", "new", "add"  -> "create_note"
- "update", "edit"        -> "update_note"
- "delete", "remove"      -> "delete_note"
- "search", "find", "look"-> "search_notes"
Fallback: "general"
"""




_RULES = [
    (("create", "new", "add"), "create_note"),
    (("update", "edit"), "update_note"),
    (("delete", "remove"), "delete_note"),
    (("search", "find", "look"), "search_notes"),
]


def extract_intent(text: str) -> str:
    t = (text or "").lower()
    for keys, label in _RULES:
        if any(k in t for k in keys):
            return label
    return "general"
