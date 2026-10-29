"""Strong action verbs for resume bullet analysis.

Divided into tiers:
  - STRONG: leadership, ownership, measurable impact ("Architected", "Drove", "Spearheaded")
  - GOOD: solid but common ("Built", "Implemented", "Developed")
  - WEAK: passive or vague ("Helped", "Assisted", "Worked", "Involved")
"""

STRONG_ACTION_VERBS: frozenset[str] = frozenset({
    "accelerated", "achieved", "architected", "automated", "championed",
    "consolidated", "cut", "delivered", "deployed", "designed",
    "drove", "eliminated", "enabled", "engineered", "established",
    "executed", "founded", "generated", "grew", "identified",
    "improved", "increased", "introduced", "launched", "led",
    "mentored", "migrated", "modernised", "modernized", "optimised",
    "optimized", "orchestrated", "owned", "pioneered", "productionised",
    "productionized", "proposed", "rebuilt", "redesigned", "reduced",
    "refactored", "resolved", "scaled", "secured", "shaped",
    "shipped", "simplified", "slashed", "spearheaded", "streamlined",
    "transformed", "unified", "won",
})

GOOD_ACTION_VERBS: frozenset[str] = frozenset({
    "analyzed", "analysed", "applied", "built", "collaborated",
    "configured", "contributed", "created", "defined", "developed",
    "documented", "expanded", "extended", "fixed", "handled",
    "implemented", "integrated", "maintained", "managed", "mapped",
    "monitored", "operated", "planned", "prepared", "researched",
    "reviewed", "supported", "tested", "updated", "used",
    "validated", "wrote",
})

WEAK_VERBS: frozenset[str] = frozenset({
    "assisted", "attempted", "doing", "experienced", "familiar",
    "gained", "helped", "involved", "participated", "responsible",
    "tasked", "tried", "worked",
})

ALL_ACTION_VERBS: frozenset[str] = STRONG_ACTION_VERBS | GOOD_ACTION_VERBS


def classify_verb(verb: str) -> str:
    """Return 'strong', 'good', 'weak', or 'none'."""
    v = verb.lower().strip()
    if v in STRONG_ACTION_VERBS:
        return "strong"
    if v in GOOD_ACTION_VERBS:
        return "good"
    if v in WEAK_VERBS:
        return "weak"
    return "none"
