You are implementing a pre-approved resume strategy inside a LaTeX template. You are NOT analysing the job or figuring out the role. That work is already done. Your job is precise, disciplined implementation.

Return only a complete LaTeX document. Do not wrap it in Markdown.

---

TARGETING BRIEF (implement this exactly):
{{TARGETING_BRIEF}}

---

Job description:
{{JD_TEXT}}

Selected base resume LaTeX:
{{BASE_RESUME_TEX}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

---

Implementation rules:

STRUCTURE
- Preserve the base resume's documentclass, packages, macros, section order, and formatting exactly.
- Do not change section names, column layout, or spacing commands.
- Output a complete, valid LaTeX document.

CONTENT
- Use the targeting brief's positioning_statement to shape the professional summary.
- Use grounded_keywords confidently throughout skills and bullets.
- For learning_signal_keywords: use adjacent evidence from source of truth, or frame as willingness/exposure. Never fabricate.
- Do not include anything in forbidden_claims. If a forbidden item is in the base resume, remove it.
- Replace seniority_verbs_to_avoid with seniority_verbs_to_use consistently across all bullets.
- Every bullet must map to a specific entry in the evidence_map. If a JD requirement has candidate_evidence, reflect it. If not, do not invent it.
- Follow keyword_strategy exactly: confident for has_evidence=true, adjacent/framed for false, absent for "do not claim".

TONE
- The entire document must match the brief's tone field.
- This is not negotiable. If the brief says "collaborative, learning-oriented," every ownership-heavy or solo-credit phrase must be rewritten.

CREDIBILITY
- Do not invent companies, titles, dates, degrees, certifications, projects, or metrics.
- Do not round up metrics unless source of truth supports the range.
- Do not add skills to the Technical Skills section that are not in grounded_keywords.

PAGE BUDGET — MANDATORY (A4, 0.5in margins, 10pt font = exactly 1 page):
- Professional Summary: 2–3 lines of prose ONLY. Do NOT add a bullet list under the summary paragraph. A prose summary is required; bullets under summary are prohibited.
- Most recent role (longest tenure): TARGET 6–7 bullets (hard cap 7). Fill the space — every strong, JD-relevant bullet backed by source-of-truth evidence should be included.
- Each older role: TARGET 4 bullets (hard cap 4).
- Professional Development section: TARGET 3 bullets (hard cap 3).
- Skills section: fit within 4 dense lines; no line break per skill category unless strictly necessary.
- Education: single header line only; no bullets.
- FILL THE PAGE: Aim to use at least 14 total bullets across all experience/dev sections combined. If you stop well short of the caps with white space remaining at the bottom, add more impactful, grounded bullets — do not leave blank space. A resume that exceeds 1 page is a critical defect; a resume with significant blank space at the bottom is wasted opportunity.
If the 1-page budget cannot be met with these limits, remove the weakest bullets first. Never exceed these per-section bullet caps.

