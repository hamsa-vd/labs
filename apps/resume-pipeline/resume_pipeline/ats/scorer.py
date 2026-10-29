"""Core ATS scoring engine.

Score breakdown (0–100):
  - Keyword score    (50 pts): section-weighted, synonym-aware keyword match
  - Structural score (30 pts): action verb quality, quantification, section completeness
  - Semantic score   (20 pts): context richness — impact phrase density, bullet depth,
                               seniority alignment (independent of keyword score)

Each component is independently explainable so the caller can surface
exactly why the score is what it is and what to fix.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from resume_pipeline.ats.action_verbs import STRONG_ACTION_VERBS, GOOD_ACTION_VERBS, WEAK_VERBS, classify_verb
from resume_pipeline.ats.config import (
    ACTION_VERB_SCORE_MAX,
    HARD_SKILL_KEYWORD_MULTIPLIER,
    KEYWORD_SECTION_CREDIT,
    KEYWORD_WEIGHT,
    QUANTIFICATION_SCALE,
    QUANTIFICATION_SCORE_MAX,
    REQUIRED_SECTIONS,
    SECTION_COMPLETENESS_SCORE_MAX,
    SEMANTIC_WEIGHT,
    SOFT_SKILL_KEYWORD_MULTIPLIER,
    STRUCTURAL_WEIGHT,
)
from resume_pipeline.ats.hard_requirements import HardRequirementsResult, check_hard_requirements
from resume_pipeline.ats.jd_cleaner import clean_jd
from resume_pipeline.ats.keyword_extractor import JDKeyword, extract_keywords
from resume_pipeline.ats.resume_parser import parse as parse_resume
from resume_pipeline.ats.section_parser import ResumeSection, parse_sections

_NUMBER_RE = re.compile(r"\d[\d,.%xX]*|\b\d+[kKmMbB%]\b")
_BULLET_START_RE = re.compile(r"^\s*[\-•◦▸*]\s+(.+)$")


# ─── Result dataclasses ───────────────────────────────────────────────────────

@dataclass
class KeywordResult:
    matched: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)
    missing_nice_to_have: list[str] = field(default_factory=list)
    score: float = 0.0                  # 0–50


@dataclass
class StructuralResult:
    action_verb_score: float = 0.0     # 0–10
    quantification_score: float = 0.0  # 0–10
    section_completeness_score: float = 0.0  # 0–10
    total_bullets: int = 0
    strong_verb_bullets: int = 0
    good_verb_bullets: int = 0
    weak_verb_bullets: int = 0
    no_verb_bullets: int = 0
    quantified_bullets: int = 0
    found_sections: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    score: float = 0.0                 # 0–30


@dataclass
class SemanticResult:
    top_jd_phrases: list[str] = field(default_factory=list)
    matched_phrases: list[str] = field(default_factory=list)
    score: float = 0.0                 # 0–20


@dataclass
class ATSResult:
    total_score: float = 0.0           # 0–100, rounded to 1 dp
    grade: str = ""                    # Excellent / Good / Fair / Poor
    keyword: KeywordResult = field(default_factory=KeywordResult)
    structural: StructuralResult = field(default_factory=StructuralResult)
    semantic: SemanticResult = field(default_factory=SemanticResult)
    hard_requirements: HardRequirementsResult = field(default_factory=HardRequirementsResult)
    top_actions: list[str] = field(default_factory=list)   # highest-impact fixes


# ─── Keyword scoring ──────────────────────────────────────────────────────────

from resume_pipeline.ats.keyword_extractor import _extract_phrases, _extract_single_tokens  # noqa: E402


def _build_resume_token_map(
    sections: list[ResumeSection],
) -> tuple[dict[str, float], dict[str, str]]:
    """Return ({token: max_weight}, {token: best_section_name}) in one pass.

    Doing a single extraction pass here avoids the duplicate work that was
    previously happening inside _score_keywords (which re-extracted every
    section's phrases to build the token→section lookup).
    """
    token_map: dict[str, float] = {}
    token_to_section: dict[str, str] = {}
    for section in sections:
        w = section.weight
        tokens = _extract_phrases(section.text) + _extract_single_tokens(section.text)
        for canonical in tokens:
            if w > token_map.get(canonical, 0.0):
                token_map[canonical] = w
                token_to_section[canonical] = section.name
    return token_map, token_to_section


def _section_credit(section_name: str) -> float:
    """Return credit fraction (0–1) for a keyword found in a given section.

    Real ATS systems do near-boolean matching: Skills section = strong signal,
    Education = very weak. This replaces the linear (0.5 + 0.5 * fraction)
    formula which over-rewarded keywords buried in Education (67% credit).
    """
    name = section_name.lower()
    for key, credit in KEYWORD_SECTION_CREDIT.items():
        if key in name:
            return credit
    return KEYWORD_SECTION_CREDIT["default"]


def _score_keywords(
    jd_keywords: list[JDKeyword],
    resume_token_map: dict[str, float],
    token_to_section: dict[str, str],
) -> KeywordResult:
    result = KeywordResult()
    total_possible = 0.0
    total_earned = 0.0

    for kw in jd_keywords:
        # Soft skills carry reduced weight — they're near-universal in JDs
        # and easy to game, so real ATS systems penalise over-reliance on them.
        skill_multiplier = SOFT_SKILL_KEYWORD_MULTIPLIER if kw.is_soft_skill else HARD_SKILL_KEYWORD_MULTIPLIER
        possible = kw.importance_weight * skill_multiplier
        total_possible += possible

        section_weight = resume_token_map.get(kw.canonical, 0.0)
        if section_weight > 0:
            # Threshold-based credit: full credit in Skills, near-zero in Education
            best_section = token_to_section.get(kw.canonical, "default")
            credit = _section_credit(best_section)
            earned = possible * credit
            total_earned += earned
            result.matched.append(kw.canonical)
        else:
            if kw.importance == "required":
                result.missing_required.append(kw.canonical)
            elif kw.importance == "preferred":
                result.missing_preferred.append(kw.canonical)
            else:
                result.missing_nice_to_have.append(kw.canonical)

    if total_possible == 0:
        result.score = 0.0
        return result

    raw_ratio = total_earned / total_possible
    result.score = round(raw_ratio * KEYWORD_WEIGHT, 2)
    return result


# ─── Structural scoring ───────────────────────────────────────────────────────

def _extract_bullets(text: str) -> list[str]:
    """Return first word of each bullet line."""
    bullets: list[str] = []
    for line in text.splitlines():
        m = _BULLET_START_RE.match(line)
        if m:
            bullets.append(m.group(1).strip())
    return bullets


def _score_structural(sections: list[ResumeSection]) -> StructuralResult:
    result = StructuralResult()
    full_text = "\n".join(s.text for s in sections)
    all_bullets = _extract_bullets(full_text)

    result.total_bullets = len(all_bullets)

    # Action verb analysis
    for bullet in all_bullets:
        first_word = bullet.split()[0].rstrip(".,;:") if bullet.split() else ""
        cls = classify_verb(first_word)
        if cls == "strong":
            result.strong_verb_bullets += 1
        elif cls == "good":
            result.good_verb_bullets += 1
        elif cls == "weak":
            result.weak_verb_bullets += 1
        else:
            result.no_verb_bullets += 1

    if result.total_bullets > 0:
        strong_ratio = result.strong_verb_bullets / result.total_bullets
        good_ratio = result.good_verb_bullets / result.total_bullets
        # Strong verbs = full credit, good verbs = half credit
        verb_score = (strong_ratio * ACTION_VERB_SCORE_MAX) + (good_ratio * ACTION_VERB_SCORE_MAX * 0.5)
        result.action_verb_score = round(min(verb_score, ACTION_VERB_SCORE_MAX), 2)
    else:
        result.action_verb_score = 0.0

    # Quantification analysis
    for bullet in all_bullets:
        if _NUMBER_RE.search(bullet):
            result.quantified_bullets += 1

    if result.total_bullets > 0:
        quant_ratio = result.quantified_bullets / result.total_bullets
        result.quantification_score = round(
            min(quant_ratio * QUANTIFICATION_SCORE_MAX * QUANTIFICATION_SCALE, QUANTIFICATION_SCORE_MAX), 2
        )
    else:
        result.quantification_score = 0.0

    # Section completeness
    section_names = {s.name.lower() for s in sections}

    def _has_section(keyword: str) -> bool:
        return any(keyword in name for name in section_names)

    present = set()
    if _has_section("skill") or _has_section("technical"):
        present.add("skills")
    if _has_section("experience") or _has_section("employment"):
        present.add("experience")
    if _has_section("education"):
        present.add("education")
    if _has_section("summary") or _has_section("objective") or _has_section("profile"):
        present.add("summary")

    result.found_sections = sorted(present)
    result.missing_sections = sorted(REQUIRED_SECTIONS - present)
    completeness = len(present) / len(REQUIRED_SECTIONS)
    result.section_completeness_score = round(completeness * SECTION_COMPLETENESS_SCORE_MAX, 2)

    result.score = round(
        result.action_verb_score + result.quantification_score + result.section_completeness_score,
        2,
    )
    return result


# ─── Semantic scoring (TF-IDF noun phrases) ───────────────────────────────────

# ─── Semantic scoring — context richness (independent of keyword score) ────────

# High-impact phrases that indicate strong, substantive bullets
_IMPACT_PHRASES: re.Pattern[str] = re.compile(
    r"\b(reduc(ed|ing)|improv(ed|ing)|increas(ed|ing)|cut|sav(ed|ing)|"
    r"migrat(ed|ing)|architect(ed|ing)|scal(ed|ing)|optim(is|iz)(ed|ing)|"
    r"own(ed|ing)|deliver(ed|ing)|launch(ed|ing)|built|drove|led|"
    r"eliminat(ed|ing)|automat(ed|ing)|accelerat(ed|ing)|transform(ed|ing))\b",
    re.I,
)

# Seniority and depth signals in the JD
_SENIORITY_SIGNALS: re.Pattern[str] = re.compile(
    r"\b(senior|staff|lead|principal|architect|sr\.?|iii|iv|l[34567])\b", re.I,
)

_YEARS_RE = re.compile(r"\b(\d+)\+?\s+years?\b", re.I)

# Role function clusters — used to detect clear cross-domain mismatches
# (e.g. applying for a Data Engineer role with a Frontend-only background)
_ROLE_CLUSTERS: dict[str, re.Pattern[str]] = {
    "backend": re.compile(
        r"\b(backend|back.end|server.side|api|microservice|distributed\s+system|java|python|go|"
        r"spring|node\.?js|rest|grpc|kafka|service\s+mesh)\b", re.I
    ),
    "frontend": re.compile(
        r"\b(frontend|front.end|ui|ux|react|vue|angular|css|html|web\s+app|"
        r"javascript|typescript|browser|mobile\s+web)\b", re.I
    ),
    "data": re.compile(
        r"\b(data\s+(engineer|scientist|analyst|platform)|etl|pipeline|spark|"
        r"airflow|dbt|warehouse|lakehouse|pandas|ml\s+pipeline|feature\s+store)\b", re.I
    ),
    "ml": re.compile(
        r"\b(machine\s+learning|ml|deep\s+learning|nlp|llm|model\s+training|"
        r"pytorch|tensorflow|data\s+scientist|ai\s+engineer)\b", re.I
    ),
    "devops": re.compile(
        r"\b(devops|sre|platform\s+eng|infrastructure|kubernetes|helm|terraform|"
        r"ci.?cd|jenkins|github\s+actions|observability|on.call)\b", re.I
    ),
    "mobile": re.compile(
        r"\b(ios|android|swift|kotlin|react\s+native|flutter|mobile\s+app|"
        r"xcode|cocoapods|gradle)\b", re.I
    ),
    "qa": re.compile(
        r"\b(qa|quality\s+assurance|sdet|test\s+engineer|automation\s+test|"
        r"selenium|cypress|playwright|testng|junit|pytest|load\s+test|performance\s+test)\b", re.I
    ),
    "security": re.compile(
        r"\b(security\s+engineer|appsec|infosec|penetration\s+test|pentest|soc|"
        r"vulnerability|devsecops|owasp|siem|iam|zero\s+trust|cryptograph)\b", re.I
    ),
    "product": re.compile(
        r"\b(product\s+manager|product\s+designer|ux\s+designer|ui\s+designer|"
        r"figma|sketch|wireframe|user\s+research|design\s+system|product\s+owner)\b", re.I
    ),
}


def _role_clusters(text: str) -> set[str]:
    """Return the set of role clusters matched in text."""
    return {name for name, pat in _ROLE_CLUSTERS.items() if pat.search(text)}


def _score_title_match(resume_title_area: str, jd_text: str) -> float:
    """Score alignment between the JD's role function and the resume title area.

    Returns 0–3 pts:
    - 3: resume clusters overlap with JD clusters (or neither has a clear cluster)
    - 1.5: partial overlap (candidate is multi-discipline, some match)
    - 0: clear mismatch (e.g. JD=Data Engineer, resume=iOS Developer)
    """
    jd_clusters = _role_clusters(jd_text)
    resume_clusters = _role_clusters(resume_title_area)

    if not jd_clusters or not resume_clusters:
        # No clear cluster detected — can't determine mismatch, give partial credit
        return 1.5

    overlap = jd_clusters & resume_clusters
    if overlap:
        return 3.0
    if len(resume_clusters) > 1:
        # Multi-discipline resume — some clusters may transfer
        return 1.5
    # Clear domain mismatch
    return 0.0


def _score_semantic(resume_text: str, jd_text: str) -> SemanticResult:
    """Score context richness — independent of keyword matching.

    Measures (total 20 pts):
    1. Impact phrase density (0–8 pts): bullets using strong outcome language
    2. Average bullet depth (0–5 pts): longer, structured bullets = more substantive
    3. Seniority alignment (0–4 pts): does resume title area match JD level?
    4. Title/role match (0–3 pts): does the resume job function match the JD role?

    This replaces TF-IDF over the same phrase set (which was ~95% correlated
    with keyword score and thus not adding independent signal).
    """
    result = SemanticResult()
    bullets = [
        m.group(1).strip()
        for line in resume_text.splitlines()
        if (m := _BULLET_START_RE.match(line))
    ]

    if not bullets:
        result.score = 0.0
        return result

    # 1. Impact phrase density (0–8 pts)
    bullets_with_impact = sum(1 for b in bullets if _IMPACT_PHRASES.search(b))
    impact_ratio = bullets_with_impact / len(bullets)
    # Full marks at 60%+ impact ratio
    impact_score = min(impact_ratio / 0.6, 1.0) * 8.0

    # 2. Bullet depth / substance (0–5 pts)
    avg_words = sum(len(b.split()) for b in bullets) / len(bullets)
    # Full marks at 18+ words avg; sparse bullets (<10 words) score near 0
    depth_score = min(max(avg_words - 8, 0) / 10.0, 1.0) * 5.0

    # 3. Seniority alignment (0–4 pts)
    jd_years = [int(m.group(1)) for m in _YEARS_RE.finditer(jd_text)]
    resume_years = [int(m.group(1)) for m in _YEARS_RE.finditer(resume_text)]
    jd_is_senior = bool(_SENIORITY_SIGNALS.search(jd_text))

    # Only check the resume title/summary area for seniority — exclude bullet
    # points entirely (candidate titles are never in bullets).
    # For short resumes, "first 15 lines" may include WE bullets where
    # "Assisted senior engineers" would falsely signal seniority.
    _resume_title_lines = [
        line for line in resume_text.splitlines()[:20]
        if not _BULLET_START_RE.match(line)  # skip bullet points
    ]
    _resume_title_area = "\n".join(_resume_title_lines)
    resume_signals_senior = bool(_SENIORITY_SIGNALS.search(_resume_title_area))

    seniority_score = 0.0
    if jd_is_senior and resume_signals_senior:
        seniority_score += 2.0
    elif not jd_is_senior:
        seniority_score += 2.0  # not a senior role — no mismatch
    if jd_years and resume_years:
        jd_min = min(jd_years)
        resume_max = max(resume_years)
        if resume_max >= jd_min:
            seniority_score += 2.0
        elif resume_max >= jd_min - 1:
            seniority_score += 1.0  # close enough

    # 4. Title/role function match (0–3 pts)
    # Extract the dominant role function from JD and resume title area,
    # then check for overlap. Penalise clear mismatches (e.g. JD=Data Engineer,
    # resume=Frontend Developer).
    title_score = _score_title_match(_resume_title_area, jd_text)

    total = impact_score + depth_score + seniority_score + title_score
    result.score = round(min(total, SEMANTIC_WEIGHT), 2)

    # Surface debug info
    impactful = [b for b in bullets if _IMPACT_PHRASES.search(b)]
    result.matched_phrases = [b[:80] for b in impactful[:5]]
    seniority_tag = "aligned" if seniority_score >= 2 else "gap"
    result.top_jd_phrases = [
        f"avg_words={avg_words:.1f}",
        f"impact_ratio={impact_ratio:.0%}",
        f"seniority={seniority_tag}",
        f"title_score={title_score:.1f}/3",
    ]
    return result


# ─── Grade ────────────────────────────────────────────────────────────────────

def _grade(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Poor"


def _top_actions(
    keyword: KeywordResult,
    structural: StructuralResult,
    hard_req: HardRequirementsResult | None = None,
) -> list[str]:
    """Return prioritised list of improvement actions."""
    actions: list[str] = []
    if hard_req and hard_req.unmet:
        for req in hard_req.unmet:
            actions.append(f"❌ Hard requirement not met: {req.description} (confidence: {int(req.confidence * 100)}%)")
    if keyword.missing_required:
        top = keyword.missing_required[:5]
        actions.append(f"Add missing required keywords to Skills/Experience: {', '.join(top)}")
    if structural.weak_verb_bullets > 0 or structural.no_verb_bullets > 0:
        actions.append(
            f"{structural.weak_verb_bullets + structural.no_verb_bullets} bullets start with weak/no action verb. "
            "Rewrite to start with: Architected, Drove, Optimised, Delivered, etc."
        )
    if structural.quantification_score < 6:
        actions.append(
            f"Only {structural.quantified_bullets}/{structural.total_bullets} bullets have metrics. "
            "Add numbers (%, latency, team size, cost) to at least 50% of bullets."
        )
    if structural.missing_sections:
        actions.append(f"Missing sections: {', '.join(structural.missing_sections)}")
    if keyword.missing_preferred:
        top = keyword.missing_preferred[:3]
        actions.append(f"Preferred keywords absent: {', '.join(top)}")
    return actions


# ─── Public API ───────────────────────────────────────────────────────────────

def score(
    resume_source: str,
    jd_text: str,
) -> ATSResult:
    """Score a resume against a job description.

    Args:
        resume_source: raw text, file path (.pdf or .tex), or LaTeX string.
        jd_text: raw job description text.

    Returns:
        ATSResult with full breakdown.
    """
    resume_text = parse_resume(resume_source)
    jd_cleaned = clean_jd(jd_text)

    # Validate JD has parseable content
    if len(jd_cleaned.strip()) < 10:
        raise ValueError(
            "Job description is empty or could not be parsed. "
            "Please provide the raw JD text, not just a job title or URL."
        )

    sections = parse_sections(resume_text)
    jd_keywords = extract_keywords(jd_cleaned)

    if not jd_keywords:
        raise ValueError(
            "No recognisable keywords could be extracted from the job description. "
            "The JD may be too generic or missing technical requirements."
        )

    resume_token_map, token_to_section = _build_resume_token_map(sections)

    keyword_result = _score_keywords(jd_keywords, resume_token_map, token_to_section)
    structural_result = _score_structural(sections)
    semantic_result = _score_semantic(resume_text, jd_cleaned)
    hard_req_result = check_hard_requirements(jd_cleaned, resume_text)

    total = round(
        keyword_result.score + structural_result.score + semantic_result.score,
        1,
    )
    total = min(total, 100.0)

    result = ATSResult(
        total_score=total,
        grade=_grade(total),
        keyword=keyword_result,
        structural=structural_result,
        semantic=semantic_result,
        hard_requirements=hard_req_result,
        top_actions=_top_actions(keyword_result, structural_result, hard_req_result),
    )
    return result
