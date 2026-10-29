# WP2 — Deterministic core

Discharges RG-020 (render half), RG-021 (selection half), RG-022 (render half), RG-033, RG-034.

Everything here is pure: no database, no network, no LLM, no clock, no filesystem beyond reading
a passed-in string. The same inputs always produce the same outputs. That is what makes this the
package to build first and the one whose tests are worth the most.

Root: `apps/resume-pipeline/`. Run with `make test`.

---

## 1. `resume_pipeline/pipeline/scoring.py`

**Port verbatim** from `Resume/resume_generator/resume_agent/scoring.py`. Change nothing but the
module docstring. It already exports everything needed:

```python
RESUME_RUBRIC: dict[str, float]        # 8 categories, weights sum to 1.0
COVER_LETTER_RUBRIC: dict[str, float]  # 5 categories, weights sum to 1.0

@dataclass(frozen=True)
class ScoreResult:
    score: float
    missing_categories: list[str]

def score_resume_review(review: dict[str, Any]) -> ScoreResult
def score_cover_letter_review(review: dict[str, Any]) -> ScoreResult
def weighted_score(category_scores: dict[str, Any], rubric: dict[str, float]) -> ScoreResult
def attach_scores(review_payload: dict[str, Any]) -> dict[str, Any]
```

Behaviour that must hold:
- `weighted_score` clamps each category to 0.0–10.0 inclusive; a non-numeric or unparseable value
  clamps to 0.0 rather than raising.
- A category absent from `category_scores` contributes 0.0 and its key appears in
  `missing_categories`.
- The returned `score` is rounded to 2 decimal places.
- `attach_scores` does not mutate its argument. It returns a new dict where `payload["resume"]`
  and `payload["cover_letter"]`, when present and dict-valued, each gain a `score` float and a
  `missing_score_categories` list. A key that is absent, or present but not a dict, is left alone.

The exact weights, which must not change:

| Resume category | Weight |
| --- | --- |
| jd_skills_keyword_match | 0.20 |
| role_domain_relevance | 0.15 |
| achievement_evidence_strength | 0.15 |
| credibility_source_truth_compliance | 0.15 |
| single_page_compliance | 0.15 |
| targeting_brief_compliance | 0.10 |
| ats_latex_formatting_safety | 0.05 |
| recruiter_impression_seniority_alignment | 0.05 |

| Cover letter category | Weight |
| --- | --- |
| jd_company_alignment | 0.30 |
| evidence_relevance | 0.25 |
| motivation_domain_fit | 0.20 |
| clarity_tone | 0.15 |
| credibility_no_fabrication | 0.10 |

---

## 2. `resume_pipeline/pipeline/budgets.py`

Replaces v1's `resume_agent/config.py` constants. No filesystem paths — v2 has none.

```python
MIN_JD_TEXT_LENGTH: int = 300
ATS_PASS_THRESHOLD: int = 80
RESUME_PASS_SCORE: float = 8.0
COVER_LETTER_PASS_SCORE: float = 8.0
MAX_REVISIONS: int = 1
MAX_TOTAL_LLM_CALLS: int = 16
MAX_OPENAI_CALLS: int = 4
MAX_CLAUDE_CALLS: int = 8
MAX_REVISION_CALLS: int = 5
RECURSION_LIMIT: int = 25

@dataclass(frozen=True)
class RunBudget:
    max_revisions: int = MAX_REVISIONS
    resume_pass_score: float = RESUME_PASS_SCORE
    ats_pass_threshold: int = ATS_PASS_THRESHOLD
    max_total_llm_calls: int = MAX_TOTAL_LLM_CALLS
    max_openai_calls: int = MAX_OPENAI_CALLS
    max_claude_calls: int = MAX_CLAUDE_CALLS
    max_revision_calls: int = MAX_REVISION_CALLS

SERVER_CEILINGS: dict[str, int | float]

def clamp_budget(requested: Mapping[str, Any]) -> RunBudget: ...
```

`COVER_LETTER_PASS_SCORE` exists because v1's `build_persist_warnings` references it without
importing it — a latent `NameError` on the cover-letter warning branch. RG-030 calls for fixing it
by defining it here. 8.0 mirrors the resume threshold.

`clamp_budget` takes a partial mapping of user settings and returns a `RunBudget` where:
- an absent key takes the default above;
- a present key is clamped to `SERVER_CEILINGS` when it exceeds it, never honoured above it;
- a present key below 1 (or below 0.0 for scores) is clamped up to the minimum;
- an unparseable value falls back to the default rather than raising.

Ceilings, from RG-031's table: `max_revisions` 5, `max_total_llm_calls` 30, `max_openai_calls` 10,
`max_claude_calls` 16, `max_revision_calls` 10, `resume_pass_score` 9.5, `ats_pass_threshold` 95.

---

## 3. `resume_pipeline/pipeline/template_select.py`

**Port** from `resume_agent/resume_selection.py`. The single change: it must not import
`storage.template_options()` (there is no filesystem template registry in v2). Define the five
keys locally as `TEMPLATE_KEYS = ["frontend", "backend-java", "backend-python", "fullstack",
"senior-engineer"]` and use that wherever v1 used `template_options()`.

```python
@dataclass(frozen=True)
class TemplateRecommendation:
    template_key: str
    scores: dict[str, int]
    matched_terms: dict[str, list[str]]
    reason: str

def recommend_template(jd_text: str, job_title: str = "") -> TemplateRecommendation: ...
```

`KEYWORD_RULES`, `EXPLICIT_TITLE_BOOSTS`, `TIE_BREAK_ORDER`, `_count_term`, `_term_weight`,
`_apply_mixed_fullstack_bonus`, `_build_reason` all port unchanged. The scoring behaviour that
must hold:
- A term is counted only on a word boundary: `java` matches in `Java 17` but not in `javascript`.
- A term containing a space, a dot, or a hyphen weighs 3; any other term weighs 2.
- A title matching an `EXPLICIT_TITLE_BOOSTS` pattern adds that boost to that key.
- When frontend signals and backend signals both appear, `fullstack` gains 25.
- Ties resolve by `TIE_BREAK_ORDER`, earliest wins.
- `reason` names the selected key and up to eight matched terms, or states that no stronger role
  signal was found.

`Resume/resume_generator/tests/test_resume_selection.py` is the regression net. A copy sits at
`tests/fixtures/v1/test_resume_selection.py` for reference.

---

## 4. `resume_pipeline/pipeline/jd_loader.py`

**Port** from `resume_agent/jd_loader.py`, with the Playwright fallback **dropped** — v2 does not
ship a headless browser. `fetch_jd_from_url` keeps only the httpx path.

```python
JDSourceType = Literal["text", "upload", "url"]

@dataclass(frozen=True)
class JDLoadResult:
    text: str
    error: str | None = None
    source_type: JDSourceType = "text"
    @property
    def ok(self) -> bool: ...   # error is None and text.strip() is non-empty

def load_jd_from_text(text: str) -> JDLoadResult
def load_jd_from_upload(file_name: str, data: bytes) -> JDLoadResult
def fetch_jd_from_url(url: str, timeout_seconds: float = 12.0, *, client: Any | None = None) -> JDLoadResult
def normalize_text(text: str) -> str
def extract_text_from_html(html: str) -> str
def detect_blocked_or_auth_page(text: str) -> str | None
def looks_like_job_description(text: str) -> bool
```

Behaviour that must hold:
- Text below `MIN_JD_TEXT_LENGTH` (300) after normalisation is rejected with a non-empty `error`
  and an empty `text`. This is the guard that stops a run before any LLM call.
- `load_jd_from_upload` accepts only `.txt` and `.md`; any other suffix is an error. Bytes that
  are not valid UTF-8 are an error, not an exception.
- `fetch_jd_from_url` with a blank URL returns an error without making a request.
- An HTTP status ≥ 400, a timeout, or a transport error each return a `JDLoadResult` with an
  error — never raise.
- An HTML response is reduced to text before the length check; a non-HTML response is used as-is.
- A response detected as a block page, a login wall, or page boilerplate is an error even when it
  is longer than 300 characters.
- The `client` keyword argument accepts a pre-built httpx client so tests can drive the function
  through a transport stub. This is the one addition to v1's signature, and it exists so no test
  needs the network.

---

## 5. `resume_pipeline/pipeline/prompts.py`

**Port** `render_prompt` and the governance prompt from `resume_agent/prompt_loader.py`, changed
so the body is passed in rather than read from disk (RG-022).

```python
USER_CONTROLLED_KEYS: frozenset[str] = frozenset({"JD_TEXT", "COMPANY_NAME", "JOB_TITLE"})
COMPACT_GOVERNANCE_PROMPT: str
PromptStage = Literal["targeting", "generation", "review", "revision", "ats", "cover_letter"]
REQUIRED_VARS: dict[PromptStage, frozenset[str]]

def render_prompt(body: str, **values: str) -> str
def governance_prompt() -> str
def extract_variables(body: str) -> set[str]
def validate_prompt_body(stage: PromptStage, body: str) -> list[str]
```

- `render_prompt` replaces every `{{KEY}}` with its value. A key in `USER_CONTROLLED_KEYS` is
  wrapped as `<user_input>\n{value}\n</user_input>` before substitution. This is prompt-injection
  containment and must survive the port: a job description is attacker-controlled text.
- A `{{VAR}}` left unsubstituted after all values are applied raises `ValidationFailed` naming it.
  (v1 silently left it in place; RG-022 calls for the raise.)
- `extract_variables` returns the set of `{{...}}` token names in a body.
- `validate_prompt_body` returns a list of human-readable problems, empty when valid: one entry
  per required variable that is missing, and one per token present that the stage does not define.
  It returns **all** problems, never just the first.
- `governance_prompt()` returns `COMPACT_GOVERNANCE_PROMPT.strip()`, copied verbatim from v1
  including the `<user_input>` clause. Do not reword it; it is what stops fabrication.

`REQUIRED_VARS` per stage, taken from v1's actual `render_prompt` call sites:

| Stage | Variables |
| --- | --- |
| targeting | COMPANY_NAME, JOB_TITLE, JD_TEXT, SOURCE_OF_TRUTH |
| generation | TARGETING_BRIEF, JD_TEXT, BASE_RESUME_TEX, SOURCE_OF_TRUTH |
| review | COMPANY_NAME, JOB_TITLE, REVISION_COUNT, TARGETING_BRIEF, JD_TEXT, SOURCE_OF_TRUTH, PREVIOUS_MUST_FIX, RESUME_TEX |
| revision | COMPANY_NAME, JOB_TITLE, TARGETING_BRIEF, JD_TEXT, SOURCE_OF_TRUTH, RESUME_TEX, RESUME_MUST_FIX, FIX_RESOLUTION_MATRIX, RESUME_SCORE, RESUME_TARGET_SCORE, RESUME_CATEGORY_SCORES, ATS_TOP_ACTIONS, ATS_UNMET_HARD_REQUIREMENTS |
| cover_letter | COMPANY_NAME, JOB_TITLE, TARGETING_BRIEF, JD_TEXT, RESUME_TEX, SOURCE_OF_TRUTH, FIX_RESOLUTION_SUMMARY |
| ats | JD_TEXT, ATS_FINDINGS |

The five seeded prompt bodies live at `seed/prompts/*.md` and each must pass its own stage's
validation. Mapping: `targeting_brief.md`→targeting, `generator.md`→generation,
`reviewer.md`→review, `reviser.md`→revision, `cover_letter.md`→cover_letter.

---

## 6. `resume_pipeline/pipeline/latex_text.py`

New, shared by the ATS service and the import service.

```python
def tex_to_text(tex: str) -> str: ...
```

Reduces a LaTeX document to the prose an ATS would see. It must:
- drop the preamble before `\begin{document}` when one is present, and keep the whole input when
  it is not (an imported plain-text resume passes through);
- strip comments (an unescaped `%` to end of line), leaving `\%` intact as a literal percent —
  **but only when the input is actually LaTeX.** A document carrying no LaTeX signal at all (no
  `\documentclass`, no environment, no macro with an argument, no backslash escape, no `\item`)
  is prose, and a `%` in prose is a percent sign. Stripping to end of line there silently deletes
  the rest of any bullet containing a percentage — which is exactly the quantified achievement the
  ATS structural score rewards — from every resume a user pastes into the import flow.
  *(Amended during WP2 reconciliation: the original wording made this rule unconditional while also
  requiring that "an imported plain-text resume passes through", which cannot both hold. Both the
  test agent and the implementing agent flagged the conflict independently.)*
- unwrap common text macros to their argument — `\textbf{x}`, `\textit{x}`, `\emph{x}`,
  `\underline{x}`, `\href{url}{label}` → `label`, `\texttt{x}`;
- drop layout-only macros and their arguments — `\vspace`, `\hspace`, `\rule`, `\hfill`, and
  `\begin{...}`/`\end{...}` markers;
- turn `\item` into a line break so bullets stay separate lines, because the ATS structural score
  counts bullets;
- convert escaped characters `\&`, `\%`, `\$`, `\#`, `\_` to their literal forms;
- collapse runs of three or more blank lines to two, and strip trailing whitespace per line.

The bar it must clear, from RG-033: a `.tex` resume and its plain-text equivalent score within
2 points of each other.

---

## 7. `resume_pipeline/pipeline/sot_render.py`

New (RG-020). Turns structured career rows into the exact `SOURCE_OF_TRUTH` string the prompts
take. This is the single producer of that string.

```python
@dataclass(frozen=True)
class SotBullet:
    id: str
    text: str
    metrics: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    sort_order: int = 0

@dataclass(frozen=True)
class SotProject:
    id: str
    name: str
    summary: str = ""
    tech: list[str] = field(default_factory=list)
    sort_order: int = 0
    bullets: list[SotBullet] = field(default_factory=list)

@dataclass(frozen=True)
class SotCompany:
    id: str
    name: str
    role_title: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    sort_order: int = 0
    projects: list[SotProject] = field(default_factory=list)
    bullets: list[SotBullet] = field(default_factory=list)

@dataclass(frozen=True)
class SotSkill:
    id: str
    name: str
    category: str = ""
    proficiency: str = ""
    years: float | None = None
    evidence_bullet_ids: list[str] = field(default_factory=list)
    sort_order: int = 0

@dataclass(frozen=True)
class SourceOfTruth:
    header: str = ""
    companies: list[SotCompany] = field(default_factory=list)
    skills: list[SotSkill] = field(default_factory=list)

def render_source_of_truth(sot: SourceOfTruth) -> str: ...
def parse_v1_source_of_truth(text: str) -> SourceOfTruth: ...
```

`render_source_of_truth` must be **deterministic**: it sorts companies by `sort_order` then `name`,
projects and bullets the same way within their parent, and skills by category then `sort_order`
then `name`. Two calls on the same data return identical strings, and rows inserted in a different
order render identically. Prompt caching and run-to-run comparison both depend on this.

Output shape, following v1's `base/source_of_truth.txt` so the existing prompts need no edit:
- the `header` block verbatim first, when non-empty, followed by a blank line;
- per company, a line `<name> — <role_title> (<start_date> – <end_date>, <location>)` with absent
  parts and their separators omitted rather than rendered empty;
- company-level bullets as `- <text>` lines, indented two spaces;
- each project as `  Project: <name>` then its summary, a `Tech: a, b, c` line when `tech` is
  non-empty, then its bullets indented four spaces;
- a `[SKILLS]` section at the end, grouped by category with the category name as a sub-header and
  each skill on its own `- ` line; a skill with `years` set renders `- <name> (<years>y)`.

`parse_v1_source_of_truth` reads a v1-format text block and returns the structured record. It is
the import path for RG-020's `/import` route and the migration in RG-053. It is best-effort: text
it cannot classify belongs in `header` rather than being dropped. The round-trip bar is that
re-rendering a parsed real `source_of_truth.txt` loses no company, project, bullet, or skill —
not that it is byte-identical, because v1's file has hand-written sections with no structural
meaning. `tests/fixtures/v1/source_of_truth.txt` is the real file to test against.

---

## 8. `resume_pipeline/services/ats_service.py`

Wraps the vendored `resume_pipeline.ats` package (already present, tests already green at
`tests/ats/`). Ports the contract of `resume_agent/ats_client.py`.

```python
def check(resume_text: str, jd_text: str) -> dict[str, Any]: ...
```

Returns a dict with exactly these keys — v1's names, which `persist_outputs` writes and the
result view reads:

```
ats_total_score          float | None   0–100, clamped
ats_grade                str | None     Excellent / Good / Fair / Poor
ats_keyword_score        float | None   0–50
ats_structural_score     float | None   0–30
ats_semantic_score       float | None   0–20
ats_matched              list[str]
ats_missing_required     list[str]
ats_missing_preferred    list[str]
ats_missing_nice_to_have list[str]
ats_top_actions          list[str]
ats_hard_requirements    list[dict]     each: kind, description, required_value, met, confidence
ats_all_hard_met         bool
ats_error                str | None
```

Behaviour that must hold:
- **It never raises.** Any exception from the scorer is caught and returned as `ats_error` with
  every score key `None` and every list key empty and `ats_all_hard_met` False. A run must survive
  a bad ATS check; this is point 5 of the must-not-lose list.
- It calls `tex_to_text` on `resume_text` before scoring, because the scorer expects prose.
- `ats_total_score` is clamped into 0.0–100.0.
- Given identical inputs it returns an identical result. No randomness, no clock, no network.
- An empty resume or an empty JD returns `ats_error`, not a zero score — a zero would read as a
  real, terrible score rather than a missing measurement.

---

## Acceptance criteria for the package

1. The 39 vendored ATS tests still pass, unmodified.
2. v1's `test_scoring.py` and `test_resume_selection.py` pass against the ported modules with only
   import paths changed.
3. Every seeded prompt in `seed/prompts/` passes `validate_prompt_body` for its stage.
4. `render_source_of_truth` is stable across insertion orders and repeated calls.
5. A `.tex` resume and its plain-text equivalent score within 2 ATS points.
6. Nothing in this package opens a socket, reads an environment variable, or touches a database.

## Test paths (test agent writes only here)

```
tests/pipeline/test_scoring.py
tests/pipeline/test_budgets.py
tests/pipeline/test_template_select.py
tests/pipeline/test_jd_loader.py
tests/pipeline/test_prompts.py
tests/pipeline/test_latex_text.py
tests/pipeline/test_sot_render.py
tests/services/test_ats_service.py
tests/conftest.py
```

## Source paths (implementing agent writes only here)

```
resume_pipeline/pipeline/scoring.py
resume_pipeline/pipeline/budgets.py
resume_pipeline/pipeline/template_select.py
resume_pipeline/pipeline/jd_loader.py
resume_pipeline/pipeline/prompts.py
resume_pipeline/pipeline/latex_text.py
resume_pipeline/pipeline/sot_render.py
resume_pipeline/services/ats_service.py
resume_pipeline/errors.py   (only ValidationFailed, if WP3 has not landed it yet)
```
