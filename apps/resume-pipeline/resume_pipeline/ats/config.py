"""Scoring weights and thresholds."""

# Component weights — must sum to 100
KEYWORD_WEIGHT = 50       # keyword match score (section-weighted, synonym-aware)
STRUCTURAL_WEIGHT = 30    # action verbs + quantification + section completeness
SEMANTIC_WEIGHT = 20      # context richness (impact density, bullet depth, seniority)

# Hard vs soft skill weighting within keyword scoring.
# Hard skills (tech tools, languages, frameworks) carry full weight.
# Soft skills (collaboration, leadership) carry reduced weight — ATS systems
# weight them less as they're near-universal in JDs and easy to game.
HARD_SKILL_KEYWORD_MULTIPLIER = 1.0
SOFT_SKILL_KEYWORD_MULTIPLIER = 0.4

# Section weights for keyword matching (Skills section matters most)
SECTION_WEIGHTS: dict[str, float] = {
    "skills": 3.0,
    "technical skills": 3.0,
    "technical skill set": 3.0,
    "experience": 2.0,
    "work experience": 2.0,
    "employment": 2.0,
    "summary": 1.5,
    "professional summary": 1.5,
    "objective": 1.5,
    "professional development": 1.2,
    "education": 1.0,
    "projects": 1.5,
    "certifications": 1.5,
    "default": 1.0,
}

# Keyword importance tiers — matched by JD position heuristics
REQUIRED_KEYWORD_MULTIPLIER = 2.0    # in first 30% of JD or in "requirements" section
PREFERRED_KEYWORD_MULTIPLIER = 1.0   # in "preferred" / "nice to have" section
NICE_TO_HAVE_MULTIPLIER = 0.5        # in optional/bonus section

# Structural scoring thresholds
ACTION_VERB_SCORE_MAX = 10
QUANTIFICATION_SCORE_MAX = 10
SECTION_COMPLETENESS_SCORE_MAX = 10

# Quantification scaling factor: a resume where 67% of bullets have numbers
# earns full marks (1.0 / 0.67 ≈ 1.5). Adjust to raise or lower the bar.
QUANTIFICATION_SCALE = 1.5

# Section-based partial-credit fractions for keyword matching.
# A keyword found only in Education gets 30% credit; in Skills = 100%.
# Keys are SECTION_WEIGHTS values, sorted highest to lowest.
KEYWORD_SECTION_CREDIT: dict[str, float] = {
    "skills":       1.00,  # Skills / Technical Skills
    "experience":   0.85,  # Work Experience
    "projects":     0.80,
    "certifications": 0.75,
    "summary":      0.70,
    "professional development": 0.60,
    "education":    0.30,  # keyword in education is near-meaningless to ATS
    "default":      0.50,
}

# Required sections for full section_completeness score
REQUIRED_SECTIONS = {"experience", "skills", "education", "summary"}

# Score bands (mirrors Jobscan-style labels)
EXCELLENT_THRESHOLD = 80
GOOD_THRESHOLD = 60
FAIR_THRESHOLD = 40
