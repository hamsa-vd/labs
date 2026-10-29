"""Tests for synonym normalisation."""

from resume_pipeline.ats.synonyms import normalise, ALIAS_TO_CANONICAL


def test_js_normalises_to_javascript():
    assert normalise("js") == "javascript"


def test_k8s_normalises_to_kubernetes():
    assert normalise("k8s") == "kubernetes"


def test_aws_normalises_to_amazon_web_services():
    assert normalise("aws") == "amazon web services"


def test_postgres_normalises_to_postgresql():
    assert normalise("postgres") == "postgresql"


def test_unknown_term_returns_itself():
    assert normalise("someunknowntech") == "someunknowntech"


def test_reverse_map_has_no_empty_keys():
    for key in ALIAS_TO_CANONICAL:
        assert key.strip(), f"Empty key found in ALIAS_TO_CANONICAL"
