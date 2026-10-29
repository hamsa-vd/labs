"""Source-of-truth rendering and v1 import (WP2 §7).

`render_source_of_truth` is the single producer of the SOURCE_OF_TRUTH string every prompt
takes. Acceptance criterion 4 is that it is stable across insertion orders and repeat calls:
prompt caching and run-to-run comparison both depend on that, so the determinism tests here
are the point of the module.
"""

from __future__ import annotations

import dataclasses

import pytest

from resume_pipeline.pipeline.sot_render import (
    SotBullet,
    SotCompany,
    SotProject,
    SotSkill,
    SourceOfTruth,
    parse_v1_source_of_truth,
    render_source_of_truth,
)

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _index_of_line_containing(text: str, needle: str) -> int:
    for number, line in enumerate(text.splitlines()):
        if needle in line:
            return number
    raise AssertionError(f"{needle!r} not found in rendered output:\n{text}")


def _line_containing(text: str, needle: str) -> str:
    return text.splitlines()[_index_of_line_containing(text, needle)]


def _full_sot() -> SourceOfTruth:
    return SourceOfTruth(
        header="CANDIDATE MASTER SOURCE DOC\nName: Jane Doe",
        companies=[
            SotCompany(
                id="c1",
                name="Acme",
                role_title="Staff Engineer",
                start_date="Jan 2020",
                end_date="Dec 2022",
                location="London, UK",
                sort_order=1,
                bullets=[
                    SotBullet(id="b1", text="Led the payments rebuild.", sort_order=1),
                    SotBullet(id="b2", text="Cut latency by 45 percent.", sort_order=2),
                ],
                projects=[
                    SotProject(
                        id="p1",
                        name="Payments",
                        summary="Rebuilt the settlement path.",
                        tech=["Python", "Kafka"],
                        sort_order=1,
                        bullets=[SotBullet(id="b3", text="Shipped the ledger.", sort_order=1)],
                    )
                ],
            ),
            SotCompany(
                id="c2",
                name="Initech",
                role_title="Engineer",
                start_date="Jan 2018",
                end_date="Dec 2019",
                location="Chennai, India",
                sort_order=2,
                bullets=[SotBullet(id="b4", text="Built the reporting API.", sort_order=1)],
            ),
        ],
        skills=[
            SotSkill(id="s1", name="Python", category="Languages", years=5.5, sort_order=1),
            SotSkill(id="s2", name="Java", category="Languages", sort_order=2),
            SotSkill(id="s3", name="AWS", category="Cloud", sort_order=1),
        ],
    )


# ─── Dataclass shape ──────────────────────────────────────────────────────────


def test_dataclasses_are_frozen_with_the_contract_defaults() -> None:
    bullet = SotBullet(id="b", text="t")
    assert (bullet.metrics, bullet.tags, bullet.sort_order) == ([], [], 0)

    project = SotProject(id="p", name="n")
    assert (project.summary, project.tech, project.sort_order, project.bullets) == ("", [], 0, [])

    company = SotCompany(id="c", name="n")
    assert company.role_title == company.start_date == company.end_date == company.location == ""
    assert (company.sort_order, company.projects, company.bullets) == (0, [], [])

    skill = SotSkill(id="s", name="n")
    assert (skill.category, skill.proficiency, skill.years) == ("", "", None)
    assert (skill.evidence_bullet_ids, skill.sort_order) == ([], 0)

    sot = SourceOfTruth()
    assert (sot.header, sot.companies, sot.skills) == ("", [], [])

    for frozen in (bullet, project, company, skill, sot):
        with pytest.raises(dataclasses.FrozenInstanceError):
            frozen.id = "changed"  # type: ignore[misc]


def test_default_lists_are_not_shared_between_instances() -> None:
    first = SotCompany(id="a", name="A")
    second = SotCompany(id="b", name="B")
    assert first.bullets is not second.bullets


# ─── Acceptance criterion 4: determinism ──────────────────────────────────────


def test_repeated_calls_on_the_same_data_are_identical() -> None:
    sot = _full_sot()
    assert render_source_of_truth(sot) == render_source_of_truth(sot)


def test_rows_inserted_in_a_different_order_render_identically() -> None:
    sot = _full_sot()
    shuffled = dataclasses.replace(
        sot,
        companies=[
            dataclasses.replace(
                sot.companies[1],
                bullets=list(reversed(sot.companies[1].bullets)),
            ),
            dataclasses.replace(
                sot.companies[0],
                bullets=list(reversed(sot.companies[0].bullets)),
                projects=list(reversed(sot.companies[0].projects)),
            ),
        ],
        skills=list(reversed(sot.skills)),
    )
    assert render_source_of_truth(shuffled) == render_source_of_truth(sot)


def test_two_separately_built_but_equal_records_render_identically() -> None:
    assert render_source_of_truth(_full_sot()) == render_source_of_truth(_full_sot())


def test_an_empty_record_renders_without_raising() -> None:
    assert isinstance(render_source_of_truth(SourceOfTruth()), str)


# ─── Ordering ─────────────────────────────────────────────────────────────────


def test_companies_sort_by_sort_order_then_name() -> None:
    sot = SourceOfTruth(
        companies=[
            SotCompany(id="3", name="Zeta", sort_order=2),
            SotCompany(id="1", name="Beta", sort_order=1),
            SotCompany(id="2", name="Alpha", sort_order=1),
        ]
    )
    rendered = render_source_of_truth(sot)
    assert (
        _index_of_line_containing(rendered, "Alpha")
        < _index_of_line_containing(rendered, "Beta")
        < _index_of_line_containing(rendered, "Zeta")
    )


def test_company_bullets_sort_by_sort_order_then_text() -> None:
    sot = SourceOfTruth(
        companies=[
            SotCompany(
                id="c",
                name="Acme",
                bullets=[
                    SotBullet(id="3", text="third bullet", sort_order=2),
                    SotBullet(id="2", text="second bullet", sort_order=1),
                    SotBullet(id="1", text="first bullet", sort_order=0),
                ],
            )
        ]
    )
    rendered = render_source_of_truth(sot)
    assert (
        _index_of_line_containing(rendered, "first bullet")
        < _index_of_line_containing(rendered, "second bullet")
        < _index_of_line_containing(rendered, "third bullet")
    )


def test_projects_sort_by_sort_order_then_name() -> None:
    sot = SourceOfTruth(
        companies=[
            SotCompany(
                id="c",
                name="Acme",
                projects=[
                    SotProject(id="3", name="Gamma", sort_order=2),
                    SotProject(id="2", name="Beta", sort_order=1),
                    SotProject(id="1", name="Alpha", sort_order=1),
                ],
            )
        ]
    )
    rendered = render_source_of_truth(sot)
    assert (
        _index_of_line_containing(rendered, "Alpha")
        < _index_of_line_containing(rendered, "Beta")
        < _index_of_line_containing(rendered, "Gamma")
    )


def test_skills_group_by_category_then_sort_order_then_name() -> None:
    sot = SourceOfTruth(
        skills=[
            SotSkill(id="4", name="Terraform", category="Cloud", sort_order=2),
            SotSkill(id="3", name="AWS", category="Cloud", sort_order=1),
            SotSkill(id="2", name="Python", category="Languages", sort_order=1),
            SotSkill(id="1", name="Java", category="Languages", sort_order=1),
        ]
    )
    rendered = render_source_of_truth(sot)
    assert (
        _index_of_line_containing(rendered, "AWS")
        < _index_of_line_containing(rendered, "Terraform")
        < _index_of_line_containing(rendered, "Java")
        < _index_of_line_containing(rendered, "Python")
    )


# ─── Header ───────────────────────────────────────────────────────────────────


def test_a_non_empty_header_renders_first_and_verbatim() -> None:
    header = "CANDIDATE MASTER SOURCE DOC\nName: Jane Doe\nVisa: none required"
    rendered = render_source_of_truth(
        SourceOfTruth(header=header, companies=[SotCompany(id="c", name="Acme")])
    )
    assert rendered.startswith(header)
    assert _index_of_line_containing(rendered, "CANDIDATE") < _index_of_line_containing(rendered, "Acme")


def test_a_header_is_followed_by_a_blank_line() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(header="Header line", companies=[SotCompany(id="c", name="Acme")])
    )
    lines = rendered.splitlines()
    assert lines[0] == "Header line"
    assert lines[1] == ""


def test_an_empty_header_adds_no_leading_blank_line() -> None:
    rendered = render_source_of_truth(SourceOfTruth(companies=[SotCompany(id="c", name="Acme")]))
    assert not rendered.startswith("\n")
    assert rendered.splitlines()[0].strip() != ""


# ─── Company line ─────────────────────────────────────────────────────────────


def test_a_complete_company_line_uses_the_contract_shape() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(
            companies=[
                SotCompany(
                    id="c",
                    name="Acme",
                    role_title="Staff Engineer",
                    start_date="Jan 2020",
                    end_date="Dec 2022",
                    location="London, UK",
                )
            ]
        )
    )
    assert _line_containing(rendered, "Acme").strip() == (
        "Acme — Staff Engineer (Jan 2020 – Dec 2022, London, UK)"
    )


def test_a_company_with_only_a_name_renders_only_its_name() -> None:
    rendered = render_source_of_truth(SourceOfTruth(companies=[SotCompany(id="c", name="Acme")]))
    assert _line_containing(rendered, "Acme").strip() == "Acme"


def test_a_missing_role_title_drops_the_dash_separator() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(
            companies=[
                SotCompany(
                    id="c",
                    name="Acme",
                    start_date="Jan 2020",
                    end_date="Dec 2022",
                    location="London, UK",
                )
            ]
        )
    )
    assert _line_containing(rendered, "Acme").strip() == "Acme (Jan 2020 – Dec 2022, London, UK)"


def test_a_missing_location_drops_the_comma() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(
            companies=[
                SotCompany(
                    id="c",
                    name="Acme",
                    role_title="Staff Engineer",
                    start_date="Jan 2020",
                    end_date="Dec 2022",
                )
            ]
        )
    )
    assert _line_containing(rendered, "Acme").strip() == "Acme — Staff Engineer (Jan 2020 – Dec 2022)"


def test_missing_dates_leave_the_location_alone_in_the_parentheses() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(
            companies=[SotCompany(id="c", name="Acme", role_title="Staff Engineer", location="London, UK")]
        )
    )
    assert _line_containing(rendered, "Acme").strip() == "Acme — Staff Engineer (London, UK)"


def test_no_rendered_line_is_only_whitespace() -> None:
    # Absent parts are omitted, not rendered as empty padding.
    rendered = render_source_of_truth(_full_sot())
    for line in rendered.splitlines():
        assert line == "" or line.strip() != ""


# ─── Bullets, projects, skills ────────────────────────────────────────────────


def test_company_bullets_are_dash_prefixed_and_indented_two_spaces() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(
            companies=[
                SotCompany(id="c", name="Acme", bullets=[SotBullet(id="b", text="Led the rebuild.")])
            ]
        )
    )
    assert "  - Led the rebuild." in rendered.splitlines()


def test_a_project_renders_its_header_summary_tech_and_bullets() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(
            companies=[
                SotCompany(
                    id="c",
                    name="Acme",
                    projects=[
                        SotProject(
                            id="p",
                            name="Payments",
                            summary="Rebuilt the settlement path.",
                            tech=["Python", "Kafka", "AWS"],
                            bullets=[SotBullet(id="b", text="Shipped the ledger.")],
                        )
                    ],
                )
            ]
        )
    )
    lines = rendered.splitlines()
    assert "  Project: Payments" in lines
    assert "    - Shipped the ledger." in lines
    assert any(line.strip() == "Tech: Python, Kafka, AWS" for line in lines)
    assert any("Rebuilt the settlement path." in line for line in lines)
    assert (
        _index_of_line_containing(rendered, "Project: Payments")
        < _index_of_line_containing(rendered, "Rebuilt the settlement path.")
        < _index_of_line_containing(rendered, "Tech: Python")
        < _index_of_line_containing(rendered, "Shipped the ledger.")
    )


def test_a_project_without_tech_renders_no_tech_line() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(
            companies=[SotCompany(id="c", name="Acme", projects=[SotProject(id="p", name="Payments")])]
        )
    )
    assert "Tech:" not in rendered


def test_skills_render_in_a_skills_section_at_the_end() -> None:
    rendered = render_source_of_truth(_full_sot())
    assert "[SKILLS]" in rendered
    assert _index_of_line_containing(rendered, "[SKILLS]") > _index_of_line_containing(rendered, "Acme")
    assert _index_of_line_containing(rendered, "[SKILLS]") > _index_of_line_containing(rendered, "Initech")


def test_each_category_is_a_sub_header_above_its_skills() -> None:
    rendered = render_source_of_truth(_full_sot())
    cloud_header = _index_of_line_containing(rendered, "Cloud")
    languages_header = _index_of_line_containing(rendered, "Languages")
    assert cloud_header < _index_of_line_containing(rendered, "- AWS")
    assert languages_header < _index_of_line_containing(rendered, "- Java")
    assert _index_of_line_containing(rendered, "- AWS") < languages_header


def test_a_skill_without_years_renders_as_a_plain_dash_line() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(skills=[SotSkill(id="s", name="Java", category="Languages")])
    )
    assert any(line.strip() == "- Java" for line in rendered.splitlines())


def test_a_skill_with_years_renders_them_in_parentheses() -> None:
    rendered = render_source_of_truth(
        SourceOfTruth(skills=[SotSkill(id="s", name="Python", category="Languages", years=5.5)])
    )
    assert any(line.strip() == "- Python (5.5y)" for line in rendered.splitlines())


def test_everything_given_appears_in_the_rendered_string() -> None:
    sot = _full_sot()
    rendered = render_source_of_truth(sot)
    for company in sot.companies:
        assert company.name in rendered
        assert company.role_title in rendered
        for bullet in company.bullets:
            assert bullet.text in rendered
        for project in company.projects:
            assert project.name in rendered
            assert project.summary in rendered
            for bullet in project.bullets:
                assert bullet.text in rendered
    for skill in sot.skills:
        assert skill.name in rendered


# ─── parse_v1_source_of_truth ─────────────────────────────────────────────────


def test_parsing_an_empty_string_returns_an_empty_record() -> None:
    parsed = parse_v1_source_of_truth("")
    assert isinstance(parsed, SourceOfTruth)
    assert parsed.companies == []
    assert parsed.skills == []


def test_parsing_reads_the_company_block_fields() -> None:
    text = (
        "--------------------------------------------------\n"
        "COMPANY: Acme (London, UK)\n"
        "ROLE: Software Engineer\n"
        "DURATION: Aug 2022 – Present\n"
        "--------------------------------------------------\n"
        "\n"
        "- Built the settlement API.\n"
        "- Cut latency by 45 percent.\n"
    )
    parsed = parse_v1_source_of_truth(text)
    assert len(parsed.companies) == 1
    company = parsed.companies[0]
    assert "Acme" in company.name
    assert company.role_title == "Software Engineer"
    assert "Aug 2022" in f"{company.start_date} {company.end_date}"
    assert "Present" in f"{company.start_date} {company.end_date}"
    assert "London, UK" in f"{company.name} {company.location}"
    bullet_text = " ".join(
        bullet.text for bullet in company.bullets + [b for p in company.projects for b in p.bullets]
    )
    assert "Built the settlement API." in bullet_text
    assert "Cut latency by 45 percent." in bullet_text


def test_text_the_parser_cannot_classify_goes_to_the_header_not_the_bin() -> None:
    text = (
        "==============================\n"
        "CANDIDATE MASTER SOURCE DOC\n"
        "==============================\n"
        "\n"
        "[PERSONAL INFORMATION]\n"
        "Name: Jane Doe\n"
        "Visa: sponsorship required until 2027\n"
        "\n"
        "--------------------------------------------------\n"
        "COMPANY: Acme (London, UK)\n"
        "ROLE: Software Engineer\n"
        "DURATION: Aug 2022 – Present\n"
        "--------------------------------------------------\n"
        "- Built the settlement API.\n"
    )
    parsed = parse_v1_source_of_truth(text)
    assert "Name: Jane Doe" in parsed.header
    assert "Visa: sponsorship required until 2027" in parsed.header


def test_parsing_is_deterministic(v1_source_of_truth_text: str) -> None:
    assert parse_v1_source_of_truth(v1_source_of_truth_text) == parse_v1_source_of_truth(
        v1_source_of_truth_text
    )


def test_the_real_v1_file_yields_its_companies(v1_source_of_truth_text: str) -> None:
    parsed = parse_v1_source_of_truth(v1_source_of_truth_text)
    names = " | ".join(company.name for company in parsed.companies)
    assert "Liv-ex" in names
    assert "Presidio" in names


def test_the_real_v1_file_yields_its_bullets(v1_source_of_truth_text: str) -> None:
    parsed = parse_v1_source_of_truth(v1_source_of_truth_text)
    bullets = [
        bullet
        for company in parsed.companies
        for bullet in company.bullets + [b for project in company.projects for b in project.bullets]
    ]
    assert len(bullets) > 10


def test_re_rendering_the_real_v1_file_loses_nothing_it_parsed(v1_source_of_truth_text: str) -> None:
    parsed = parse_v1_source_of_truth(v1_source_of_truth_text)
    rendered = render_source_of_truth(parsed)
    for company in parsed.companies:
        assert company.name in rendered
        for bullet in company.bullets:
            assert bullet.text in rendered
        for project in company.projects:
            assert project.name in rendered
            for bullet in project.bullets:
                assert bullet.text in rendered
    for skill in parsed.skills:
        assert skill.name in rendered


@pytest.mark.parametrize(
    "fragment",
    [
        "hamsavardhan99@gmail.com",
        "Reduced bundle size",
        "Migrated Lucene",
        "Built telephony system backend",
        "Hackathon winner",
        "Red Hat Certified Engineer",
        "SRM University",
    ],
)
def test_no_content_of_the_real_v1_file_is_dropped_on_round_trip(
    v1_source_of_truth_text: str, fragment: str
) -> None:
    assert fragment in v1_source_of_truth_text
    rendered = render_source_of_truth(parse_v1_source_of_truth(v1_source_of_truth_text))
    assert fragment in rendered


def test_round_trip_rendering_is_deterministic(v1_source_of_truth_text: str) -> None:
    parsed = parse_v1_source_of_truth(v1_source_of_truth_text)
    assert render_source_of_truth(parsed) == render_source_of_truth(parsed)
