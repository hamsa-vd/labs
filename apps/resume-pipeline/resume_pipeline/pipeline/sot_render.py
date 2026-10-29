"""Source-of-truth rendering and import (RG-020).

The single producer of the `SOURCE_OF_TRUTH` string the prompts take. Rendering is deterministic:
rows sort by their explicit `sort_order` and then by name, so two runs over the same career record
produce byte-identical text no matter what order the rows arrived in. Prompt caching and
run-to-run comparison both depend on that.

The output shape follows v1's `base/source_of_truth.txt` closely enough that the existing prompt
bodies need no edit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


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


SKILLS_HEADING = "[SKILLS]"

_COMPANY_INDENT = "  "
_PROJECT_INDENT = "  "
_PROJECT_BODY_INDENT = "    "


# ─── Rendering ────────────────────────────────────────────────────────────────


def render_source_of_truth(sot: SourceOfTruth) -> str:
    """Render a career record as the `SOURCE_OF_TRUTH` prompt variable.

    Deterministic: companies sort by `sort_order` then `name`, projects and bullets the same way
    within their parent, and skills by category then `sort_order` then `name`.
    """
    lines: list[str] = []

    header = (sot.header or "").strip()
    if header:
        lines.extend(header.split("\n"))
        lines.append("")

    for company in _sorted_companies(sot.companies):
        lines.append(_company_line(company))
        for bullet in _sorted_bullets(company.bullets):
            lines.append(f"{_COMPANY_INDENT}- {_clean(bullet.text)}")
        for project in _sorted_projects(company.projects):
            lines.extend(_project_lines(project))
        lines.append("")

    skill_lines = _skill_lines(sot.skills)
    if skill_lines:
        lines.extend(skill_lines)

    return _collapse(lines)


def _sorted_companies(companies: list[SotCompany]) -> list[SotCompany]:
    return sorted(companies, key=lambda c: (c.sort_order, c.name, c.id))


def _sorted_projects(projects: list[SotProject]) -> list[SotProject]:
    return sorted(projects, key=lambda p: (p.sort_order, p.name, p.id))


def _sorted_bullets(bullets: list[SotBullet]) -> list[SotBullet]:
    # Bullets have no name, so their text stands in for one. Two bullets that share a
    # `sort_order` still render in a fixed order whichever way round they were inserted.
    return sorted(bullets, key=lambda b: (b.sort_order, b.text, b.id))


def _company_line(company: SotCompany) -> str:
    parts = [_clean(company.name)]
    role = _clean(company.role_title)
    if role:
        parts.append(f" — {role}")

    dates = " – ".join(p for p in (_clean(company.start_date), _clean(company.end_date)) if p)
    location = _clean(company.location)
    meta = ", ".join(p for p in (dates, location) if p)
    if meta:
        parts.append(f" ({meta})")
    return "".join(parts)


def _project_lines(project: SotProject) -> list[str]:
    lines = [f"{_PROJECT_INDENT}Project: {_clean(project.name)}"]
    summary = _clean(project.summary)
    if summary:
        lines.append(f"{_PROJECT_BODY_INDENT}{summary}")
    tech = [_clean(item) for item in project.tech if _clean(item)]
    if tech:
        lines.append(f"{_PROJECT_BODY_INDENT}Tech: {', '.join(tech)}")
    for bullet in _sorted_bullets(project.bullets):
        lines.append(f"{_PROJECT_BODY_INDENT}- {_clean(bullet.text)}")
    return lines


def _skill_lines(skills: list[SotSkill]) -> list[str]:
    if not skills:
        return []
    ordered = sorted(skills, key=lambda s: (s.category, s.sort_order, s.name, s.id))

    lines = [SKILLS_HEADING, ""]
    current_category: str | None = None
    for skill in ordered:
        category = _clean(skill.category)
        if category != current_category:
            if current_category is not None:
                lines.append("")
            # A skill with no category renders directly under the heading; there is no
            # sub-header to write for it.
            if category:
                lines.append(category)
            current_category = category
        lines.append(f"- {_skill_label(skill)}")
    return lines


def _skill_label(skill: SotSkill) -> str:
    name = _clean(skill.name)
    if skill.years is None:
        return name
    return f"{name} ({_format_years(skill.years)}y)"


def _format_years(years: float) -> str:
    if float(years).is_integer():
        return str(int(years))
    return str(round(float(years), 1))


def _clean(value: str) -> str:
    return (value or "").strip()


def _collapse(lines: list[str]) -> str:
    text = "\n".join(line.rstrip() for line in lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


# ─── Importing v1 text ────────────────────────────────────────────────────────

_SECTION_RE = re.compile(r"^\[(?P<label>[^\]]+)\]\s*$")
_RULE_RE = re.compile(r"^[-=_]{5,}\s*$")
_BULLET_RE = re.compile(r"^\s*[-•*]\s+(?P<text>.*\S)\s*$")
_FIELD_RE = re.compile(r"^(?P<key>COMPANY|ROLE|DURATION|TYPE|LOCATION)\s*:\s*(?P<value>.*)$", re.I)
_PROJECT_LABEL_RE = re.compile(r"^PROJECT\b[^:]*:?\s*(?P<name>.*)$", re.I)
_PROJECT_LINE_RE = re.compile(r"^\s*Project\s*:\s*(?P<name>.*\S)\s*$")
_TECH_LINE_RE = re.compile(r"^\s*Tech\s*:\s*(?P<value>.*\S)\s*$")
_CATEGORY_RE = re.compile(r"^(?P<name>[A-Za-z][^:]*):\s*$")
_COMPANY_NAME_RE = re.compile(r"^(?P<name>.*?)\s*\((?P<location>[^()]*)\)\s*$")
_DURATION_RE = re.compile(r"^(?P<start>.*?)\s*[–—-]\s*(?P<end>.*)$")

_SKILL_SECTIONS = {"CORE TECH STACK", "SKILLS", "TECHNICAL SKILLS", "TECH STACK"}
_EXPERIENCE_SECTIONS = {"EXPERIENCE TIMELINE", "EXPERIENCE", "WORK EXPERIENCE"}


class _Mode:
    HEADER = "header"
    SKILLS = "skills"
    EXPERIENCE = "experience"


def parse_v1_source_of_truth(text: str) -> SourceOfTruth:
    """Read a v1-format source-of-truth block into the structured record.

    Best-effort by design: anything that cannot be classified as a company, project, bullet or
    skill is kept in `header` rather than dropped, so re-rendering loses no content that matters.
    Document order is preserved by assigning each row an increasing `sort_order`, which the
    renderer then honours.
    """
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")

    header_lines: list[str] = []
    companies: list[_CompanyDraft] = []
    skills: list[SotSkill] = []

    mode = _Mode.HEADER
    company: _CompanyDraft | None = None
    project: _ProjectDraft | None = None
    category = ""
    counters = _Counters()

    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped or _RULE_RE.match(stripped):
            # Blank lines and decorative rules carry no structure, but a blank line inside the
            # header keeps its hand-written sections apart, so that one is worth keeping.
            if mode == _Mode.HEADER and header_lines and header_lines[-1]:
                header_lines.append("")
            continue

        section = _SECTION_RE.match(stripped)
        if section:
            label = section.group("label").strip()
            upper = label.upper()
            if _is_top_level_section(lines, index):
                if upper in _SKILL_SECTIONS:
                    mode, category = _Mode.SKILLS, ""
                elif upper in _EXPERIENCE_SECTIONS:
                    mode = _Mode.EXPERIENCE
                else:
                    mode = _Mode.HEADER
                    header_lines.append(stripped)
                company, project = None, None
                continue
            if mode == _Mode.EXPERIENCE and company is not None:
                project_label = _PROJECT_LABEL_RE.match(label)
                if project_label:
                    project = _new_project(company, project_label.group("name").strip() or label, counters)
                else:
                    # A grouping label inside a company block, such as [OBSERVABILITY]. Its
                    # bullets belong to the company; the label itself carries no schema meaning.
                    project = None
                continue
            header_lines.append(stripped)
            continue

        field_match = _FIELD_RE.match(stripped)
        if field_match and field_match.group("key").upper() == "COMPANY":
            mode = _Mode.EXPERIENCE
            company = _new_company(field_match.group("value").strip(), counters)
            companies.append(company)
            project = None
            continue

        if mode == _Mode.EXPERIENCE and company is not None:
            if field_match:
                _apply_company_field(
                    company,
                    field_match.group("key").upper(),
                    field_match.group("value").strip(),
                )
                continue

            project_line = _PROJECT_LINE_RE.match(line)
            if project_line:
                project = _new_project(company, project_line.group("name").strip(), counters)
                continue

            bullet = _BULLET_RE.match(line)
            if bullet:
                target = project.bullets if project is not None else company.bullets
                target.append(
                    SotBullet(
                        id=f"bullet-{counters.next_bullet()}",
                        text=bullet.group("text").strip(),
                        sort_order=counters.bullets,
                    )
                )
                continue

            if project is not None:
                tech_line = _TECH_LINE_RE.match(line)
                if tech_line:
                    raw_tech = tech_line.group("value").split(",")
                    project.tech = [part.strip() for part in raw_tech if part.strip()]
                    continue
                project.summary_lines.append(stripped)
                continue

            header_lines.append(stripped)
            continue

        if mode == _Mode.SKILLS:
            bullet = _BULLET_RE.match(line)
            if bullet:
                skills.append(
                    SotSkill(
                        id=f"skill-{counters.next_skill()}",
                        name=bullet.group("text").strip(),
                        category=category,
                        sort_order=counters.skills,
                    )
                )
                continue
            category_match = _CATEGORY_RE.match(stripped)
            if category_match:
                category = category_match.group("name").strip()
                continue
            header_lines.append(stripped)
            continue

        header_lines.append(stripped)

    return SourceOfTruth(
        header=_join_header(header_lines),
        companies=[draft.build() for draft in companies],
        skills=skills,
    )


@dataclass
class _Counters:
    companies: int = 0
    projects: int = 0
    bullets: int = 0
    skills: int = 0

    def next_company(self) -> int:
        self.companies += 1
        return self.companies

    def next_project(self) -> int:
        self.projects += 1
        return self.projects

    def next_bullet(self) -> int:
        self.bullets += 1
        return self.bullets

    def next_skill(self) -> int:
        self.skills += 1
        return self.skills


@dataclass
class _ProjectDraft:
    id: str
    name: str
    sort_order: int
    tech: list[str] = field(default_factory=list)
    summary_lines: list[str] = field(default_factory=list)
    bullets: list[SotBullet] = field(default_factory=list)

    def build(self) -> SotProject:
        return SotProject(
            id=self.id,
            name=self.name,
            summary=" ".join(self.summary_lines).strip(),
            tech=list(self.tech),
            sort_order=self.sort_order,
            bullets=list(self.bullets),
        )


@dataclass
class _CompanyDraft:
    id: str
    name: str
    sort_order: int
    role_title: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    projects: list[_ProjectDraft] = field(default_factory=list)
    bullets: list[SotBullet] = field(default_factory=list)

    def build(self) -> SotCompany:
        return SotCompany(
            id=self.id,
            name=self.name,
            role_title=self.role_title,
            start_date=self.start_date,
            end_date=self.end_date,
            location=self.location,
            sort_order=self.sort_order,
            projects=[project.build() for project in self.projects],
            bullets=list(self.bullets),
        )


def _new_company(value: str, counters: _Counters) -> _CompanyDraft:
    name, location = value, ""
    name_match = _COMPANY_NAME_RE.match(value)
    if name_match:
        name = name_match.group("name").strip()
        location = name_match.group("location").strip()
    order = counters.next_company()
    return _CompanyDraft(id=f"company-{order}", name=name, location=location, sort_order=order)


def _new_project(company: _CompanyDraft, name: str, counters: _Counters) -> _ProjectDraft:
    order = counters.next_project()
    project = _ProjectDraft(id=f"project-{order}", name=name, sort_order=order)
    company.projects.append(project)
    return project


def _apply_company_field(company: _CompanyDraft, key: str, value: str) -> None:
    if key == "ROLE":
        company.role_title = value
    elif key == "LOCATION":
        company.location = value
    elif key == "DURATION":
        duration = _DURATION_RE.match(value)
        if duration:
            company.start_date = duration.group("start").strip()
            company.end_date = duration.group("end").strip()
        else:
            company.start_date = value
    # TYPE has no field in the v2 record; it is company metadata, not a bullet, so it is not
    # folded into the header either.


def _is_top_level_section(lines: list[str], index: int) -> bool:
    """A top-level section label is the one followed by a rule line, as v1's file writes them."""
    for candidate in lines[index + 1 : index + 2]:
        if _RULE_RE.match(candidate.strip()):
            return True
    return False


def _join_header(header_lines: list[str]) -> str:
    text = "\n".join(header_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
