"""URL and filename slugs.

Ported verbatim from v1's `resume_agent/storage.py::slugify`. The output of this function is
baked into every directory name v1 ever produced, and the v1 directory migration matches those
names, so a "tidier" implementation here would silently fail to recognise existing work.
"""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str, fallback: str = "untitled") -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    lowered = normalized.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or fallback
