"""Section parser — split resume text into weighted sections.

Returns a list of (section_name, text, weight) tuples so the scorer can
apply higher weight to Skills and Experience matches vs Education.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from resume_pipeline.ats.config import SECTION_WEIGHTS


@dataclass
class ResumeSection:
    name: str          # normalised lowercase name
    raw_name: str      # as it appears in the resume
    text: str
    weight: float


# Common section header patterns (order matters — more specific first)
_HEADER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(technical\s+skill\s+set|technical\s+skills?|skills?\s+&\s+tools?|skills?)\s*$", re.I),
    re.compile(r"^(professional\s+summary|summary|executive\s+summary|profile|objective)\s*$", re.I),
    re.compile(r"^(work\s+experience|professional\s+experience|experience|employment(\s+history)?)\s*$", re.I),
    re.compile(r"^(professional\s+development|training|courses?|certifications?|licenses?)\s*$", re.I),
    re.compile(r"^(education|academic\s+background)\s*$", re.I),
    re.compile(r"^(projects?|side\s+projects?|personal\s+projects?)\s*$", re.I),
    re.compile(r"^(awards?|honors?|achievements?|accomplishments?)\s*$", re.I),
    re.compile(r"^(publications?|research)\s*$", re.I),
    re.compile(r"^(volunteer|community|leadership)\s*$", re.I),
]


def _section_weight(name: str) -> float:
    normalised = name.lower().strip()
    # Exact match first
    if normalised in SECTION_WEIGHTS:
        return SECTION_WEIGHTS[normalised]
    # Partial match
    for key, weight in SECTION_WEIGHTS.items():
        if key in normalised or normalised in key:
            return weight
    return SECTION_WEIGHTS["default"]


def _detect_header(line: str) -> str | None:
    """Return normalised section name if line looks like a section header."""
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return None
    # All caps header (common in LaTeX resumes)
    if stripped.isupper() and len(stripped.split()) <= 6:
        return stripped.lower()
    # Title case or known patterns
    for pattern in _HEADER_PATTERNS:
        if pattern.match(stripped):
            return stripped.lower()
    return None


def parse_sections(resume_text: str) -> list[ResumeSection]:
    """Split resume into sections with weights.

    Falls back to a single 'full_resume' section with weight 1.0 if no
    recognisable headers are found.

    Note: Text before the first detected header is accumulated into a
    'pre_header' section (name header) rather than discarded. This is
    intentional — the top of the resume (name/contact block) is low-signal
    for ATS purposes and gets default weight 1.0.
    """
    lines = resume_text.splitlines()
    sections: list[ResumeSection] = []
    current_name: str = "pre_header"
    current_raw: str = ""
    current_lines: list[str] = []
    found_any_header = False

    for line in lines:
        header = _detect_header(line)
        if header is not None:
            found_any_header = True
            # Save previous section — skip empty pre-header blocks
            text = "\n".join(current_lines).strip()
            if text and current_name != "pre_header":
                sections.append(ResumeSection(
                    name=current_name,
                    raw_name=current_raw,
                    text=text,
                    weight=_section_weight(current_name),
                ))
            elif text and current_name == "pre_header":
                # Contact/name block — include with low default weight
                sections.append(ResumeSection(
                    name=current_name,
                    raw_name=current_raw or "header",
                    text=text,
                    weight=SECTION_WEIGHTS["default"],
                ))
            current_name = header
            current_raw = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Flush last section
    text = "\n".join(current_lines).strip()
    if text:
        sections.append(ResumeSection(
            name=current_name,
            raw_name=current_raw,
            text=text,
            weight=_section_weight(current_name),
        ))

    if not found_any_header:
        # No section headers detected — treat the whole doc as one section
        return [ResumeSection(
            name="full_resume",
            raw_name="full_resume",
            text=resume_text,
            weight=1.0,
        )]

    return [s for s in sections if s.text]


def full_text_with_weights(sections: list[ResumeSection]) -> list[tuple[str, float]]:
    """Return list of (token, weight) for all words in the resume."""
    result: list[tuple[str, float]] = []
    for section in sections:
        for word in section.text.split():
            result.append((word.lower(), section.weight))
    return result
