from __future__ import annotations

from resume_agent.resume_selection import recommend_template


def test_recommends_frontend_for_react_typescript_jd() -> None:
    recommendation = recommend_template("Build React TypeScript SPA interfaces with Redux and Vite.", "Frontend Engineer")
    assert recommendation.template_key == "frontend"


def test_recommends_backend_java_for_spring_jd() -> None:
    jd = "Design Java 17 Spring Boot microservices, REST APIs, MongoDB, and Spring Security."
    recommendation = recommend_template(jd, "Backend Java Developer")
    assert recommendation.template_key == "backend-java"


def test_recommends_fullstack_for_mixed_frontend_backend_jd() -> None:
    jd = "Full Stack Engineer using React, TypeScript, backend APIs, Node.js, and cloud services."
    recommendation = recommend_template(jd, "Fullstack Software Engineer")
    assert recommendation.template_key == "fullstack"
