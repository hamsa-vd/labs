"""Tests for keyword extractor."""

from __future__ import annotations

from resume_pipeline.ats.keyword_extractor import extract_keywords


def test_extracts_single_tokens():
    jd = "Requires Python, Java, and Docker experience."
    keywords = extract_keywords(jd)
    canonicals = {k.canonical for k in keywords}
    assert "python" in canonicals
    assert "java" in canonicals
    assert "docker" in canonicals


def test_extracts_multi_word_phrases():
    jd = "Experience with Spring Boot and machine learning required."
    keywords = extract_keywords(jd)
    canonicals = {k.canonical for k in keywords}
    assert "spring boot" in canonicals or any("spring" in c for c in canonicals)


def test_synonyms_normalised():
    jd = "Must have k8s and AWS experience."
    keywords = extract_keywords(jd)
    canonicals = {k.canonical for k in keywords}
    assert "kubernetes" in canonicals, f"k8s should normalise to kubernetes. Got: {canonicals}"
    assert "amazon web services" in canonicals or "aws" in canonicals


def test_importance_tagging_required():
    jd = "Requirements:\n- Java\n- Spring Boot\nPreferred:\n- Scala\nNice to have:\n- Couchbase"
    keywords = extract_keywords(jd)
    by_canonical = {k.canonical: k for k in keywords}
    # Java should be required
    if "java" in by_canonical:
        assert by_canonical["java"].importance == "required", (
            f"Java should be required. Got: {by_canonical['java'].importance}"
        )


def test_filler_words_excluded():
    jd = "Looking for a strong candidate with passion and mindset."
    keywords = extract_keywords(jd)
    canonicals = {k.canonical for k in keywords}
    for skip in {"passion", "mindset", "candidate", "strong"}:
        assert skip not in canonicals, f"'{skip}' should be filtered out"
