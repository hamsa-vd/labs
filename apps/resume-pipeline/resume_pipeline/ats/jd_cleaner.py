"""JD cleaner — strips website boilerplate from scraped job descriptions.

When a JD is copy-pasted or scraped from a website it often has navigation
menus, headers, footers, and cookie notices mixed in. This module finds
where the actual job content starts and strips everything before it.
"""

from __future__ import annotations

import re

# Lines that strongly signal the start of actual job content
_JOB_CONTENT_SIGNALS: list[re.Pattern[str]] = [
    re.compile(r"\b(about\s+(the\s+)?(role|position|team|job|company))\b", re.I),
    re.compile(r"\b(job\s+(summary|description|overview|details))\b", re.I),
    re.compile(r"\b(position\s+(summary|overview|description))\b", re.I),
    re.compile(r"\b(what\s+you.ll\s+(do|be|work|own|build))\b", re.I),
    re.compile(r"\b(responsibilities|key\s+responsibilities)\b", re.I),
    re.compile(r"\b(qualifications?|requirements?|requires?|required|must\s+have|you\s+(will|must|should)\s+have)\b", re.I),
    re.compile(r"\b(what\s+(we|you)\s+(offer|need|require|are\s+looking))\b", re.I),
    re.compile(r"(software|senior|lead|principal|staff)\s+(engineer|developer|architect|manager)", re.I),
]

# Lines that are clearly navigation/boilerplate junk to skip
_BOILERPLATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^skip\s+to\s+(main\s+)?content$", re.I),
    re.compile(r"^(careers|jobs|home|menu|search|apply|login|sign\s+in)$", re.I),
    re.compile(r"^teams?$", re.I),
    re.compile(r"^(administration|commercial|communications|corporate|finance|marketing|legal|strategy|operations|technology)$", re.I),
    re.compile(r"^(human\s+resources?|inclusion\s+&\s+diversity|contractor\s+positions?)$", re.I),
    re.compile(r"^similar\s+positions?$", re.I),
    # Only strip copyright/legal lines if they're clearly isolated footer tokens
    # (no surrounding sentence context). "Privacy Policy" multi-word is intentionally
    # NOT matched to avoid stripping a legitimate section header.
    re.compile(r"^(cookie\s+policy|terms\s+of\s+use|copyright\s+notice|all\s+rights\s+reserved)$", re.I),
    re.compile(r"^\s*$"),  # empty lines count but don't match content
]


def _is_boilerplate(line: str) -> bool:
    stripped = line.strip()
    return any(p.match(stripped) for p in _BOILERPLATE_PATTERNS)


def _is_content_signal(line: str) -> bool:
    return any(p.search(line) for p in _JOB_CONTENT_SIGNALS)


_FOOTER_START_SIGNALS: list[re.Pattern[str]] = [
    re.compile(r"\b(accommodation\s+request[s]?|disability\s+accommodation)\b", re.I),
    re.compile(r"\b(similar\s+positions?|related\s+(jobs?|positions?))\b", re.I),
    re.compile(r"\b(we\s+are\s+proud|best\s+place\s+to\s+work|glassdoor|award.winning\s+culture)\b", re.I),
    re.compile(r"\b(our\s+(brands?|portfolio|family\s+of\s+brands?))\b", re.I),
    # Generic copyright/trademark line: "© 2024 CompanyName Inc." or "2024 Acme Corp."
    re.compile(r"^\s*\©?\s*\d{4}\s+[A-Z][A-Za-z\s]+(?:Inc|LLC|Corp|Group|Ltd)\.?\s*$", re.I),
    re.compile(r"\b(all\s+rights\s+reserved|trademarks\s+and\s+logos)\b", re.I),
    re.compile(r"\b(already\s+applied|share\s+this\s+position)\b", re.I),
]

# Footer signals that are ONLY valid when the line is short (< 80 chars) —
# to avoid mid-paragraph false-positives on phrases like "learn more about X"
_FOOTER_SHORT_LINE_SIGNALS: list[re.Pattern[str]] = [
    re.compile(r"\b(learn\s+(more|about)|apply\s+now|view\s+(job|account))\b", re.I),
    re.compile(r"^(full.time|part.time|contract|temporary)\s*(regular|position)?$", re.I),
]


def _is_footer_signal(line: str) -> bool:
    """Return True if line strongly signals the start of job posting footer.

    Long lines (paragraphs) are NOT considered footer signals for ambiguous
    patterns — this prevents "learn more about our culture" mid-JD from
    truncating the output.
    """
    stripped = line.strip()
    if any(p.search(stripped) for p in _FOOTER_START_SIGNALS):
        return True
    # Short-line-only signals
    if len(stripped) < 80 and any(p.search(stripped) for p in _FOOTER_SHORT_LINE_SIGNALS):
        return True
    return False


def clean_jd(raw_jd: str) -> str:
    """Return the JD with website boilerplate stripped.

    Strategy:
    1. Scan line by line from the top.
    2. Find the first line that looks like real job content.
    3. Only search for footer signals in the last 30% of lines (30% doc bound).
       This prevents mid-JD phrases like "learn more" or "apply now" from
       truncating real content.
    4. Return content_start:footer_start, minus boilerplate lines.
    """
    lines = raw_jd.splitlines()

    # Find start of real content
    content_start = 0
    for i, line in enumerate(lines):
        if _is_content_signal(line):
            content_start = i
            break
    else:
        # No content signal found — the input is likely pure boilerplate/navigation.
        # Return empty string so the caller (scorer.score()) raises ValueError.
        return ""

    # Find end of real content.
    # Only search for footer signals in the last 30% of lines — protects the
    # first 70% of content from false-positive truncation on phrases like
    # "learn more about our platform" that could otherwise fire mid-JD.
    content_end = len(lines)
    footer_search_from = content_start + max(1, int((len(lines) - content_start) * 0.70))
    for i in range(footer_search_from, len(lines)):
        if _is_footer_signal(lines[i]):
            content_end = i
            break

    cleaned_lines = lines[content_start:content_end]
    result = "\n".join(l for l in cleaned_lines if not _is_boilerplate(l))
    return result.strip()
