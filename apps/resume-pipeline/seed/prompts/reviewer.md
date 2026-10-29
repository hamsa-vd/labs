Review the resume against the JD, targeting brief, and source of truth. The cover letter is not reviewed — it is regenerated alongside any resume revision.

Return strict JSON only. Do not include Markdown or prose outside JSON.

Company: {{COMPANY_NAME}}
Job title: {{JOB_TITLE}}
Revision number: {{REVISION_COUNT}}

Targeting brief (the strategy that was meant to guide generation):
{{TARGETING_BRIEF}}

Job description:
{{JD_TEXT}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

Must-fix items from previous review (populated only on revision passes):
{{PREVIOUS_MUST_FIX}}

Resume LaTeX:
{{RESUME_TEX}}

JSON schema:

{
  "resume": {
    "category_scores": {
      "jd_skills_keyword_match": 0,
      "role_domain_relevance": 0,
      "achievement_evidence_strength": 0,
      "credibility_source_truth_compliance": 0,
      "ats_latex_formatting_safety": 0,
      "recruiter_impression_seniority_alignment": 0,
      "targeting_brief_compliance": 0,
      "single_page_compliance": 0
    },
    "verdict": "pass|fail",
    "brutal_recruiter_opinion": "",
    "must_fix": [],
    "nice_to_have": [],
    "ats_risks": [],
    "missing_keywords": [],
    "credibility_risks": [],
    "fix_resolution": [
      {
        "must_fix_item": "exact text of the must-fix from previous review",
        "status": "fixed | partial | not_fixed | made_worse",
        "evidence": "what you see in the document that supports this status"
      }
    ]
  }
}

Rules:
- Category scores: 0–10, no arithmetic, be strict and realistic.
- targeting_brief_compliance: how well did the resume follow the targeting brief's tone, forbidden_claims, seniority_verbs, and keyword_strategy?
- single_page_compliance: score based on page-budget analysis of the LaTeX. Count total itemize bullets across ALL sections. Hard caps: (a) Professional Summary MUST be prose only — any \begin{itemize} under the summary is a violation; (b) most recent role must have ≤7 bullets; (c) each older role must have ≤4 bullets; (d) Professional Development must have ≤3 bullets; (e) total bullets across all sections must be ≤14. Underuse is also penalised: if total bullets across experience+dev sections are ≤9 (leaving significant blank space at the bottom of the page), deduct 2 points and add a must_fix item instructing the reviser to add grounded bullets to reach at least 12 total. Score: 10 = compliant AND uses ≥12 total bullets; 7–9 = minor over/under by 1–2 bullets; 4–6 = summary has bullet list, a role is over cap by 3+, or severe underuse (≤7 total bullets); 0–3 = major overflow (total >17) or multiple sections over cap. If single_page_compliance < 7, add a must_fix item listing exactly which sections have issues and the required caps.
- fix_resolution: populate only when previous_must_fix is non-empty. For each item, assess status honestly — "made_worse" if the revision created a new credibility problem while trying to address the issue.
- Be strict. Penalise: weak JD match, vague evidence, unsupported claims, ATS issues, formatting changes, brief non-compliance, page overflow.
- Do not do arithmetic. The application calculates weighted scores.
- MUST-FIX GENERATION IS MANDATORY: For every category you score below 9.0, you MUST include at least one specific, actionable must_fix item. These items are the primary signal used by the reviser — vague or missing must_fix items make revision impossible. Each must_fix item must: (a) name the exact category it addresses, (b) cite specific text, missing keywords, or weak bullets from the resume LaTeX, (c) state precisely what change is needed. Do not write generic feedback. Write instructions a developer could execute mechanically.
- ATS KEYWORD AUDIT — jd_skills_keyword_match scoring rules:
  * Extract every concrete technology, tool, methodology, and domain term from the JD (languages, frameworks, databases, platforms, practices).
  * For each one, check whether it appears literally in the resume text (exact string match, case-insensitive).
  * Count how many are present vs absent. Score: 10 = ≥90% present; 9 = 80–89%; 8 = 70–79%; 7 = 60–69%; below 7 = <60%.
  * Every absent keyword that the candidate HAS grounded evidence for in the source of truth is a must_fix item — specify exactly where in the resume to add it and how.
  * Absent keywords with NO source of truth evidence go into missing_keywords only (do not fabricate).
  * Do not award jd_skills_keyword_match above 8 if any keyword with grounded evidence is absent from the resume text.

