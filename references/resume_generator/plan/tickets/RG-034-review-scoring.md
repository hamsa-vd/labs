# RG-034 — Review rubric and scoring service

**Epic:** D — Pipeline · **Depends on:** RG-030 · **Estimate:** S · **Labels:** pipeline, api

## Product requirement

**Problem.** The human-reviewer score is the product's other headline number. In v1 it is a
weighted rubric computed in `scoring.py` from category scores the reviewer model returns.

**User story.** As a user I see not just an overall score but the eight weighted categories
behind it, so I know what to fix.

**Acceptance criteria**
- The overall score is reproducible from the category scores shown.
- A reviewer response missing a category degrades gracefully — that category scores zero and is
  reported as missing, rather than the run failing.
- The category weights are visible in the UI.

## Technical plan

### Files
```
apps/api/resume_api/pipeline/scoring.py     ← v1 scoring.py, verbatim
apps/api/tests/test_scoring.py              ← v1, verbatim
packages/contracts/src/rubric.ts            weights mirrored for display
```

### The rubric — do not change these weights
Resume: jd_skills_keyword_match .20 · role_domain_relevance .15 ·
achievement_evidence_strength .15 · credibility_source_truth_compliance .15 ·
single_page_compliance .15 · targeting_brief_compliance .10 ·
ats_latex_formatting_safety .05 · recruiter_impression_seniority_alignment .05

Cover letter: jd_company_alignment .30 · evidence_relevance .25 · motivation_domain_fit .20 ·
clarity_tone .15 · credibility_no_fabrication .10

### Steps
1. Copy `scoring.py` across with no edits. `weighted_score` clamps each category to 0–10, treats
   a missing category as 0, and reports it in `missing_categories` — keep all of that.
2. Mirror the weights into `packages/contracts/src/rubric.ts` for the result view, and add a test
   asserting the TS weights sum to 1.0 and match the Python dict key-for-key. Two copies of a
   constant is acceptable only with a test that keeps them honest.

### Reuse from v1
`resume_agent/scoring.py` and `tests/test_scoring.py` — verbatim, both.

### Tests
- Ported test passes unchanged.
- Python and TS rubrics agree (key set and weights).

### Definition of done
Both green.

### Out of scope
Rendering (RG-043).
