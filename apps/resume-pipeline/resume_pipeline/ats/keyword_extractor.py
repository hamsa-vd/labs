"""JD keyword extractor — phrase-aware, synonym-normalised.

Extracts single-token and multi-word tech phrases from a job description,
tags each as required/preferred/nice-to-have based on JD structure,
and normalises to canonical forms via the synonym dictionary.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass, field

from resume_pipeline.ats.synonyms import ALIAS_TO_CANONICAL, TECH_SYNONYMS, normalise

# Professional terms not in the tech synonym dictionary but meaningful for ATS
_PROFESSIONAL_TERMS: frozenset[str] = frozenset({
    # Methodologies
    "agile", "scrum", "kanban", "devops", "devsecops",
    # Engineering practices
    "testing", "tdd", "bdd", "code review", "peer review", "pair programming",
    "mentoring", "mentorship", "coaching", "documentation",
    "technical design", "system design",
    # Quality / reliability concepts
    "resiliency", "reliability", "scalability", "observability", "availability",
    "operational excellence", "sla", "slo", "sli",
    "monitoring", "alerting", "logging", "tracing",
    # Architecture patterns
    "microservices", "microservice", "distributed systems",
    "service oriented", "event driven", "event-driven",
    "api design", "api contracts", "rest api", "graphql",
    # Language / runtime concepts
    "object-oriented", "functional", "concurrency", "multithreading",
    "data structures", "algorithms",
    # Deployment
    "ci/cd", "continuous integration", "continuous delivery",
    "version control", "code review",
    # Soft skills that JDs list as requirements
    "collaboration", "leadership", "communication", "mentoring",
})

# Soft skills — same extraction pipeline but awarded lower weight in keyword scoring.
# These terms are near-universal in JDs and easy to game, so real ATS systems
# weight them less than hard technical skills.
_SOFT_SKILLS: frozenset[str] = frozenset({
    "collaboration", "leadership", "communication", "mentoring", "mentorship",
    "coaching", "teamwork", "interpersonal", "presentation",
    "problem solving", "critical thinking", "time management",
    "stakeholder management", "cross-functional", "cross functional",
    "agile", "scrum", "kanban",  # methodologies — borderline soft/hard
    "operational excellence",
})

# Common inflection aliases for professional terms — inflected form → canonical
_PROF_INFLECTIONS: dict[str, str] = {
    # mentoring / mentor
    "mentor": "mentoring", "mentored": "mentoring", "mentors": "mentoring",
    # testing
    "tested": "testing", "test": "testing",
    # scalability
    "scalable": "scalability",
    # reliability
    "reliable": "reliability",
    # collaboration
    "collaborate": "collaboration", "collaborated": "collaboration", "collaborates": "collaboration",
    "collaborative": "collaboration",
    # observability
    "observable": "observability",
    # availability
    "available": "availability",
    # monitoring
    "monitor": "monitoring", "monitored": "monitoring",
    # alerting
    "alert": "alerting", "alerted": "alerting",
    # documentation
    "document": "documentation", "documented": "documentation",
    # logging
    "log": "logging", "logged": "logging",
    # tracing
    "trace": "tracing", "traced": "tracing",
}


@dataclass
class JDKeyword:
    canonical: str          # normalised canonical form
    original: str           # as extracted from JD
    importance: str         # "required" | "preferred" | "nice_to_have"
    importance_weight: float
    is_phrase: bool         # True if multi-word
    is_soft_skill: bool = False  # True for collaboration/leadership/etc. (lower ATS weight)


# Importance weights
_IMPORTANCE_WEIGHTS = {
    "required": 2.0,
    "preferred": 1.0,
    "nice_to_have": 0.5,
}

# JD section signals that indicate required vs preferred keywords
_REQUIRED_SIGNALS = re.compile(
    r"\b(require[sd]?|must\s+have|minimum|essential|mandatory|qualification[s]?|"
    r"you\s+(will|must|should)|we\s+(require|expect|need))\b",
    re.I,
)
_PREFERRED_SIGNALS = re.compile(
    r"\b(prefer(red)?|ideal(ly)?|desirable|advantage|asset|"
    r"strong\s+background|solid\s+(experience|knowledge))\b",
    re.I,
)
_NICE_TO_HAVE_SIGNALS = re.compile(
    r"\b(nice\s+to\s+have|bonus|plus|optional|familiarity|exposure|"
    r"experience\s+with|knowledge\s+of)\b",
    re.I,
)

# English stopwords — not useful as ATS keywords
_STOPWORDS: frozenset[str] = frozenset({
    # Articles / prepositions / conjunctions
    "a", "an", "the", "and", "or", "but", "nor", "for", "yet", "so",
    "in", "on", "at", "to", "by", "of", "up", "as", "is", "it",
    "its", "be", "do", "if", "we", "us", "our", "you", "your",
    "they", "their", "with", "from", "into", "onto", "upon",
    "about", "above", "after", "along", "among", "around",
    "before", "behind", "below", "beneath", "beside", "between",
    "beyond", "during", "except", "inside", "near", "off",
    "outside", "over", "past", "since", "through", "throughout",
    "under", "until", "within", "without", "across", "against",
    "along", "amid", "among", "behind", "below", "beneath",
    # Common verbs (uninformative as standalone keywords)
    "are", "was", "were", "has", "have", "had", "been", "being",
    "will", "would", "should", "could", "may", "might", "can",
    "shall", "must", "need", "use", "used", "using",
    "include", "including", "includes", "such",
    # Generic JD adjectives/nouns (not signals of specific tech or skill)
    "team", "teams", "candidate", "bonus", "plus",
    "responsibility", "responsibilities", "knowledge", "mindset",
    "passion", "communication", "platform", "product", "products",
    "experience", "experiences", "role", "roles", "position",
    "looking", "hiring", "join", "ability", "work", "working",
    "skill", "skills", "background", "year", "years",
    "strong", "good", "excellent", "great", "proven", "solid",
    "understanding", "familiar", "proficient", "expertise", "deep",
    "new", "large", "small", "fast", "high", "low", "key",
    "real", "full", "best", "other", "related", "various",
    "based", "driven", "oriented", "focused", "facing",
    "able", "key", "main", "top", "most", "more", "many",
    "all", "any", "each", "both", "few", "some",
    # JD filler phrases (single tokens)
    "et", "al", "eg", "ie", "etc", "also", "well", "when",
    "how", "what", "which", "who", "this", "that", "these",
    "those", "then", "than", "very", "often", "always",
    "apply", "applying", "applies",
    "make", "makes", "making", "ensure", "ensuring",
    "help", "helps", "helping", "provide", "provides",
    "build", "building", "create", "creating", "develop",
    "improving", "manage", "managing", "driving",
    "collaborating", "partnering", "working", "supporting",
    # Single characters that slip through
    "s", "d", "x", "m",
})

# Generic JD filler words that are not useful ATS signals even if not stopwords
_SKIP_TERMS: frozenset[str] = _STOPWORDS | frozenset({
    "familiarity", "demonstrated", "proficiency", "proficient",
    "programs", "procedures", "variety", "creatively", "recommend",
    "maintain", "applications", "related", "recommend", "research",
    "identify", "areas", "improvement", "solutions",
})


_REQUIRED_HEADER = re.compile(
    r"^(requirements?|must\s+have|minimum|essential|mandatory|qualifications?|"
    r"what\s+you.ll\s+(need|bring)|basic\s+qualifications?)\s*:?\s*$",
    re.I,
)
_PREFERRED_HEADER = re.compile(
    r"^(preferred|ideal(ly)?|desirable|advantage|asset|"
    r"preferred\s+qualifications?|what\s+would\s+be\s+great)\s*:?\s*$",
    re.I,
)
_NICE_HEADER = re.compile(
    r"^(nice\s+to\s+have|bonus|optional|good\s+to\s+have|additional)\s*:?\s*$",
    re.I,
)


def _split_into_paragraphs(text: str) -> list[tuple[str, str]]:
    """Return (line_text, importance_tag) pairs with line-level granularity.

    Handles both double-newline paragraph breaks AND inline section headers
    like 'Requirements:', 'Preferred:', 'Nice to have:' on their own line.
    """
    lines = text.splitlines()
    result: list[tuple[str, str]] = []
    current_importance = "required"  # default: start of JD is usually required context

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line is a section header that shifts importance
        if _REQUIRED_HEADER.match(stripped):
            current_importance = "required"
            continue
        if _PREFERRED_HEADER.match(stripped):
            current_importance = "preferred"
            continue
        if _NICE_HEADER.match(stripped):
            current_importance = "nice_to_have"
            continue

        # Detect inline signals within a line.
        # When multiple signals match on the same line, specificity wins:
        # nice_to_have > preferred > required. JD authors write "preferred" or
        # "nice to have" to soften a requirement — honouring that avoids
        # over-penalising candidates for missing truly optional skills.
        if _NICE_TO_HAVE_SIGNALS.search(stripped):
            tag = "nice_to_have"
        elif _PREFERRED_SIGNALS.search(stripped):
            tag = "preferred"
        elif _REQUIRED_SIGNALS.search(stripped):
            tag = "required"
        else:
            tag = current_importance

        result.append((stripped, tag))

    return result


def _build_phrase_patterns() -> list[tuple[re.Pattern[str], str]]:
    """Build regex patterns for all known multi-word tech phrases."""
    patterns: list[tuple[re.Pattern[str], str]] = []
    for canonical, aliases in TECH_SYNONYMS.items():
        all_forms = [canonical] + aliases
        for form in all_forms:
            if " " in form or "/" in form or "." in form:
                escaped = re.escape(form)
                # Allow flexible spacing/punctuation
                escaped = re.sub(r"\\ ", r"[\\s\\-/.]?", escaped)
                try:
                    patterns.append((
                        re.compile(r"\b" + escaped + r"\b", re.I),
                        canonical,
                    ))
                except re.error:
                    pass
    # Sort longer patterns first (greedy matching)
    patterns.sort(key=lambda x: -len(x[1]))
    return patterns


_PHRASE_PATTERNS = _build_phrase_patterns()


def _extract_phrases(text: str) -> list[str]:
    """Find all multi-word tech phrases in text, return canonical forms."""
    found: list[str] = []
    for pattern, canonical in _PHRASE_PATTERNS:
        if pattern.search(text):
            found.append(canonical)
    return found


_ALL_KNOWN = None  # lazy init


def _all_known_terms() -> frozenset[str]:
    global _ALL_KNOWN
    if _ALL_KNOWN is None:
        _ALL_KNOWN = (
            frozenset(ALIAS_TO_CANONICAL.keys())
            | _PROFESSIONAL_TERMS
            | frozenset(_PROF_INFLECTIONS.keys())
        )
    return _ALL_KNOWN


def _stems(token: str) -> list[str]:
    """Return candidate stem forms to check against known vocabulary."""
    variants: list[str] = [token]
    # -ing → base (mentoring → mentor, testing → test)
    if token.endswith("ing") and len(token) > 5:
        variants.append(token[:-3])      # mentoring → mentor
        variants.append(token[:-3] + "e")  # developing → develope (close enough)
    # -ed → base (mentored → mentor)
    if token.endswith("ed") and len(token) > 4:
        variants.append(token[:-2])      # mentored → mentor
        variants.append(token[:-1])      # tested → teste → test doesn't work, but mentored→mentor does
    # -ity → base (scalability → scalab → not great, but worth trying)
    # -tion → base
    if token.endswith("tion") and len(token) > 6:
        variants.append(token[:-4])
    # -ment → base
    if token.endswith("ment") and len(token) > 6:
        variants.append(token[:-4])
    return variants


def _lookup_known(token: str) -> str | None:
    """Return canonical form if token (or a stem/inflection) is in known vocabulary.

    Priority order:
    1. Explicit professional term inflection table (e.g. mentored → mentoring)
    2. Synonym alias → canonical (e.g. cicd → ci/cd)
    3. Direct match in professional terms
    4. Stem-based fallback
    """
    # 1. Check explicit inflection table first (mentored → mentoring, scalable → scalability)
    if token in _PROF_INFLECTIONS:
        return _PROF_INFLECTIONS[token]

    # 2. Synonym alias lookup
    canonical = normalise(token)
    if canonical != token and canonical in (frozenset(ALIAS_TO_CANONICAL.keys()) | _PROFESSIONAL_TERMS):
        return canonical
    if token in ALIAS_TO_CANONICAL:
        return ALIAS_TO_CANONICAL[token]

    # 3. Direct professional term match
    if token in _PROFESSIONAL_TERMS:
        return token
    if canonical in _PROFESSIONAL_TERMS:
        return canonical

    # 4. Stem-based fallback
    for stem in _stems(token):
        if stem in _PROF_INFLECTIONS:
            return _PROF_INFLECTIONS[stem]
        stem_canonical = normalise(stem)
        if stem_canonical in _PROFESSIONAL_TERMS:
            return stem_canonical
        if stem in _PROFESSIONAL_TERMS:
            return stem
        if stem_canonical in ALIAS_TO_CANONICAL:
            return ALIAS_TO_CANONICAL[stem_canonical]
        if stem in ALIAS_TO_CANONICAL:
            return ALIAS_TO_CANONICAL[stem]
    return None


def _extract_single_tokens(text: str) -> list[str]:
    """Extract individual tech keywords from text — restricted to known vocabulary.

    Only tokens in the synonym dictionary (ALIAS_TO_CANONICAL) or in our
    curated professional terms list are kept. This prevents generic English
    words like 'test', 'following', 'customer' from polluting keyword lists.
    """
    cleaned = re.sub(r"[^\w\s\-/#+.]", " ", text)
    tokens = cleaned.lower().split()
    result: list[str] = []
    for token in tokens:
        token = token.strip(string.punctuation)
        if not token or len(token) < 2 or token.isdigit():
            continue
        if token in _SKIP_TERMS:
            continue
        found = _lookup_known(token)
        if found:
            result.append(found)
    return result


# Patterns to detect unknown tech terms not in the whitelist vocabulary

# Catches: GraphQL (G+raph+Q), NextJS (N+ext+J), OpenTelemetry (O+pen+T)
# AND: iOS (i+O), eCommerce (e+C) — lowercase-start then uppercase transition
_CAMEL_CASE_RE = re.compile(r"[A-Z][a-z]+[A-Z]|[a-z]+[A-Z]")

# Letter-only ALL-CAPS acronyms: HTMX, GRPC, WASM, REST, SOAP (2–6 chars)
_ALL_CAPS_ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")

# Digit-suffixed tech names: HTML5, CSS3, ES6, Vue3, HTTP2, OAuth2, C++, C#
# Captures letters followed by digits (or punctuation like ++/#)
_DIGIT_SUFFIX_TECH_RE = re.compile(r"^[A-Z][A-Za-z]{1,8}[\d]+$|^[A-Z][A-Za-z]?[+#]{1,2}$")

# Compound tech names ending in known tech suffixes (requires a non-empty prefix)
# e.g. nodejs, mongodb, reactjs, rabbitmq — but NOT standalone "js" or "sql"
_TECH_COMPOUND_RE = re.compile(r"(?i)^.{2,}(?:js|db|sql|ql|lang|mq|hub|ops|io)$")

# Explicit standalone tech shorthands that don't have a prefix but are meaningful.
# These are only used when NOT already in the known whitelist vocabulary.
_TECH_STANDALONE: frozenset[str] = frozenset({
    "js", "ts", "py", "go", "rs",           # language shorthands
    "sql", "nosql",                           # query shorthands
    "ios", "pwa", "ssr", "spa",              # platform/pattern shorthands
    "grpc", "wasm", "htmx",                  # protocol/framework shorthands
    "iac", "sre", "slo", "sli",             # ops shorthands not in whitelist
})


def _extract_unknown_tech(text: str) -> list[str]:
    """Hybrid second-pass: detect tech terms not in the whitelist vocabulary.

    Heuristics (in priority order):
    1. CamelCase: `[A-Z][a-z]+[A-Z]` (GraphQL, NextJS) OR `[a-z]+[A-Z]` (iOS)
    2. ALL_CAPS acronyms 2–6 letters (HTMX, GRPC, WASM)
    3. Digit-suffix tech: HTML5, CSS3, ES6, Vue3, C++, C# (letters + digits/punctuation)
    4. Compound names ending in tech suffixes (nodejs, mongodb, reactjs)
    5. Explicit standalone shorthands (js, sql, ios, grpc — not already in whitelist)

    These are returned as-is (lowercased) for use as nice_to_have keywords.
    Any terms already in the known vocabulary are skipped (handled by primary pass).
    """
    known = _all_known_terms()
    found: list[str] = []
    seen: set[str] = set()

    # Tokenize preserving digits, +, # so HTML5/C++/C# are captured as whole tokens
    # Use a pattern that allows dots mid-word (node.js) but strips trailing punctuation
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-+#.]*", text)
    for raw_word in words:
        word = raw_word.rstrip(".,-;:")  # strip trailing sentence punctuation
        lower = word.lower()
        if lower in seen or lower in _SKIP_TERMS or len(lower) < 2:
            continue
        if lower in known or normalise(lower) in known:
            continue  # already in whitelist — primary pass handles it

        is_unknown_tech = (
            _CAMEL_CASE_RE.search(word)                          # GraphQL, iOS, NextJS
            or (_ALL_CAPS_ACRONYM_RE.fullmatch(word) and len(word) >= 2)  # HTMX, GRPC
            or bool(_DIGIT_SUFFIX_TECH_RE.match(word))           # HTML5, CSS3, ES6, C++
            or bool(_TECH_COMPOUND_RE.match(lower))              # nodejs, mongodb
            or lower in _TECH_STANDALONE                         # js, sql, ios, grpc
        )
        if is_unknown_tech:
            found.append(lower)
            seen.add(lower)

    return found


def extract_keywords(jd_text: str) -> list[JDKeyword]:
    """Extract all keywords from JD, deduplicated and tagged with importance."""
    paragraphs = _split_into_paragraphs(jd_text)
    seen: dict[str, JDKeyword] = {}

    for para_text, importance in paragraphs:
        weight = _IMPORTANCE_WEIGHTS[importance]

        # Multi-word phrases first (they take priority)
        for canonical in _extract_phrases(para_text):
            if canonical not in seen or _IMPORTANCE_WEIGHTS[seen[canonical].importance] < weight:
                seen[canonical] = JDKeyword(
                    canonical=canonical,
                    original=canonical,
                    importance=importance,
                    importance_weight=weight,
                    is_phrase=True,
                    is_soft_skill=canonical in _SOFT_SKILLS,
                )

        # Single tokens
        for canonical in _extract_single_tokens(para_text):
            if canonical not in seen:
                seen[canonical] = JDKeyword(
                    canonical=canonical,
                    original=canonical,
                    importance=importance,
                    importance_weight=weight,
                    is_phrase=False,
                    is_soft_skill=canonical in _SOFT_SKILLS,
                )

        # Hybrid second-pass: unknown tech terms not in whitelist vocabulary
        for unknown in _extract_unknown_tech(para_text):
            if unknown not in seen:
                seen[unknown] = JDKeyword(
                    canonical=unknown,
                    original=unknown,
                    importance="nice_to_have",
                    importance_weight=_IMPORTANCE_WEIGHTS["nice_to_have"],
                    is_phrase=False,
                    is_soft_skill=False,
                )

    return list(seen.values())
