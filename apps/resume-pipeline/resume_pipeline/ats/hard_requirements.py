"""Hard-requirement parsing and enforcement.

Parses a job description for explicit hard requirements:
  - Years of experience (e.g. "5+ years", "3-5 years of experience")
  - Degree level (Bachelor's, Master's, PhD, MBA)
  - Certifications (AWS Certified, PMP, CISSP, etc.)

Then checks whether a resume satisfies each requirement.
These are flagged as pass/fail — they do not reduce the numeric ATS score
(the score reflects keyword/structural/semantic fit), but callers can surface
unmet hard requirements as blockers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class HardRequirement:
    kind: str           # "years_experience" | "degree" | "certification"
    description: str    # human-readable label shown to user
    required_value: str # raw value extracted from JD
    met: bool           # whether the resume satisfies this requirement
    confidence: float   # 0.0–1.0 — how certain is the detection


@dataclass
class HardRequirementsResult:
    requirements: list[HardRequirement] = field(default_factory=list)
    all_met: bool = True
    unmet: list[HardRequirement] = field(default_factory=list)


# ─── Years-of-experience patterns ─────────────────────────────────────────────

# Matches: "5+ years", "5 or more years", "at least 5 years",
#          "minimum of 5 years", "3-5 years", "3 to 5 years of experience"
_YEARS_JD_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # "5+ years" / "5+ years of experience"
    (re.compile(r"(\d+)\+\s*years?\b", re.I), "plus"),
    # "at least N years" / "minimum N years" / "minimum of N years"
    (re.compile(r"(?:at\s+least|minimum\s+of?|more\s+than)\s+(\d+)\s+years?\b", re.I), "min"),
    # "N or more years"
    (re.compile(r"(\d+)\s+or\s+more\s+years?\b", re.I), "min"),
    # "N-M years" or "N to M years" — take the lower bound
    (re.compile(r"(\d+)\s*(?:-|to)\s*\d+\s+years?\b", re.I), "range"),
    # plain "N years of experience" (only if N >= 1 and <= 30 to skip "100 years ago")
    (re.compile(r"(\d+)\s+years?\s+of\s+(?:relevant\s+)?experience\b", re.I), "plain"),
]

# Matches year mentions in a resume (to gauge candidate's stated experience)
# e.g. "8 years of experience", "over 10 years"
_YEARS_RESUME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(\d+)\+?\s+years?\s+of\s+(?:\w+\s+)?experience\b", re.I),
    re.compile(r"over\s+(\d+)\s+years?\b", re.I),
    re.compile(r"(\d+)\+\s*years?\b", re.I),
]

# Date-span pattern to infer total experience: "2018 - 2023", "Jan 2018 - Present"
_DATE_SPAN_RE = re.compile(
    r"\b(20\d\d|19\d\d)\b.*?\b(?:(20\d\d|19\d\d)|present|current)\b",
    re.I,
)

_CURRENT_YEAR = date.today().year


def _extract_required_years(jd: str) -> int | None:
    """Return the minimum years of experience required by the JD, or None."""
    best: int | None = None
    for pattern, _ in _YEARS_JD_PATTERNS:
        for m in pattern.finditer(jd):
            try:
                n = int(m.group(1))
            except (IndexError, ValueError):
                continue
            if 1 <= n <= 30:  # sanity range — ignore "50 years ago" artifacts
                best = max(best or 0, n)
    return best


def _infer_resume_years(resume_text: str) -> int:
    """Estimate total years of experience from the resume text.

    Strategy (in priority order):
    1. Explicit "X years of experience" / "X+ years" in summary/experience
    2. Longest single date span found (start_year → end_year or Present)
    """
    # 1. Explicit mentions
    claimed: list[int] = []
    for pat in _YEARS_RESUME_PATTERNS:
        for m in pat.finditer(resume_text):
            try:
                n = int(m.group(1))
                if 1 <= n <= 40:
                    claimed.append(n)
            except (IndexError, ValueError):
                pass
    if claimed:
        return max(claimed)

    # 2. Date spans
    spans: list[int] = []
    for m in _DATE_SPAN_RE.finditer(resume_text):
        start = int(m.group(1))
        end_str = m.group(2)
        end = int(end_str) if end_str else _CURRENT_YEAR
        duration = end - start
        if 0 < duration <= 40:
            spans.append(duration)
    if spans:
        return max(spans)

    return 0  # cannot determine


# ─── Degree level patterns ─────────────────────────────────────────────────────

_DEGREE_LEVEL: dict[str, int] = {
    # 0 = any degree / associate
    "associate": 0,
    # 1 = bachelor's
    "bachelor": 1, "bs": 1, "ba": 1, "b.s": 1, "b.a": 1,
    "b.tech": 1, "b.e": 1, "btech": 1, "undergraduate": 1,
    "bsc": 1, "b.sc": 1, "beng": 1, "b.eng": 1,
    "b.com": 1, "bcom": 1,
    # 2 = master's
    "master": 2, "ms": 2, "ma": 2, "m.s": 2, "m.a": 2,
    "mba": 2, "m.tech": 2, "mtech": 2, "m.e": 2,
    "graduate degree": 2, "postgraduate": 2,
    # 3 = doctorate
    "phd": 3, "ph.d": 3, "doctorate": 3, "doctoral": 3,
}

# Patterns that indicate a degree is *required* (not just preferred)
_DEGREE_REQUIRED_RE = re.compile(
    r"(?:require[sd]?|must\s+have|minimum|necessary)\b[^.]{0,80}"
    r"\b(bachelor|master|phd|ph\.d|mba|b\.s|m\.s|b\.tech|m\.tech|doctorate)\b",
    re.I,
)
# Looser: just presence of a degree name near common phrasing
_DEGREE_MENTION_RE = re.compile(
    r"\b(bachelor'?s?|master'?s?|phd|ph\.d|mba|b\.s\.?|m\.s\.?|b\.tech|m\.tech"
    r"|undergraduate\s+degree|graduate\s+degree|doctorate)\b",
    re.I,
)


def _extract_required_degree(jd: str) -> tuple[str, float] | None:
    """Return (degree_label, confidence) for the minimum degree required, or None."""
    # First try a strict "required" pattern
    m = _DEGREE_REQUIRED_RE.search(jd)
    if m:
        raw = m.group(1).lower().rstrip("'s").rstrip(".")
        for key, _ in _DEGREE_LEVEL.items():
            if key.startswith(raw) or raw.startswith(key):
                return (m.group(1), 0.9)
        return (m.group(1), 0.7)

    # Fallback: first mention near the requirements section
    # (any mention in a JD usually implies it's required)
    for m2 in _DEGREE_MENTION_RE.finditer(jd):
        raw = m2.group(1).lower()
        return (m2.group(1), 0.6)

    return None


def _degree_level_from_text(text: str) -> int:
    """Return the highest degree level found in the given text."""
    best = -1
    for token, level in _DEGREE_LEVEL.items():
        if re.search(r"\b" + re.escape(token) + r"\b", text, re.I):
            best = max(best, level)
    return best


# ─── Certification patterns ────────────────────────────────────────────────────

# Common certification names — checked via substring/regex in JD and resume.
# Each entry: (display_name, pattern)
_KNOWN_CERTS: list[tuple[str, re.Pattern[str]]] = [
    # AWS
    ("AWS Certified Solutions Architect",
     re.compile(r"\baws\s+certified\s+solutions?\s+architect\b", re.I)),
    ("AWS Certified Developer",
     re.compile(r"\baws\s+certified\s+developer\b", re.I)),
    ("AWS Certified DevOps Engineer",
     re.compile(r"\baws\s+certified\s+devops\b", re.I)),
    ("AWS Certified (any)",
     re.compile(r"\baws\s+certified\b", re.I)),
    # Google Cloud
    ("Google Cloud Professional",
     re.compile(r"\bgoogle\s+cloud\s+(professional|certified)\b", re.I)),
    ("Google Associate Cloud Engineer",
     re.compile(r"\bassociate\s+cloud\s+engineer\b", re.I)),
    # Azure
    ("Microsoft Azure",
     re.compile(r"\b(azure\s+certified|az-\d{3}|microsoft\s+certified[^.]{0,30}azure)\b", re.I)),
    # Kubernetes / CNCF
    ("CKA / Kubernetes Certified",
     re.compile(r"\b(cka|ckad|cks|certified\s+kubernetes)\b", re.I)),
    # Project management
    ("PMP",
     re.compile(r"\bpmp\b", re.I)),
    ("Scrum Master (CSM/PSM)",
     re.compile(r"\b(csm|psm|certified\s+scrum\s+master|professional\s+scrum\s+master)\b", re.I)),
    ("Agile / SAFe",
     re.compile(r"\b(safe\s+agilist|safe\s+practitioner|leading\s+safe)\b", re.I)),
    # Security
    ("CISSP",
     re.compile(r"\bcissp\b", re.I)),
    ("CISM",
     re.compile(r"\bcism\b", re.I)),
    ("Security+ / CompTIA",
     re.compile(r"\b(security\+|comptia\s+security|comptia\s+network)\b", re.I)),
    ("CEH",
     re.compile(r"\bceh\b", re.I)),
    # Networking
    ("CCNA / CCNP",
     re.compile(r"\b(ccna|ccnp|cisco\s+certified)\b", re.I)),
    # Finance
    ("CPA",
     re.compile(r"\bcpa\b", re.I)),
    ("CFA",
     re.compile(r"\bcfa\b", re.I)),
    # Data / ML
    ("Databricks Certified",
     re.compile(r"\bdatabricks\s+(certified|associate|professional)\b", re.I)),
    ("Snowflake SnowPro",
     re.compile(r"\b(snowpro|snowflake\s+certif)\b", re.I)),
    # Six Sigma
    ("Six Sigma",
     re.compile(r"\b(six\s+sigma|lean\s+six\s+sigma|green\s+belt|black\s+belt)\b", re.I)),
]

# JD context signals that a cert is required (not just mentioned as "nice to have")
_CERT_REQUIRED_CONTEXT_RE = re.compile(
    r"(?:require[sd]?|must|expected|mandatory|preferred|certification\s+(?:is|are)\s+(?:a\s+)?(?:plus|required))"
    r"[^.]{0,120}",
    re.I,
)


def _extract_required_certs(jd: str) -> list[tuple[str, float]]:
    """Return list of (cert_display_name, confidence) for certs mentioned in the JD."""
    found: list[tuple[str, float]] = []
    seen: set[str] = set()

    for display_name, pat in _KNOWN_CERTS:
        m = pat.search(jd)
        if not m or display_name in seen:
            continue
        seen.add(display_name)

        # Slightly higher confidence if surrounded by requirement language
        start = max(0, m.start() - 150)
        context = jd[start: m.end() + 100]
        has_required_context = bool(_CERT_REQUIRED_CONTEXT_RE.search(context))
        confidence = 0.85 if has_required_context else 0.65
        found.append((display_name, confidence))

    return found


def _has_cert_in_resume(cert_name: str, cert_pattern: re.Pattern[str], resume: str) -> bool:
    return bool(cert_pattern.search(resume))


# ─── Public API ───────────────────────────────────────────────────────────────

def check_hard_requirements(jd_text: str, resume_text: str) -> HardRequirementsResult:
    """Parse the JD for hard requirements and check them against the resume.

    Args:
        jd_text:     cleaned job description text
        resume_text: parsed resume text

    Returns:
        HardRequirementsResult with each requirement's met/unmet status.
    """
    requirements: list[HardRequirement] = []

    # ── Years of experience ──────────────────────────────────────────────────
    required_years = _extract_required_years(jd_text)
    if required_years is not None:
        resume_years = _infer_resume_years(resume_text)
        met = resume_years >= required_years
        requirements.append(HardRequirement(
            kind="years_experience",
            description=f"{required_years}+ years of experience",
            required_value=str(required_years),
            met=met,
            confidence=0.85,
        ))

    # ── Degree ───────────────────────────────────────────────────────────────
    degree_info = _extract_required_degree(jd_text)
    if degree_info is not None:
        degree_label, confidence = degree_info
        required_level = _degree_level_from_text(degree_label)
        resume_level = _degree_level_from_text(resume_text)
        # Give benefit of the doubt when either level can't be determined
        met = (required_level == -1) or (resume_level == -1) or (resume_level >= required_level)
        requirements.append(HardRequirement(
            kind="degree",
            description=f"{degree_label} degree required",
            required_value=degree_label,
            met=met,
            confidence=confidence,
        ))

    # ── Certifications ───────────────────────────────────────────────────────
    for cert_name, cert_confidence in _extract_required_certs(jd_text):
        # Find the pattern object to check resume
        cert_pattern = next(
            (pat for (dn, pat) in _KNOWN_CERTS if dn == cert_name), None
        )
        if cert_pattern is None:
            continue
        met = _has_cert_in_resume(cert_name, cert_pattern, resume_text)
        requirements.append(HardRequirement(
            kind="certification",
            description=f"Certification: {cert_name}",
            required_value=cert_name,
            met=met,
            confidence=cert_confidence,
        ))

    unmet = [r for r in requirements if not r.met]
    return HardRequirementsResult(
        requirements=requirements,
        all_met=len(unmet) == 0,
        unmet=unmet,
    )
