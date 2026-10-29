from __future__ import annotations

from datetime import datetime

from resume_agent.storage import _choose_output_dir, slugify


def test_slugify_lowercase_kebab_and_strips_non_alphanumeric() -> None:
    assert slugify("Software Engineer III") == "software-engineer-iii"
    assert slugify("Wise: Senior II!") == "wise-senior-ii"
    assert slugify("  Paloma Health  ") == "paloma-health"


def test_choose_output_dir_versions_existing_directory(tmp_path) -> None:
    base = tmp_path / "company" / "role"
    base.mkdir(parents=True)
    (base / "hamsa_resume.tex").write_text("old", encoding="utf-8")

    chosen = _choose_output_dir(base, now=datetime(2026, 5, 19, 12, 30, 0))

    assert chosen == base / "run-20260519-123000"
