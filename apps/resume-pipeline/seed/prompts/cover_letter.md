Generate a tailored LaTeX cover letter for this job application.

Return only a complete LaTeX document. Do not wrap it in Markdown.

Company: {{COMPANY_NAME}}
Job title: {{JOB_TITLE}}

Targeting brief (follow the cover_letter_angle and tone exactly):
{{TARGETING_BRIEF}}

Job description:
{{JD_TEXT}}

Tailored resume LaTeX (final version after all revisions):
{{RESUME_TEX}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

Revision history (what was strengthened in the resume — use this to inform the narrative):
{{FIX_RESOLUTION_SUMMARY}}

Instructions:
- Open with the cover_letter_angle from the targeting brief — not a generic statement.
- Adopt the tone from the brief exactly.
- Do not claim anything in forbidden_claims from the brief.
- For learning_signal_keywords: use adjacent evidence or express genuine openness to learn. Do not fabricate expertise.
- Do not invent experience, dates, projects, or motivations.
- Ground every claim in the tailored resume and source of truth.
- If the revision history is not "none", use items with status "fixed" or "partial" as signals of what was emphasised in the resume — mirror those themes in the cover letter without repeating bullet text verbatim.
- Keep it to roughly one page.
