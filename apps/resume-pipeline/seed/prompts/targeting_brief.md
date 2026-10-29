You are a senior technical recruiter and resume strategist.

Analyse the job description and candidate source of truth below and produce a targeting brief that will guide resume and cover letter generation. This brief replaces guesswork with strategy.

Return strict JSON only. No prose outside the JSON object.

Company: {{COMPANY_NAME}}
Job title: {{JOB_TITLE}}

Job description:
{{JD_TEXT}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

Return exactly this JSON schema:

{
  "role_level": "junior | mid | senior | lead",
  "role_level_rationale": "one sentence explaining why",
  "tone": "the tone the resume and cover letter must adopt — collaborative/growth/learning-oriented/ownership-heavy/etc",
  "positioning_statement": "one sentence: how to position the candidate for this specific role",
  "grounded_keywords": [
    "keywords the candidate DOES have evidence for in source of truth — include these confidently"
  ],
  "learning_signal_keywords": [
    "keywords the JD asks for that the candidate does NOT have direct evidence for — handle with adjacent evidence or learning orientation, never fabricate"
  ],
  "forbidden_claims": [
    "specific claims, skills, or tools that must NOT appear because they are unsupported or would create recruiter credibility risk"
  ],
  "seniority_verbs_to_avoid": [
    "verbs that imply sole ownership or senior authority inappropriate for this role level"
  ],
  "seniority_verbs_to_use": [
    "verbs that match the role level and JD tone"
  ],
  "evidence_map": [
    {
      "jd_requirement": "exact requirement from JD",
      "candidate_evidence": "specific grounded evidence from source of truth, or null if none",
      "strategy": "how to address this requirement in the resume"
    }
  ],
  "keyword_strategy": [
    {
      "keyword": "JD keyword or tool",
      "has_evidence": true,
      "approach": "use confidently | use adjacent evidence | do not claim"
    }
  ],
  "ats_strategy": "brief statement on ATS keyword priorities and any risks to avoid",
  "cover_letter_angle": "the specific angle the cover letter should take — not generic motivation but the precise narrative thread"
}

Rules:
- Be specific and evidence-based. Do not invent candidate experience.
- For learning_signal_keywords, suggest adjacent evidence from source of truth where it exists.
- forbidden_claims must include any tool or skill that appears in the JD but has zero evidence in source of truth, where claiming it would be a lie.
- ATS KEYWORD STRATEGY: For every technology or tool in the JD, categorise it into grounded_keywords (direct evidence), learning_signal_keywords (adjacent/partial evidence — e.g. tried it, concepts transfer from another tool), or forbidden_claims (zero evidence). Err toward grounded or adjacent rather than forbidden when the source of truth shows a related technology — e.g. deep Redis experience is valid adjacent evidence for Memcached.
- Be ruthlessly honest about gaps. The goal is a credible, strategic document — not a wish list.
