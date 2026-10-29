from __future__ import annotations

from pathlib import Path

from resume_agent.storage import SavedApplication, read_application_status, write_application_status


def test_application_status_defaults_and_round_trip(tmp_path: Path) -> None:
    application = SavedApplication(
        label="company/role",
        output_dir=tmp_path,
        status_path=tmp_path / "application_status.json",
        jd_path=None,
        resume_tex_path=None,
        cover_letter_tex_path=None,
        review_json_path=None,
        resume_pdf_path=None,
        cover_letter_pdf_path=None,
    )

    assert read_application_status(application)["status"] == "Draft"

    write_application_status(
        application,
        {
            "status": "Interviewing",
            "selected": True,
            "rejected": False,
            "round_count": 3,
            "current_round": "Technical",
            "next_action": "Prepare system design",
            "notes": "Strong match",
        },
    )

    status = read_application_status(application)
    assert status["status"] == "Interviewing"
    assert status["round_count"] == 3
    assert status["current_round"] == "Technical"
