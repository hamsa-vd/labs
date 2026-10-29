"""Shared fixtures and the suite-wide network guard for WP2.

Two things live here that the whole suite depends on:

1. A socket guard (RG-008 / acceptance criterion 6). No test in this repository may open a
   socket. Anything that tries fails loudly rather than silently reaching the network.
2. The tex/plain-text resume pair and the sample job description used by the ATS service
   tests, so the "within 2 ATS points" bar (RG-033) is measured against one fixture.

`tests/fixtures/v1/` holds copies of v1's own suite as reference material. Those modules
import `resume_agent`, which does not exist here, so they are excluded from collection.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_DIR.parent
V1_FIXTURE_DIR = TESTS_DIR / "fixtures" / "v1"
SEED_PROMPT_DIR = APP_DIR / "seed" / "prompts"

# Reference copies of v1's suite, not runnable here (they import `resume_agent`).
collect_ignore_glob = ["fixtures/*", "fixtures/v1/*"]


# ─── Network guard ────────────────────────────────────────────────────────────


class NetworkAccessAttempted(RuntimeError):
    """Raised when a test tries to touch the network."""


def _blocked(*args: object, **kwargs: object) -> None:
    raise NetworkAccessAttempted(
        "A test tried to open a network connection. Tests in this package make no network "
        "calls. Drive HTTP through an httpx MockTransport passed as the `client` argument."
    )


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail any test that attempts a real connection or a DNS lookup."""
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    monkeypatch.setattr(socket.socket, "sendto", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


# ─── Path fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def v1_fixture_dir() -> Path:
    return V1_FIXTURE_DIR


@pytest.fixture(scope="session")
def v1_source_of_truth_text() -> str:
    return (V1_FIXTURE_DIR / "source_of_truth.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def seed_prompt_dir() -> Path:
    return SEED_PROMPT_DIR


# ─── Resume / JD fixtures ─────────────────────────────────────────────────────

SAMPLE_JD = """
Senior Backend Engineer — Platform

We are hiring a senior backend engineer to own our order settlement platform.

Responsibilities
In this role, you will design and operate Python and Java microservices on AWS, build
event-driven pipelines with Kafka, and drive the observability of the whole platform.
You will lead technical design reviews and mentor other engineers.

Requirements
- 5+ years of experience building backend applications in Python or Java.
- Strong experience with Spring Boot, FastAPI, and REST APIs.
- Proficiency with PostgreSQL, Redis, and Kafka.
- Experience with Docker, Kubernetes, and Terraform on AWS.
- Familiarity with Prometheus and Grafana for monitoring.
- Bachelor's degree in computer science or a related field.

Nice to have
- Experience with OAuth2 and JWT based authentication.
- Experience with OpenSearch or Elasticsearch.
"""

# The plain-text form of the resume below. A human typing out the .tex resume by hand
# would produce this: same words, bullets as dashed lines, section names on their own line.
PLAIN_RESUME = """Hamsa Vardhan
London, UK linkedin.com/in/hamsa-vardhan

SUMMARY

Senior backend engineer with 6 years of experience building Python and Java microservices
on AWS, with deep ownership of authentication, search, and observability.

SKILLS

Python, Java, Spring Boot, FastAPI, Django, PostgreSQL, Redis, Kafka, Docker, Kubernetes,
Terraform, AWS, Prometheus, Grafana, REST APIs, OAuth2, JWT, OpenSearch

EXPERIENCE

Liv-ex, London, UK — Software Engineer — Aug 2022 to Present

- Architected a Kafka event pipeline that cut order settlement latency by 45% across 12 services.
- Migrated search from Lucene to AWS OpenSearch, reducing p95 latency from 2.5s to 250ms.
- Designed JWT and OAuth2 authentication for 12 Spring Boot microservices, removing shared API keys.
- Delivered Prometheus and Grafana observability, cutting mean time to detect by 60%.
- Automated infrastructure with Terraform and Docker, saving 20 engineering hours each month.

Presidio, Chennai, India — Software Engineer — Jan 2021 to Jul 2022

- Built REST APIs in Java and Spring Boot serving 3 million requests per day.
- Developed FastAPI and Django services for internal reporting used by 200 analysts.
- Optimised PostgreSQL queries and Redis caching, reducing database load by 35%.

EDUCATION

B.Tech in Electronics and Communication Engineering, SRM University, 2016 to 2020
"""

# The same resume as LaTeX. Only constructs the contract names are used: a preamble before
# \begin{document}, comments, \textbf / \textit / \href / \texttt unwrapping, \vspace and
# \hspace and \rule and \hfill dropping, itemize markers, \item bullets, and \% \& \_ \# escapes.
TEX_RESUME = r"""\documentclass[letterpaper,11pt]{article}
\usepackage[margin=0.5in]{geometry}
\usepackage{hyperref}
\usepackage{enumitem}
% Layout tuning below — none of this is prose.
\pagestyle{empty}
\setlist[itemize]{leftmargin=*}

\begin{document}

\textbf{Hamsa Vardhan}

London, UK \hspace{6pt} \hfill \href{https://www.linkedin.com/in/hamsa-vardhan}{linkedin.com/in/hamsa-vardhan}

\vspace{-6pt}
\rule{\linewidth}{0.4pt}

\textbf{SUMMARY}

Senior backend engineer with 6 years of experience building Python and Java microservices
on AWS, with deep ownership of authentication, search, and observability.

\textbf{SKILLS}

Python, Java, Spring Boot, FastAPI, Django, PostgreSQL, Redis, Kafka, Docker, Kubernetes,
Terraform, AWS, Prometheus, Grafana, REST APIs, OAuth2, JWT, OpenSearch

\textbf{EXPERIENCE}

% Most recent role first.
\textbf{Liv-ex, London, UK} — \textit{Software Engineer} — Aug 2022 to Present

\begin{itemize}
  \item Architected a Kafka event pipeline that cut order settlement latency by 45\% across 12 services.
  \item Migrated search from Lucene to AWS OpenSearch, reducing p95 latency from 2.5s to 250ms.
  \item Designed JWT and OAuth2 authentication for 12 Spring Boot microservices, removing shared API keys.
  \item Delivered Prometheus and Grafana observability, cutting mean time to detect by 60\%.
  \item Automated infrastructure with Terraform and Docker, saving 20 engineering hours each month.
\end{itemize}

\vspace{-4pt}

\textbf{Presidio, Chennai, India} — \textit{Software Engineer} — Jan 2021 to Jul 2022

\begin{itemize}
  \item Built REST APIs in Java and Spring Boot serving 3 million requests per day.
  \item Developed FastAPI and Django services for internal reporting used by 200 analysts.
  \item Optimised PostgreSQL queries and Redis caching, reducing database load by 35\%.
\end{itemize}

\textbf{EDUCATION}

B.Tech in Electronics and Communication Engineering, SRM University, 2016 to 2020

\end{document}
"""


@pytest.fixture(scope="session")
def sample_jd() -> str:
    return SAMPLE_JD


@pytest.fixture(scope="session")
def plain_resume() -> str:
    return PLAIN_RESUME


@pytest.fixture(scope="session")
def tex_resume() -> str:
    return TEX_RESUME
