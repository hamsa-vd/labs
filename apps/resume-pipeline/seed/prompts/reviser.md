You are making surgical, measurable fixes to the resume. You are not rewriting from scratch. Every change must directly resolve a specific must-fix item from the review, or target a low-scoring category. The cover letter will be regenerated fresh from the revised resume — do not produce it here.

Return only the complete revised resume LaTeX. Do not wrap in Markdown.

---

Company: {{COMPANY_NAME}}
Job title: {{JOB_TITLE}}

Targeting brief (original strategy — do not contradict it):
{{TARGETING_BRIEF}}

Job description:
{{JD_TEXT}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

Current resume LaTeX:
{{RESUME_TEX}}

---

SCORE CONTEXT — understand where the resume is weak before making changes:

Current score: {{RESUME_SCORE}} / 10 (target to pass: {{RESUME_TARGET_SCORE}})

Category scores (the weighted rubric that determines the overall score):
{{RESUME_CATEGORY_SCORES}}

Any category below 9.0 is underperforming. Focus your changes on the lowest-scoring categories first. The must_fix items below are your primary instructions, but if must_fix is sparse, use the category scores above to identify what to improve independently.

---

MUST-FIX ITEMS — address every single one. These are not suggestions:

{{RESUME_MUST_FIX}}

---

Fix-resolution audit from previous pass (if present — do not repeat items marked "made_worse"):
{{FIX_RESOLUTION_MATRIX}}

---

ATS CHECKER RESULTS — mechanical keyword/structural gaps to address:

Top ATS actions (address these alongside the must-fix items above):
{{ATS_TOP_ACTIONS}}

Unmet hard requirements flagged by ATS (only fix if genuinely absent — do not fabricate):
{{ATS_UNMET_HARD_REQUIREMENTS}}

---

Rules:
- Address ALL must-fix items. If you cannot address one without fabrication, explain why in a LaTeX comment and leave the original.
- For any category scoring below 9.0 that has no must_fix item, make at least one targeted improvement based on what that category measures:
  * jd_skills_keyword_match: integrate missing JD keywords into bullets or skills section with grounded evidence
  * role_domain_relevance: sharpen framing of experience to better match the role domain
  * achievement_evidence_strength: replace weak/vague bullets with quantified, outcome-focused language from source of truth
  * credibility_source_truth_compliance: remove or qualify any claim not directly supported by source of truth
  * targeting_brief_compliance: align tone, seniority verbs, and keyword strategy with the targeting brief
  * single_page_compliance: enforce bullet caps per section
  * ats_latex_formatting_safety: fix any ATS-unsafe LaTeX constructs
  * recruiter_impression_seniority_alignment: adjust seniority signals to match role level
- Do not invent experience, companies, titles, dates, degrees, certifications, projects, or metrics.
- Do not add any claim in forbidden_claims from the targeting brief.
- For learning_signal_keywords in the brief: use adjacent evidence or framing — never fabricate direct expertise.
- Preserve LaTeX validity. Preserve base resume structure and formatting.
- Each change must be traceable to a specific must-fix item or a low-scoring category. Do not make cosmetic changes that do not move the score.
- PAGE BUDGET ENFORCEMENT: Hard caps per section: Professional Summary = prose only (no itemize); most recent role ≤7 bullets; each older role ≤4 bullets; Professional Development ≤3 bullets; total bullets across all sections ≤14. If a must-fix item references page overflow, remove the weakest bullets in over-limit sections. If the resume has significant blank space at the bottom (Education section well above the page bottom), ADD impactful grounded bullets to the most recent role or older roles up to their cap — blank space at the bottom is wasted opportunity. Do not add bullets if the page is already full.

