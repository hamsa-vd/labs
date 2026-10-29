-- Resume generator schema. See plan/resume-generator/contracts/WP1-schema.md.
--
-- Three invariants shape everything here:
--   1. There is one applications table. The tracker and the generator are two
--      views of the same entity, so a generated resume and the reply it earns
--      cannot drift into separate rows.
--   2. Nothing stores a plaintext provider key, and nothing stores prompt or
--      completion text next to a cost figure. Only ciphertext and counts.
--   3. The source of truth is relational, not a flat file, because the evidence
--      gate has to point a keyword at one specific bullet under one specific
--      company — a claim a text blob cannot make.

-- ---------------------------------------------------------------------------
-- A10. Shared updated_at trigger
-- ---------------------------------------------------------------------------

-- Migrations 0001-0005 define no such function, so this is the first one. One
-- body, attached per table, so a future change to the rule is a single edit.
create or replace function set_updated_at()
returns trigger language plpgsql as $fn$
begin
  new.updated_at := now();
  return new;
end;
$fn$;

-- ---------------------------------------------------------------------------
-- A1. Extending applications
-- ---------------------------------------------------------------------------

-- 'draft' is the state of an application that has a generated resume and has
-- not been sent. It is safe to widen the column without weakening the closed
-- classifier enum: refresh_application_projection writes current_status only
-- when it projects a non-null status out of application_events, and 'draft' is
-- not an application_events event_type, so neither a classifier nor the
-- projection can ever put it there.
alter table applications drop constraint if exists applications_current_status_check;
alter table applications add constraint applications_current_status_check
  check (current_status in ('draft','applied','acknowledged','assessment','interview_invite',
                            'interview_scheduled','offer','rejected','withdrawn'));

-- 'generated' is an application the generator created; 'imported' is one the v1
-- directory migration brought across.
alter table applications drop constraint if exists applications_origin_check;
alter table applications add constraint applications_origin_check
  check (origin in ('gmail','manual','generated','imported'));

alter table applications
  add column if not exists company_slug text,
  add column if not exists role_slug text,
  add column if not exists jd_text text,
  add column if not exists jd_source_type text,
  add column if not exists jd_url text,
  add column if not exists round_count int not null default 0,
  add column if not exists current_round text,
  add column if not exists next_action text,
  add column if not exists applied_at timestamptz,
  add column if not exists derived_from uuid references applications(id) on delete set null,
  add column if not exists migrated_from text,
  add column if not exists updated_at timestamptz not null default now();

alter table applications drop constraint if exists applications_jd_source_type_check;
alter table applications add constraint applications_jd_source_type_check
  check (jd_source_type is null or jd_source_type in ('text','url','upload'));

create index if not exists applications_user_updated_idx on applications (user_id, updated_at desc);

-- What makes re-running the v1 directory migration boring: a second pass over
-- the same directory collides here instead of creating a duplicate application.
create unique index if not exists applications_user_migrated_from_key
  on applications (user_id, migrated_from) where migrated_from is not null;

create index if not exists applications_derived_from_idx
  on applications (derived_from) where derived_from is not null;

drop trigger if exists applications_set_updated_at on applications;
create trigger applications_set_updated_at before update on applications
  for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- A2. Source of truth (RG-020)
-- ---------------------------------------------------------------------------

create table if not exists sot_companies (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references app_users(id) on delete cascade,
  name       text not null,
  role_title text,
  -- Dates are text, not date: v1's record holds "Jul 2022" and "Present", and
  -- coercing those to a date would invent a precision the candidate never gave.
  start_date text,
  end_date   text,
  location   text,
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists sot_companies_user_idx on sot_companies (user_id, sort_order);

create table if not exists sot_projects (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references app_users(id) on delete cascade,
  company_id uuid not null references sot_companies(id) on delete cascade,
  name       text not null,
  summary    text,
  tech       text[] not null default '{}',
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists sot_projects_user_idx on sot_projects (user_id, sort_order);
create index if not exists sot_projects_company_idx on sot_projects (company_id);

create table if not exists sot_bullets (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references app_users(id) on delete cascade,
  company_id uuid not null references sot_companies(id) on delete cascade,
  -- A bullet belongs to a company always and to a project optionally: plenty of
  -- real achievements sit under a job without sitting under a named project.
  project_id uuid references sot_projects(id) on delete cascade,
  text       text not null,
  metrics    text[] not null default '{}',
  tags       text[] not null default '{}',
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists sot_bullets_user_idx on sot_bullets (user_id, sort_order);
create index if not exists sot_bullets_company_idx on sot_bullets (company_id);
create index if not exists sot_bullets_project_idx on sot_bullets (project_id) where project_id is not null;

create table if not exists sot_skills (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references app_users(id) on delete cascade,
  name                text not null,
  category            text,
  proficiency         text,
  years               numeric,
  -- The evidence gate refuses to add a keyword that no bullet supports, so a
  -- skill carries the bullets that prove it rather than a bare assertion.
  evidence_bullet_ids uuid[] not null default '{}',
  sort_order          int not null default 0,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create index if not exists sot_skills_user_idx on sot_skills (user_id, sort_order);
create unique index if not exists sot_skills_user_name_key on sot_skills (user_id, lower(name));

drop trigger if exists sot_companies_set_updated_at on sot_companies;
create trigger sot_companies_set_updated_at before update on sot_companies
  for each row execute function set_updated_at();
drop trigger if exists sot_projects_set_updated_at on sot_projects;
create trigger sot_projects_set_updated_at before update on sot_projects
  for each row execute function set_updated_at();
drop trigger if exists sot_bullets_set_updated_at on sot_bullets;
create trigger sot_bullets_set_updated_at before update on sot_bullets
  for each row execute function set_updated_at();
drop trigger if exists sot_skills_set_updated_at on sot_skills;
create trigger sot_skills_set_updated_at before update on sot_skills
  for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- A3. Templates (RG-021)
-- ---------------------------------------------------------------------------

create table if not exists resume_templates (
  id           uuid primary key default gen_random_uuid(),
  -- Null user_id means a system template, available to everyone.
  user_id      uuid references app_users(id) on delete cascade,
  key          text not null,
  name         text not null,
  kind         text not null check (kind in ('single_page','multi_page')),
  tex_source   text not null,
  is_system    boolean not null default false,
  derived_from uuid references resume_templates(id) on delete set null,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- Two partial uniques rather than one: a user may override a system key with
-- their own row for the same (key, kind), and resolution prefers the user's.
create unique index if not exists resume_templates_user_key_kind_key
  on resume_templates (user_id, key, kind) where user_id is not null;
create unique index if not exists resume_templates_system_key_kind_key
  on resume_templates (key, kind) where user_id is null;

create index if not exists resume_templates_user_idx on resume_templates (user_id) where user_id is not null;
create index if not exists resume_templates_derived_from_idx
  on resume_templates (derived_from) where derived_from is not null;

drop trigger if exists resume_templates_set_updated_at on resume_templates;
create trigger resume_templates_set_updated_at before update on resume_templates
  for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- A4. Prompts (RG-022)
-- ---------------------------------------------------------------------------

create table if not exists resume_prompts (
  id         uuid primary key default gen_random_uuid(),
  -- Null user_id means the system default for that stage.
  user_id    uuid references app_users(id) on delete cascade,
  stage      text not null check (stage in ('targeting','generation','review','revision','ats','cover_letter')),
  body       text not null,
  version    int not null default 1,
  is_active  boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- nulls not distinct, or every system row would be unique against every other
-- system row and the seed below would duplicate on a second apply.
create unique index if not exists resume_prompts_user_stage_version_key
  on resume_prompts (user_id, stage, version) nulls not distinct;

-- At most one active version per (user_id, stage): resolution must never have
-- to choose between two live prompts.
create unique index if not exists resume_prompts_active_key
  on resume_prompts (user_id, stage) nulls not distinct where is_active;

create index if not exists resume_prompts_user_idx on resume_prompts (user_id) where user_id is not null;

drop trigger if exists resume_prompts_set_updated_at on resume_prompts;
create trigger resume_prompts_set_updated_at before update on resume_prompts
  for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- A5. Runs (RG-032)
-- ---------------------------------------------------------------------------

create table if not exists resume_runs (
  id                       uuid primary key default gen_random_uuid(),
  user_id                  uuid not null references app_users(id) on delete cascade,
  application_id           uuid not null references applications(id) on delete cascade,
  status                   text not null default 'queued'
    check (status in ('queued','running','succeeded','failed','cancelled')),
  kind                     text not null default 'generate'
    check (kind in ('generate','import','apply_keywords')),
  template_id              uuid references resume_templates(id) on delete set null,
  recommended_template_key text,
  template_reason          text,
  targeting_brief          jsonb,
  resume_review            jsonb,
  resume_score             numeric,
  cover_letter_score       numeric,
  fix_resolution_matrix    jsonb not null default '[]'::jsonb,
  revision_count           int not null default 0,
  -- Key names inside this object mirror v1's exactly and unprefixed, so the
  -- pipeline's ATS output can be written and read without a translation layer:
  -- total_score, grade, keyword_score, structural_score, semantic_score,
  -- matched, missing_required, missing_preferred, missing_nice_to_have,
  -- top_actions, hard_requirements, all_hard_met, error.
  ats                      jsonb,
  warnings                 text[] not null default '{}',
  compile_errors           jsonb not null default '{}'::jsonb,
  token_usage              jsonb not null default '{}'::jsonb,
  cost_usd                 numeric not null default 0,
  budget                   jsonb not null default '{}'::jsonb,
  error                    text,
  started_at               timestamptz,
  finished_at              timestamptz,
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);

create index if not exists resume_runs_user_idx on resume_runs (user_id, created_at desc);
create index if not exists resume_runs_application_idx on resume_runs (application_id);
create index if not exists resume_runs_template_idx on resume_runs (template_id) where template_id is not null;

drop trigger if exists resume_runs_set_updated_at on resume_runs;
create trigger resume_runs_set_updated_at before update on resume_runs
  for each row execute function set_updated_at();

create table if not exists resume_run_events (
  id         uuid primary key default gen_random_uuid(),
  run_id     uuid not null references resume_runs(id) on delete cascade,
  seq        int not null,
  node       text not null,
  status     text not null,
  label      text not null,
  payload    jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- This is the SSE replay log, so uniqueness is load-bearing rather than
-- hygienic: it is what makes a reconnect-at-seq return exactly one event.
create unique index if not exists resume_run_events_run_seq_key on resume_run_events (run_id, seq);
create index if not exists resume_run_events_run_idx on resume_run_events (run_id, seq);

-- The SSE tail listens on this channel instead of polling, so a browser sees a
-- node transition at the moment the worker records it.
create or replace function notify_resume_run_event()
returns trigger language plpgsql as $fn$
begin
  perform pg_notify('resume_run_events', new.run_id::text);
  return new;
end;
$fn$;

drop trigger if exists resume_run_events_notify on resume_run_events;
create trigger resume_run_events_notify after insert on resume_run_events
  for each row execute function notify_resume_run_event();

-- ---------------------------------------------------------------------------
-- A6. Documents (RG-006)
-- ---------------------------------------------------------------------------

create table if not exists resume_documents (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references app_users(id) on delete cascade,
  application_id uuid not null references applications(id) on delete cascade,
  run_id         uuid references resume_runs(id) on delete set null,
  kind           text not null check (kind in ('resume_tex','resume_pdf','cover_letter_tex',
                                               'cover_letter_pdf','jd','imported_resume','template_preview')),
  -- The row is the index; the bytes live under RESUME_DOCUMENTS_DIR. Nothing
  -- ever lists the directory to find a file, so a stray file on disk is inert.
  storage_path   text not null,
  byte_size      bigint not null,
  content_hash   text not null,
  content_type   text not null,
  created_at     timestamptz not null default now()
);

create unique index if not exists resume_documents_storage_path_key on resume_documents (storage_path);
create index if not exists resume_documents_lookup_idx on resume_documents (user_id, application_id, kind);
create index if not exists resume_documents_run_idx on resume_documents (run_id) where run_id is not null;

-- ---------------------------------------------------------------------------
-- A7. Keys (RG-023)
-- ---------------------------------------------------------------------------

-- There is no plaintext column here and no column that could hold one. The
-- key is decrypted in memory for the length of one call and never written back.
-- pnpm audit:persistence fails the build if a plaintext column appears.
create table if not exists resume_api_keys (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references app_users(id) on delete cascade,
  provider     text not null check (provider in ('anthropic','openai','openrouter')),
  ciphertext   bytea not null,
  last_four    text not null,
  label        text not null default 'default',
  created_at   timestamptz not null default now(),
  last_used_at timestamptz
);

create unique index if not exists resume_api_keys_user_provider_label_key
  on resume_api_keys (user_id, provider, label);
create index if not exists resume_api_keys_user_idx on resume_api_keys (user_id);

-- ---------------------------------------------------------------------------
-- A8. Evidence decisions (RG-036)
-- ---------------------------------------------------------------------------

create table if not exists resume_keyword_decisions (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references app_users(id) on delete cascade,
  application_id uuid not null references applications(id) on delete cascade,
  run_id         uuid references resume_runs(id) on delete set null,
  keyword        text not null,
  decision       text not null check (decision in ('accepted','dismissed','deferred')),
  -- Which company, project and bullet the evidence gate attached the keyword
  -- to. All three nullable: a dismissal has no evidence to point at.
  sot_company_id uuid references sot_companies(id) on delete set null,
  sot_project_id uuid references sot_projects(id) on delete set null,
  sot_bullet_id  uuid references sot_bullets(id) on delete set null,
  created_bullet boolean not null default false,
  note           text,
  created_at     timestamptz not null default now()
);

-- One decision per keyword per application: answering the gate twice for the
-- same keyword is a correction, not a second opinion.
create unique index if not exists resume_keyword_decisions_application_keyword_key
  on resume_keyword_decisions (application_id, lower(keyword));
create index if not exists resume_keyword_decisions_user_idx on resume_keyword_decisions (user_id);
create index if not exists resume_keyword_decisions_application_idx on resume_keyword_decisions (application_id);
create index if not exists resume_keyword_decisions_run_idx
  on resume_keyword_decisions (run_id) where run_id is not null;
create index if not exists resume_keyword_decisions_company_idx
  on resume_keyword_decisions (sot_company_id) where sot_company_id is not null;
create index if not exists resume_keyword_decisions_project_idx
  on resume_keyword_decisions (sot_project_id) where sot_project_id is not null;
create index if not exists resume_keyword_decisions_bullet_idx
  on resume_keyword_decisions (sot_bullet_id) where sot_bullet_id is not null;

-- ---------------------------------------------------------------------------
-- A9. Cost accounting (RG-050)
-- ---------------------------------------------------------------------------

-- Counts only. No column here may hold prompt or completion text: the point of
-- this table is to answer "what did that cost" without retaining what was said.
create table if not exists resume_llm_calls (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references app_users(id) on delete cascade,
  run_id        uuid not null references resume_runs(id) on delete cascade,
  node          text not null,
  provider      text not null,
  model         text not null,
  input_tokens  int not null default 0,
  output_tokens int not null default 0,
  cost_usd      numeric not null default 0,
  latency_ms    int,
  created_at    timestamptz not null default now()
);

create index if not exists resume_llm_calls_user_idx on resume_llm_calls (user_id, created_at desc);
create index if not exists resume_llm_calls_run_idx on resume_llm_calls (run_id);

-- ---------------------------------------------------------------------------
-- Row level security, matching 0001: defence in depth. The server connects as
-- the table owner and bypasses it; this is what saves you the day something
-- queries from the browser.
-- ---------------------------------------------------------------------------

alter table sot_companies             enable row level security;
alter table sot_projects              enable row level security;
alter table sot_bullets               enable row level security;
alter table sot_skills                enable row level security;
alter table resume_templates          enable row level security;
alter table resume_prompts            enable row level security;
alter table resume_runs               enable row level security;
alter table resume_run_events         enable row level security;
alter table resume_documents          enable row level security;
alter table resume_api_keys           enable row level security;
alter table resume_keyword_decisions  enable row level security;
alter table resume_llm_calls          enable row level security;

-- ---------------------------------------------------------------------------
-- Seed data. Generated from apps/resume-pipeline/seed by
-- plan/resume-generator tooling; the bodies are inlined verbatim because a
-- migration must not depend on a file path at apply time.
-- ---------------------------------------------------------------------------

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'frontend', 'Frontend, single page', 'single_page',
$rgseed$\documentclass[10pt]{article}

\usepackage[a4paper,margin=0.5in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage{charter}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\normalsize\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\titlespacing*{\section}{0pt}{6pt}{4pt}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlist[itemize]{leftmargin=1.4em,labelsep=0.5em,noitemsep,topsep=2pt,parsep=0pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\Large \textbf{HAMSA VARDHAN}}\\[2pt]
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\;
\href{https://linkedin.com/in/hamsa-vardhan}{\underline{LinkedIn}} \;|\;
\href{https://github.com/hamsa-vd}{\underline{GitHub}} \;|\;
\href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}}
\end{center}

\vspace{-2pt}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Frontend Software Engineer with 5+ years building high-performance web applications across product and consulting environments. Strongest in React and Angular delivery, data-heavy UI architecture, performance optimization, and reliable integration with backend platforms.
\begin{itemize}
  \item Owned frontend delivery across lean product teams and 12-engineer enterprise programs, spanning implementation, performance tuning, and release hardening.
  \item Improved user experience through bundle reduction, build-tool modernization, caching, and state-driven application architecture.
  \item Comfortable partnering across product, UX, backend, and QA, with supporting depth in Java/Spring, Node.js, GraphQL, and AWS-backed integrations.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Frontend:} React, Angular, TypeScript, JavaScript, Next.js, Gatsby, Svelte\\
\textbf{UI Architecture:} Redux, React Query, Zustand, Vite, Webpack, Storybook\\
\textbf{Backend Support:} Java (Spring), Node.js, REST APIs, GraphQL\\
\textbf{Cloud \& DevOps:} AWS, CloudFront, Docker \quad
\textbf{Databases:} PostgreSQL, MySQL, MongoDB

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Served as the sole in-house frontend engineer initially, owning UI delivery across React product areas and complex data-heavy workflows.
  \item Worked directly with product managers, business analysts, UX, and executive stakeholders to refine requirements, run demos, and translate complex workflows into usable interfaces.
  \item Reduced frontend bundle size from 13.1MB to 8MB by migrating Webpack to Vite and upgrading Node 14 to Node 20 LTS.
  \item Built and maintained modular React UI patterns for complex workflows including List Studio, improving maintainability and delivery speed.
  \item Added CloudFront WAF rules and security headers to harden the statically hosted frontend against common web attacks including SQL injection and XSS.
  \item Partnered closely with backend engineers on API contracts and BFF integrations to support reliable data-heavy user experiences.
  \item Evaluated charts, tables, design-system, and state-management options through POCs, helping shape next-gen frontend decisions across React, Vite, Storybook, React Query, and Zustand.
  \item Mentored a junior frontend engineer and interns through hands-on guidance and technical knowledge-sharing sessions.
\end{itemize}

\vspace{4pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Designed the initial UI approach for a 12-member Java/React/AWS capstone project before moving into frontend implementation.
  \item Delivered enterprise frontend features across Angular and jQuery applications for AWS marketplace and healthcare workflows.
  \item Completed a 3-month ServiceNow AWS Marketplace project in 2 weeks and received the Best Employee Award.
  \item Improved application load times through frontend profiling, optimization, and tighter integration with backend services.
  \item Integrated frontend applications with backend REST APIs and AWS Lambda/SNS-powered workflows in enterprise environments.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying AI-focused software engineering techniques including distributed system design with LLM-backed components and cloud-native orchestration.
    \item Expanding practical knowledge of AI integration, software architecture decision-making, and modern engineering workflows through ongoing coursework and hands-on application.
    \item Studying how modern frontend and full-stack delivery can incorporate AI capabilities without sacrificing maintainability, performance, or production readiness.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in Electronics and Communication Engineering (ECE)}{2020}\\
SRM University, Chennai, India

\end{document}
$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'backend-java', 'Backend Java, single page', 'single_page',
$rgseed$\documentclass[10pt]{article}

\usepackage[a4paper,margin=0.5in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage{charter}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\normalsize\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\titlespacing*{\section}{0pt}{6pt}{4pt}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlist[itemize]{leftmargin=1.4em,labelsep=0.5em,noitemsep,topsep=2pt,parsep=0pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\Large \textbf{HAMSA VARDHAN}}\\[2pt]
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\;
\href{https://linkedin.com/in/hamsa-vardhan}{\underline{LinkedIn}} \;|\;
\href{https://github.com/hamsa-vd}{\underline{GitHub}} \;|\;
\href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}}
\end{center}

\vspace{-2pt}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Backend Software Engineer with 5+ years building Java-based APIs, Spring services, and cloud-native backend systems across product and consulting environments. Strongest in backend ownership, authentication systems, observability, and scalable AWS-backed delivery.
\begin{itemize}
  \item Built backend systems across lean product teams and 12-engineer enterprise deliveries, owning APIs, search, auth, and infrastructure concerns.
  \item Hands-on depth in Java, Spring Boot, Spring MVC, Spring Gateway, PostgreSQL, Docker, AWS, and messaging-driven integrations.
  \item Experienced improving reliability and security through JWT-based access control, Keycloak/Auth0 migrations, Prometheus/Grafana monitoring, and distributed architecture decisions.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Backend:} Java (8/11/17), Spring Boot, Spring MVC, Spring Gateway, REST APIs, Microservices\\
\textbf{Security:} JWT, OAuth2/OIDC, RBAC, Auth0, Keycloak, Okta\\
\textbf{Cloud \& DevOps:} AWS (EC2, Lambda, ECS, EKS, CloudFront, S3), Docker, Kubernetes, Jenkins CI/CD\\
\textbf{Databases:} PostgreSQL, MySQL, MongoDB, Redis\\
\textbf{Messaging:} Apache Kafka, RabbitMQ \quad
\textbf{Observability:} Prometheus, Grafana

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Engineered Java Spring backend services and REST APIs supporting internal operations and external integrations across distributed systems.
  \item Migrated search infrastructure from Lucene to AWS OpenSearch, cutting search latency from \raise.17ex\hbox{$\scriptstyle\sim$}3s to \raise.17ex\hbox{$\scriptstyle\sim$}300ms while expanding queryable properties by 6x.
  \item Architected Keycloak-based SSO replacing Auth0, and migrated API key/secret authentication to JWT-based validation across Spring Gateway and auth microservices.
  \item Introduced Prometheus and Grafana observability stack, eliminating manual log debugging and enabling proactive alerting across Dockerized services.
  \item Deployed and supported containerized services on AWS ECS while contributing to next-gen backend architecture built around Kafka and EKS.
  \item Optimized AWS CloudFront with WAF rules and caching strategies, improving delivery performance and hardening platform security.
  \item Built Django and FastAPI services for internal tooling and automation, extending backend support beyond the core Java service ecosystem.
\end{itemize}

\vspace{4pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Delivered Java Spring Boot backend services across full-stack capstone and enterprise healthcare projects running on AWS.
  \item Built authentication workflows using Okta with JWT and OIDC for secure access control in a 12-member team environment.
  \item Engineered AWS Lambda and SNS-based alerting services, improving reliability across healthcare workflows.
  \item Resolved PostgreSQL race conditions and deadlock issues in production while coordinating across QA, security, and DevOps teams.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying AI-focused software engineering techniques including distributed system design with LLM-backed components and cloud-native orchestration.
    \item Expanding practical knowledge of AI integration, software architecture decision-making, and modern engineering workflows through ongoing coursework and hands-on application.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in Electronics and Communication Engineering (ECE)}{2020}\\
SRM University, Chennai, India

\end{document}
$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'backend-python', 'Backend Python, single page', 'single_page',
$rgseed$\documentclass[10pt]{article}

\usepackage[a4paper,margin=0.5in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage{charter}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\normalsize\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\titlespacing*{\section}{0pt}{6pt}{4pt}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlist[itemize]{leftmargin=1.4em,labelsep=0.5em,noitemsep,topsep=2pt,parsep=0pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\Large \textbf{HAMSA VARDHAN}}\\[2pt]
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\;
\href{https://linkedin.com/in/hamsa-vardhan}{\underline{LinkedIn}} \;|\;
\href{https://github.com/hamsa-vd}{\underline{GitHub}} \;|\;
\href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}}
\end{center}

\vspace{-2pt}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Python Backend Engineer with 5+ years building Django/FastAPI services, automation workflows, and cloud-native APIs across product and consulting environments. Strongest in Python service development, AI-enabled integrations, and AWS-backed backend delivery.
\begin{itemize}
  \item Built Python services for internal tooling, automation, and AI workflows across lean product teams and enterprise programs.
  \item Hands-on depth in Django, FastAPI, REST APIs, LangChain, RAG pipelines, PostgreSQL, Docker, and AWS-based deployment patterns.
  \item Experienced partnering with product, data, and engineering teams to ship secure, scalable services that reduce manual business processes and improve delivery efficiency.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Backend:} Python, Django, FastAPI, Flask, REST APIs, Microservices\\
\textbf{AI Integration:} LangChain, OpenAI integrations, RAG pipelines, Embedding-based retrieval\\
\textbf{Cloud \& DevOps:} AWS (EC2, Lambda, ECS, CloudFront, S3), Docker, Kubernetes\\
\textbf{Databases:} PostgreSQL, MySQL, MongoDB, Redis\\
\textbf{Messaging:} Apache Kafka, RabbitMQ \quad
\textbf{Observability:} Prometheus, Grafana

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Built Django-based internal tools and FastAPI services supporting internal data workflows and lightweight AI-enabled use cases.
  \item Delivered automation for finance and logistics processes that reduced business workflows from days to hours through backend services and schedulers.
  \item Developed Python utilities for infrastructure automation, API key rotation, and operational monitoring across AWS-backed services.
  \item Introduced Prometheus and Grafana observability stack, eliminating manual log debugging and enabling proactive alerting across Dockerized services.
  \item Migrated search infrastructure from Lucene to AWS OpenSearch, cutting search latency from \raise.17ex\hbox{$\scriptstyle\sim$}3s to \raise.17ex\hbox{$\scriptstyle\sim$}300ms for richer search workflows.
  \item Strengthened API security by supporting JWT-based authentication and validation flows across backend services.
  \item Worked across Python, Java, and Node-based service boundaries to support distributed systems and cloud-native platform delivery.
\end{itemize}

\vspace{4pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Delivered backend functionality using Python alongside Java and .NET services across enterprise healthcare systems.
  \item Built AWS Lambda and SNS-based alerting workflows to improve operational visibility and reliability.
  \item Resolved PostgreSQL race conditions and deadlock issues in production, strengthening data consistency in high-traffic modules.
  \item Worked closely with DevOps, QA, and security teams while supporting enterprise delivery across multiple backend stacks.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying AI-focused software engineering techniques including distributed system design with LLM-backed components and cloud-native orchestration.
    \item Expanding practical knowledge of AI integration, software architecture decision-making, and modern engineering workflows through ongoing coursework and hands-on application.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in Electronics and Communication Engineering (ECE)}{2020}\\
SRM University, Chennai, India

\end{document}
$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'fullstack', 'Fullstack, single page', 'single_page',
$rgseed$\documentclass[10pt]{article}

\usepackage[a4paper,margin=0.5in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage{charter}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\normalsize\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\titlespacing*{\section}{0pt}{6pt}{4pt}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlist[itemize]{leftmargin=1.4em,labelsep=0.5em,noitemsep,topsep=2pt,parsep=0pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\Large \textbf{HAMSA VARDHAN}}\\[2pt]
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\;
\href{https://linkedin.com/in/hamsa-vardhan}{\underline{LinkedIn}} \;|\;
\href{https://github.com/hamsa-vd}{\underline{GitHub}} \;|\;
\href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}}
\end{center}

\vspace{-2pt}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Backend-leaning Full-Stack Software Engineer with 5+ years delivering secure, cloud-native products across product and consulting environments. Strongest in backend ownership, authentication systems, and scalable integrations, with hands-on depth across React, Java (Spring), Python, and AWS.
\begin{itemize}
  \item Built end-to-end systems across lean product teams and 12-engineer enterprise deliveries, spanning UI, BFF, API, observability, and AWS infrastructure layers.
  \item Authentication and authorization specialist with hands-on experience in JWT, OAuth2/OIDC, RBAC, Auth0, Keycloak, and Okta.
  \item Experienced in microservices, event-driven architecture, GraphQL integrations, and AI-enabled automation; mentored 3 junior/intern engineers while partnering with product, QA, security, and analysts.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Frontend:} React.js, Redux, Angular, TypeScript, JavaScript \quad
\textbf{Backend:} Java (Spring Boot), Python (Django, FastAPI), Node.js, REST APIs, Microservices\\
\textbf{Cloud \& DevOps:} AWS (EC2, Lambda, ECS, EKS, CloudFront, S3), Docker, Kubernetes, Jenkins CI/CD \quad
\textbf{Databases:} PostgreSQL, MySQL, MongoDB, Redis\\
\textbf{Messaging:} Apache Kafka, RabbitMQ \quad
\textbf{Observability:} Prometheus, Grafana \quad
\textbf{AI:} LangChain, RAG pipelines, Embedding-based retrieval

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Led full-stack feature delivery across 12 Agile sprints, reducing delivery timelines by 20\% through end-to-end ownership from UI to backend APIs and cloud deployment.
  \item Migrated search infrastructure from Lucene to AWS OpenSearch, cutting search latency from \raise.17ex\hbox{$\scriptstyle\sim$}3s to \raise.17ex\hbox{$\scriptstyle\sim$}300ms while expanding queryable properties by 6x.
  \item Architected Keycloak-based SSO replacing Auth0, and migrated API key/secret auth to JWT-based validation across Spring Gateway and auth microservices.
  \item Introduced Prometheus and Grafana observability stack, eliminating manual log debugging and enabling proactive alerting across Dockerized services.
  \item Reduced frontend bundle size from 13.1MB to 8MB by migrating Webpack to Vite and upgrading Node 14 to Node 20 LTS.
  \item Optimized AWS CloudFront with WAF rules and caching strategies, achieving 40\% faster content distribution and hardened security posture.
  \item Drove next-gen architecture decisions with senior architects -- React/Vite frontend, Kafka event-driven backend, EKS orchestration.
  \item Built Django and FastAPI services for internal tooling and AI-driven workflows; delivered automation reducing business processes from days to hours.
\end{itemize}

\vspace{4pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Delivered full-stack features combining Angular/React frontends with Java Spring Boot and Python backend APIs across enterprise healthcare and AWS marketplace projects.
  \item Engineered AWS Lambda-based serverless services and SNS alerting pipelines, reducing infrastructure costs by 10\% and improving system reliability.
  \item Resolved PostgreSQL race conditions and deadlock issues in production, strengthening database performance across high-traffic healthcare modules.
  \item Completed a 3-month ServiceNow AWS Marketplace integration in 2 weeks; recognized with Best Employee Award.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying AI-focused software engineering techniques including distributed system design with LLM-backed components and cloud-native orchestration.
    \item Expanding practical knowledge of AI integration, software architecture decision-making, and modern engineering workflows through ongoing coursework and hands-on application.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in Electronics and Communication Engineering (ECE)}{2020}\\
SRM University, Chennai, India

\end{document}
$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'senior-engineer', 'Senior engineer, single page', 'single_page',
$rgseed$\documentclass[10pt]{article}

\usepackage[a4paper,margin=0.5in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage{charter}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\normalsize\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\titlespacing*{\section}{0pt}{6pt}{4pt}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlist[itemize]{leftmargin=1.4em,labelsep=0.5em,noitemsep,topsep=2pt,parsep=0pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\Large \textbf{HAMSA VARDHAN}}\\[2pt]
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\;
\href{https://linkedin.com/in/hamsa-vardhan}{\underline{LinkedIn}} \;|\;
\href{https://github.com/hamsa-vd}{\underline{GitHub}} \;|\;
\href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}}
\end{center}

\vspace{-2pt}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Software Engineer with 5+ years of progressive experience delivering scalable, production-grade systems across React, Java (Spring), Python, and AWS. Strongest in end-to-end ownership, platform modernization, security, and architecture influence across product and consulting environments.
\begin{itemize}
  \item Led initiatives across lean product teams and 12-engineer delivery groups, spanning UI, APIs, search, observability, and cloud infrastructure.
  \item Drove performance, security, and reliability improvements through OpenSearch migration, JWT/SSO modernization, Prometheus/Grafana monitoring, and AWS hardening.
  \item Mentored 3 junior/intern engineers and partnered with architects, product, QA, security, and analysts to shape scalable delivery.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Frontend Architecture:} React, Angular, TypeScript, Redux, Vite\\
\textbf{Backend Systems:} Java (Spring Boot, Spring MVC), Python (Django, FastAPI), REST APIs, Microservices\\
\textbf{Cloud \& Infrastructure:} AWS (EC2, ECS, EKS, Lambda, CloudFront, S3), Docker, Kubernetes\\
\textbf{Security \& Integration:} JWT, OAuth2/OIDC, Auth0, Keycloak, BFF, GraphQL\\
\textbf{Data \& Messaging:} PostgreSQL, MySQL, MongoDB, Redis, Apache Kafka, RabbitMQ

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Led full-stack feature delivery across 12 Agile sprints, reducing delivery timelines by 20\% through end-to-end ownership from UI to backend APIs and cloud deployment.
  \item Migrated search infrastructure from Lucene to AWS OpenSearch, cutting search latency from \raise.17ex\hbox{$\scriptstyle\sim$}3s to \raise.17ex\hbox{$\scriptstyle\sim$}300ms while expanding queryable properties by 6x.
  \item Architected Keycloak-based SSO replacing Auth0, and migrated API key/secret authentication to JWT-based validation across Spring Gateway and auth microservices.
  \item Introduced Prometheus and Grafana observability stack, eliminating manual log debugging and enabling proactive alerting across Dockerized services.
  \item Reduced frontend bundle size from 13.1MB to 8MB by migrating Webpack to Vite and upgrading Node 14 to Node 20 LTS.
  \item Optimized AWS CloudFront with WAF rules and caching strategies, achieving 40\% faster content distribution and hardened security posture.
  \item Drove next-gen architecture decisions with senior architects across React/Vite frontend, Kafka event-driven backend, EKS orchestration, and Keycloak-based authentication.
  \item Built Django and FastAPI services for internal tooling and automation while mentoring junior engineers and interns across ongoing delivery.
\end{itemize}

\vspace{4pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Delivered full-stack features combining Angular/React frontends with Java Spring Boot and Python backend APIs across enterprise healthcare and AWS marketplace projects.
  \item Built authentication workflows using Okta with JWT and OIDC while operating in a 12-member team environment.
  \item Engineered AWS Lambda-based serverless services and SNS alerting pipelines, improving reliability across enterprise workflows.
  \item Completed a 3-month ServiceNow AWS Marketplace integration in 2 weeks; recognized with Best Employee Award.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying AI-focused software engineering techniques including distributed system design with LLM-backed components and cloud-native orchestration.
    \item Expanding practical knowledge of AI integration, software architecture decision-making, and modern engineering workflows through ongoing coursework and hands-on application.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in Electronics and Communication Engineering (ECE)}{2020}\\
SRM University, Chennai, India

\end{document}
$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'frontend', 'Frontend, multi page', 'multi_page',
$rgseed$\documentclass[11pt]{article}

\usepackage[a4paper,margin=1in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\large\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\setlength{\parindent}{0pt}
\setlist[itemize]{leftmargin=1.6em,labelsep=0.6em,noitemsep,topsep=4pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\LARGE \textbf{HAMSA VARDHAN}}\\
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\; \href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}} \\
{\small Requires visa sponsorship until End of 2027}
\end{center}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Frontend Engineer with 5+ years of experience delivering high-performance web applications using React, Angular, TypeScript, and modern JavaScript frameworks. Strong focus on UI architecture, performance optimisation, and scalable frontend systems integrated with cloud-based microservices.

\begin{itemize}
    \item Delivered end-to-end frontend features improving release velocity by \textbf{20\%}.
    \item Engineered component-driven architectures enabling scalable UI development across large applications.
    \item Optimised frontend performance achieving up to \textbf{25\%} faster load times and improved user experience.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Frontend:} React.js, Redux, Angular, Next.js, Vue.js, Svelte, TypeScript, JavaScript.\\
\textbf{Backend (Working Knowledge):} Java (Spring), Node.js, REST APIs.\\
\textbf{Cloud \& DevOps:} AWS, Docker, CloudFront.\\
\textbf{Databases:} PostgreSQL, MySQL, MongoDB.

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Led frontend delivery across \textbf{12} Agile sprints, accelerating feature rollout timelines by \textbf{20\%}.
  \item Architected modular React component systems, improving code reusability and reducing development effort by \textbf{30\%}.
  \item Optimised application bundle size from \textbf{13.1MB to 8MB} (39\% reduction), significantly improving load performance.
  \item Enhanced state management using Redux and modern hooks, ensuring consistent application behaviour at scale.
  \item Improved rendering performance by eliminating unnecessary re-renders, increasing UI responsiveness by \textbf{15\%}.
  \item Strengthened content delivery performance using AWS CloudFront and caching strategies, achieving \textbf{40\%} faster asset delivery.
  \item Coordinated closely with backend teams to align API contracts, reducing integration issues by \textbf{25\%}.
\end{itemize}

\vspace{12pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Engineered enterprise web interfaces using Angular and Vue.js, improving feature delivery speed by \textbf{20\%}.
  \item Reduced page load times by \textbf{25\%} through frontend profiling and performance optimisation.
  \item Developed reusable UI modules, decreasing duplicate code and improving maintainability by \textbf{30\%}.
  \item Integrated frontend applications with backend REST APIs and AWS Lambda services, ensuring reliable data flow across systems.
\end{itemize}

%------------------------
\section*{PROJECT EXPERIENCE}

\textbf{AI Question Bank Generator (RAG Pipeline)}
\begin{itemize}
    \item Integrated LLM-driven responses into frontend workflows, enabling dynamic and context-aware UI rendering.
    \item Structured semantic retrieval outputs for intuitive user interaction and improved response relevance.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program (Ongoing)}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying AI integration techniques including token lifecycle management and structured prompt workflows.
    \item Designing frontend-driven systems that incorporate LLM-backed components while maintaining performance and cost efficiency.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in ECE}{2020}\\
SRM University, Chennai, India

\end{document}$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'backend-java', 'Backend Java, multi page', 'multi_page',
$rgseed$\documentclass[11pt]{article}

\usepackage[a4paper,margin=1in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\large\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\setlength{\parindent}{0pt}
\setlist[itemize]{leftmargin=1.6em,labelsep=0.6em,noitemsep,topsep=4pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\LARGE \textbf{HAMSA VARDHAN}}\\
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\; \href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}} \\
{\small Requires visa sponsorship until End of 2027}
\end{center}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Backend Engineer specialising in Java and Spring ecosystems with 5+ years of experience building scalable microservices, high-performance APIs, and cloud-native backend systems. Strong expertise in distributed architectures, concurrency handling, and AWS-based deployments supporting production-grade enterprise platforms.

\begin{itemize}
    \item Delivered backend systems improving response performance by \textbf{25\%} through API and query optimisation.
    \item Engineered microservices architectures enabling scalable and fault-tolerant backend systems.
    \item Reduced infrastructure costs by \textbf{10\%} through serverless and containerised deployments.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Backend (Primary):} Java (8/11/17), Spring Boot, Spring MVC, REST APIs, Multithreading, Microservices.\\
\textbf{Cloud \& DevOps:} AWS (EC2, Lambda, ECS, CloudFront), Docker, Kubernetes.\\
\textbf{Databases:} PostgreSQL, MySQL, MongoDB, Cassandra.\\
\textbf{Messaging:} Apache Kafka, ActiveMQ.\\
\textbf{Frontend (Supporting):} React.js, Redux.\\

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Engineered and maintained Java Spring-based backend services supporting high-traffic distributed systems.
  \item Architected REST APIs for internal and external integrations, improving data throughput and system scalability.
  \item Optimised backend processing and database interactions, improving API response times by \textbf{25\%}.
  \item Deployed containerised microservices using Docker on AWS ECS, enabling scalable and resilient service execution.
  \item Migrated search infrastructure to AWS OpenSearch, reducing query latency from \textbf{2--3 seconds to under 300ms}.
  \item Strengthened authentication mechanisms by transitioning to JWT-based security models, improving system reliability and access control.
  \item Improved content delivery performance by \textbf{40\%} through backend-aware caching and CloudFront optimisation.
  \item Mentored junior engineers and conducted code reviews, improving code quality and team delivery efficiency.
  \item Influenced system design decisions across a cross-functional team of \textbf{12 engineers}, shaping backend architecture and service boundaries.
\end{itemize}

\vspace{12pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Delivered backend services using Java Spring, enabling seamless integration with frontend and enterprise systems.
  \item Reduced application load times by \textbf{25\%} through backend optimisation and efficient query handling.
  \item Provisioned AWS Lambda-based services, decreasing infrastructure costs by \textbf{10\%}.
  \item Improved system reliability, lowering defect rates by \textbf{20\%} through structured validation and testing practices.
  \item Coordinated API integrations with frontend teams, reducing data inconsistencies and deployment issues.
\end{itemize}

%------------------------
\section*{PROJECT EXPERIENCE}

\textbf{AI Question Bank Generator (RAG Pipeline)}
\begin{itemize}
    \item Designed backend workflows integrating AI-driven retrieval systems with application services.
    \item Engineered scalable processing pipelines enabling semantic query handling and context-aware responses.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program (Ongoing)}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying backend-focused AI integration techniques including token lifecycle management and structured prompt workflows.
    \item Designing distributed backend architectures supporting scalable and event-driven systems.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in ECE}{2020}\\
SRM University, Chennai, India

\end{document}$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'backend-python', 'Backend Python, multi page', 'multi_page',
$rgseed$\documentclass[11pt]{article}

\usepackage[a4paper,margin=1in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\large\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\setlength{\parindent}{0pt}
\setlist[itemize]{leftmargin=1.6em,labelsep=0.6em,noitemsep,topsep=4pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\LARGE \textbf{HAMSA VARDHAN}}\\
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\; \href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}} \\
{\small Requires visa sponsorship until End of 2027}
\end{center}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Backend Engineer specialising in Python-based systems with 5+ years of experience building scalable APIs, AI-integrated backend workflows, and cloud-native microservices. Strong expertise in Django for enterprise API systems and FastAPI for lightweight, high-performance services supporting AI-driven use cases.

\begin{itemize}
    \item Delivered backend systems improving response performance by \textbf{25\%} through API and database optimisation.
    \item Engineered AI-enabled services leveraging FastAPI to support retrieval and LLM-powered workflows.
    \item Reduced infrastructure costs by \textbf{10\%} using serverless and cloud-native backend architectures.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Backend (Primary):} Python, Django, FastAPI, REST API Design, Data Modeling, Microservices.\\
\textbf{AI Integration:} LangChain, RAG pipelines, Embedding-based retrieval.\\
\textbf{Cloud \& DevOps:} AWS (EC2, Lambda, ECS, CloudFront), Docker, Kubernetes.\\
\textbf{Databases:} PostgreSQL, MySQL, MongoDB, Cassandra.\\
\textbf{Frontend (Supporting):} React.js, Redux.\\
\textbf{Messaging:} Apache Kafka, ActiveMQ.

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Engineered and maintained Python-based REST APIs supporting high-traffic internal and external systems across distributed services.
  \item Architected FastAPI microservices powering AI-driven workflows, eliminating multi-day manual processes for finance and logistics teams.
  \item Optimised API response handling and database queries, improving backend performance by \textbf{25\%}.
  \item Deployed containerised backend services using Docker on AWS ECS, enabling scalable and fault-tolerant service execution.
  \item Migrated search infrastructure to AWS OpenSearch, reducing query latency from \textbf{2--3 seconds to under 300ms}.
  \item Strengthened API security by enabling JWT-based authentication and improving token validation workflows.
  \item Improved content delivery performance by \textbf{40\%} through backend-aware caching strategies and AWS CloudFront optimisation.
  \item Mentored junior engineers and guided backend best practices, improving team productivity and code quality.
\end{itemize}

\vspace{12pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Delivered backend APIs using Python and Java-based services, enabling seamless frontend integration across enterprise applications.
  \item Reduced application load times by \textbf{25\%} through backend optimisation and efficient query handling.
  \item Provisioned AWS Lambda services, decreasing infrastructure costs by \textbf{10\%}.
  \item Improved application reliability, lowering defect rates by \textbf{20\%} through structured validation and testing strategies.
  \item Coordinated API integrations with frontend teams, reducing data inconsistencies and integration issues.
\end{itemize}

%------------------------
\section*{PROJECT EXPERIENCE}

\textbf{AI Question Bank Generator (RAG Pipeline)}
\begin{itemize}
    \item Designed Python-based backend system using LangChain and PostgreSQL vector storage for scalable semantic retrieval.
    \item Engineered retrieval pipelines integrating LLM outputs into application workflows, enabling context-aware generation.
    \item Structured asynchronous processing pipelines to support scalable AI workloads across document embeddings.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program (Ongoing)}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying AI-focused backend engineering practices including token lifecycle management and structured prompt workflows.
    \item Designing distributed backend systems integrating LLM-backed components into scalable architectures.
    \item Advancing cloud-native backend design and service orchestration expertise.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in ECE}{2020}\\
SRM University, Chennai, India

\end{document}$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'fullstack', 'Fullstack, multi page', 'multi_page',
$rgseed$\documentclass[11pt]{article}

\usepackage[a4paper,margin=1in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\large\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\setlength{\parindent}{0pt}
\setlist[itemize]{leftmargin=1.6em,labelsep=0.6em,noitemsep,topsep=4pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\LARGE \textbf{HAMSA VARDHAN}}\\
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\; \href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}} \\
{\small Requires visa sponsorship until End of 2027}
\end{center}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Full-Stack Software Engineer with 5+ years of experience delivering end-to-end web applications across React, Angular, Java (Spring), Python (Django/FastAPI), Docker, and AWS environments. Experienced in designing scalable frontend architectures, building robust backend APIs, deploying containerised microservices, and integrating AI-enabled workflows into production systems.

\begin{itemize}
    \item Delivered complete feature lifecycles from UI implementation to backend API design and cloud deployment.
    \item Architected microservices-based systems supporting scalable, distributed application environments.
    \item Integrated AI-powered backend workflows using retrieval-based architectures and LLM-driven services.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Frontend:} React.js, Redux, Angular, TypeScript, JavaScript.\\
\textbf{Backend:} Java (Spring), Python (Django, FastAPI), REST APIs, Microservices.\\
\textbf{Cloud \& DevOps:} AWS (EC2, Lambda, ECS, CloudFront), Docker, Kubernetes.\\
\textbf{Databases:} PostgreSQL, MySQL, MongoDB, Cassandra.\\
\textbf{Messaging:} Apache Kafka, ActiveMQ.\\
\textbf{AI Integration:} LangChain, RAG pipelines, Embedding-based retrieval.

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Led full-stack feature delivery across \textbf{12} Agile sprints, cutting delivery timelines by \textbf{20\%}.
  \item Architected modular React-based frontend components, slashing bundle size from \textbf{13.1MB to 8MB} (39\% reduction) and accelerating development build speeds.
  \item Engineered and maintained REST APIs in Java and Python supporting internal operations and external integrations across distributed services.
  \item Launched FastAPI microservices for lightweight internal tooling and AI-driven workflows, eliminating multi-day manual processes for finance and logistics teams.
  \item Deployed Dockerized backend services on AWS ECS with CloudFormation, enabling independent scaling across service boundaries.
  \item Migrated Lucene-based search to AWS OpenSearch, reducing query latency from \textbf{2--3 seconds to under 300ms} across \textbf{6+} indexed wine properties.
  \item Optimised AWS CloudFront configuration and caching strategies, achieving \textbf{40\%} faster content delivery while hardening WAF rules against SQL injection and XSS attacks.
  \item Elevated authentication security by transitioning from API key access to Auth0 JWT tokens, later migrating to self-hosted Keycloak SSO for greater control and cost reduction.
  \item Mentored \textbf{3 engineers} (1 junior developer, 2 IT analyst interns) through regular code reviews, pair programming, and technical knowledge-sharing sessions.
  \item Guided architectural planning for next-generation platform with a cross-functional team of \textbf{12 engineers} and \textbf{2 architects}, influencing stack selection and service design decisions.
\end{itemize}

\vspace{12pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Crafted full-stack features spanning Angular/Vue frontends and Java Spring backend REST APIs, routinely delivering ahead of sprint estimates.
  \item Slashed page load times by \textbf{25\%} through coordinated frontend optimisation and backend query tuning.
  \item Provisioned AWS Lambda-based backend services, trimming infrastructure costs by \textbf{10\%}.
  \item Strengthened application reliability, reducing defect rates by \textbf{20\%} through structured testing and peer review processes.
  \item Coordinated frontend build releases with backend service deployments, streamlining CI/CD delivery and winning the \textbf{Best Employee Award} for delivering a 3-month project in \textbf{2 weeks}.
\end{itemize}

%------------------------
\section*{PROJECT EXPERIENCE}

\textbf{AI Question Bank Generator (RAG Pipeline)}
\begin{itemize}
    \item Designed a full-stack AI-powered question bank system using Python, LangChain, and PostgreSQL vector storage, enabling infinite scalable knowledge generation.
    \item Engineered backend retrieval pipelines integrating LLM-generated outputs into application workflows via semantic search, delivering context-aware question synthesis.
    \item Established asynchronous and event-driven processing flows for scalable AI workload handling across multi-source document embeddings.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program (Ongoing)}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying AI-focused software engineering techniques including token lifecycle management and structured prompt engineering within production-grade architectures.
    \item Designing distributed systems capable of integrating LLM-backed components into scalable backend architectures.
    \item Advancing cloud-native deployment and service orchestration expertise with emphasis on AI-integrated production systems.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in Electronics \& Communication Engineering}{2016 -- 2020}\\
SRM University, Chennai, India

\end{document}
$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_templates (user_id, key, name, kind, tex_source, is_system)
values (null, 'senior-engineer', 'Senior engineer, multi page', 'multi_page',
$rgseed$\documentclass[11pt]{article}

\usepackage[a4paper,margin=1in]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}

\definecolor{sectioncolor}{RGB}{0,102,102}

\titleformat{\section}
  {\large\bfseries\color{sectioncolor}}
  {}
  {0em}
  {}
  [\titlerule]

\setlength{\parindent}{0pt}
\setlist[itemize]{leftmargin=1.6em,labelsep=0.6em,noitemsep,topsep=4pt}

\newcommand{\resumeHeader}[2]{%
  \noindent\makebox[\textwidth][l]{%
    \parbox[t]{0.78\textwidth}{\textbf{#1}}%
    \hfill
    #2%
  }%
}

\begin{document}

\begin{center}
{\LARGE \textbf{HAMSA VARDHAN}}\\
London, UK \;|\; +44 07767930695 \;|\;
\href{mailto:hamsavardhan99@gmail.com}{hamsavardhan99@gmail.com} \;|\; \href{https://calendly.com/hamsa-vd/intro-call}{\underline{Calendly}} \\
{\small Requires visa sponsorship until End of 2027}
\end{center}

%------------------------
\section*{PROFESSIONAL SUMMARY}

Senior Software Engineer with 5+ years of experience delivering scalable, production-grade systems across React, Angular, Java (Spring), Python (Django/FastAPI), and AWS environments. Strong track record of owning end-to-end delivery, shaping microservices architectures, optimising system performance, and integrating AI-driven workflows into modern platforms.

\begin{itemize}
    \item Drove architecture decisions across distributed microservices systems spanning frontend and backend layers.
    \item Delivered measurable impact including \textbf{20\%} faster release cycles, \textbf{25\%} performance gains, and \textbf{40\%} faster content delivery.
    \item Enabled AI-powered backend workflows using RAG pipelines and LLM-integrated services.
\end{itemize}

%------------------------
\section*{TECHNICAL SKILL SET}

\textbf{Frontend Architecture:} React.js, Redux, Angular, TypeScript, Component Design.\\
\textbf{Backend Systems:} Java (Spring Boot, Spring MVC), Python (Django, FastAPI), REST APIs, Microservices, Concurrency.\\
\textbf{Cloud \& Infrastructure:} AWS (EC2, ECS, Lambda, CloudFront), Docker, Kubernetes.\\
\textbf{Data Layer:} PostgreSQL, MySQL, MongoDB, Cassandra.\\
\textbf{Messaging \& Integration:} Apache Kafka, ActiveMQ.\\
\textbf{AI Integration:} LangChain, RAG pipelines, Embedding-based retrieval.

%------------------------
\section*{WORK EXPERIENCE}

\resumeHeader{Software Engineer}{Aug 2022 -- Present}\\
\textit{Liv-Ex, London, UK}
\noindent
\begin{itemize}
  \item Led end-to-end delivery across \textbf{12} Agile sprints, accelerating release velocity by \textbf{20\%}.
  \item Architected microservices-based systems across React frontend and Java/Python backend services, improving scalability and maintainability.
  \item Engineered REST APIs supporting internal operations and external integrations across distributed systems.
  \item Launched FastAPI services enabling AI-driven workflows, eliminating multi-day manual processes.
  \item Optimised overall system performance by \textbf{25\%} through frontend rendering improvements and backend query tuning.
  \item Reduced search latency from \textbf{2--3 seconds to under 300ms} by migrating to AWS OpenSearch.
  \item Strengthened authentication by transitioning to JWT-based security and implementing Keycloak-based SSO.
  \item Improved content delivery by \textbf{40\%} using CloudFront caching and WAF security enhancements.
  \item Mentored \textbf{3 engineers}, improving onboarding speed and code quality through structured guidance.
  \item Influenced system design decisions within a cross-functional team of \textbf{12 engineers}.
\end{itemize}

\vspace{12pt}

\resumeHeader{Junior Software Engineer}{Jan 2021 -- Jul 2022}\\
\textit{Presidio, Chennai, India}
\noindent
\begin{itemize}
  \item Delivered full-stack enterprise features across Angular/Vue and Java Spring backend systems, exceeding sprint expectations.
  \item Reduced application load times by \textbf{25\%} through frontend optimisation and backend query improvements.
  \item Provisioned AWS Lambda services, reducing infrastructure costs by \textbf{10\%}.
  \item Improved system reliability by reducing defects by \textbf{20\%} through testing and review practices.
  \item Streamlined CI/CD delivery, completing a 3-month project in \textbf{2 weeks} and earning Best Employee recognition.
\end{itemize}

%------------------------
\section*{PROJECT EXPERIENCE}

\textbf{AI Question Bank Generator (RAG Pipeline)}
\begin{itemize}
    \item Architected a full-stack AI system using Python, LangChain, and PostgreSQL vector storage.
    \item Engineered retrieval pipelines integrating LLM outputs into application workflows.
    \item Designed asynchronous processing flows for scalable AI workload handling.
\end{itemize}

%------------------------
\section*{PROFESSIONAL DEVELOPMENT}

\resumeHeader{New Age Software Engineering Program (Ongoing)}{Nov 2025 -- May 2026}\\
Masai School in collaboration with IIT Roorkee
\noindent
\begin{itemize}
    \item Applying advanced AI engineering techniques including token lifecycle management and prompt orchestration.
    \item Designing distributed systems integrating LLM-backed components into scalable architectures.
    \item Strengthening cloud-native system design and orchestration expertise.
\end{itemize}

%------------------------
\section*{EDUCATION}

\resumeHeader{B.Tech in ECE}{2020}\\
SRM University, Chennai, India

\end{document}$rgseed$,
true)
on conflict (key, kind) where user_id is null do nothing;

insert into resume_prompts (user_id, stage, body, version, is_active)
values (null, 'targeting',
$rgseed$You are a senior technical recruiter and resume strategist.

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
$rgseed$,
1, true)
on conflict (user_id, stage, version) do nothing;

insert into resume_prompts (user_id, stage, body, version, is_active)
values (null, 'generation',
$rgseed$You are implementing a pre-approved resume strategy inside a LaTeX template. You are NOT analysing the job or figuring out the role. That work is already done. Your job is precise, disciplined implementation.

Return only a complete LaTeX document. Do not wrap it in Markdown.

---

TARGETING BRIEF (implement this exactly):
{{TARGETING_BRIEF}}

---

Job description:
{{JD_TEXT}}

Selected base resume LaTeX:
{{BASE_RESUME_TEX}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

---

Implementation rules:

STRUCTURE
- Preserve the base resume's documentclass, packages, macros, section order, and formatting exactly.
- Do not change section names, column layout, or spacing commands.
- Output a complete, valid LaTeX document.

CONTENT
- Use the targeting brief's positioning_statement to shape the professional summary.
- Use grounded_keywords confidently throughout skills and bullets.
- For learning_signal_keywords: use adjacent evidence from source of truth, or frame as willingness/exposure. Never fabricate.
- Do not include anything in forbidden_claims. If a forbidden item is in the base resume, remove it.
- Replace seniority_verbs_to_avoid with seniority_verbs_to_use consistently across all bullets.
- Every bullet must map to a specific entry in the evidence_map. If a JD requirement has candidate_evidence, reflect it. If not, do not invent it.
- Follow keyword_strategy exactly: confident for has_evidence=true, adjacent/framed for false, absent for "do not claim".

TONE
- The entire document must match the brief's tone field.
- This is not negotiable. If the brief says "collaborative, learning-oriented," every ownership-heavy or solo-credit phrase must be rewritten.

CREDIBILITY
- Do not invent companies, titles, dates, degrees, certifications, projects, or metrics.
- Do not round up metrics unless source of truth supports the range.
- Do not add skills to the Technical Skills section that are not in grounded_keywords.

PAGE BUDGET — MANDATORY (A4, 0.5in margins, 10pt font = exactly 1 page):
- Professional Summary: 2–3 lines of prose ONLY. Do NOT add a bullet list under the summary paragraph. A prose summary is required; bullets under summary are prohibited.
- Most recent role (longest tenure): TARGET 6–7 bullets (hard cap 7). Fill the space — every strong, JD-relevant bullet backed by source-of-truth evidence should be included.
- Each older role: TARGET 4 bullets (hard cap 4).
- Professional Development section: TARGET 3 bullets (hard cap 3).
- Skills section: fit within 4 dense lines; no line break per skill category unless strictly necessary.
- Education: single header line only; no bullets.
- FILL THE PAGE: Aim to use at least 14 total bullets across all experience/dev sections combined. If you stop well short of the caps with white space remaining at the bottom, add more impactful, grounded bullets — do not leave blank space. A resume that exceeds 1 page is a critical defect; a resume with significant blank space at the bottom is wasted opportunity.
If the 1-page budget cannot be met with these limits, remove the weakest bullets first. Never exceed these per-section bullet caps.

$rgseed$,
1, true)
on conflict (user_id, stage, version) do nothing;

insert into resume_prompts (user_id, stage, body, version, is_active)
values (null, 'review',
$rgseed$Review the resume against the JD, targeting brief, and source of truth. The cover letter is not reviewed — it is regenerated alongside any resume revision.

Return strict JSON only. Do not include Markdown or prose outside JSON.

Company: {{COMPANY_NAME}}
Job title: {{JOB_TITLE}}
Revision number: {{REVISION_COUNT}}

Targeting brief (the strategy that was meant to guide generation):
{{TARGETING_BRIEF}}

Job description:
{{JD_TEXT}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

Must-fix items from previous review (populated only on revision passes):
{{PREVIOUS_MUST_FIX}}

Resume LaTeX:
{{RESUME_TEX}}

JSON schema:

{
  "resume": {
    "category_scores": {
      "jd_skills_keyword_match": 0,
      "role_domain_relevance": 0,
      "achievement_evidence_strength": 0,
      "credibility_source_truth_compliance": 0,
      "ats_latex_formatting_safety": 0,
      "recruiter_impression_seniority_alignment": 0,
      "targeting_brief_compliance": 0,
      "single_page_compliance": 0
    },
    "verdict": "pass|fail",
    "brutal_recruiter_opinion": "",
    "must_fix": [],
    "nice_to_have": [],
    "ats_risks": [],
    "missing_keywords": [],
    "credibility_risks": [],
    "fix_resolution": [
      {
        "must_fix_item": "exact text of the must-fix from previous review",
        "status": "fixed | partial | not_fixed | made_worse",
        "evidence": "what you see in the document that supports this status"
      }
    ]
  }
}

Rules:
- Category scores: 0–10, no arithmetic, be strict and realistic.
- targeting_brief_compliance: how well did the resume follow the targeting brief's tone, forbidden_claims, seniority_verbs, and keyword_strategy?
- single_page_compliance: score based on page-budget analysis of the LaTeX. Count total itemize bullets across ALL sections. Hard caps: (a) Professional Summary MUST be prose only — any \begin{itemize} under the summary is a violation; (b) most recent role must have ≤7 bullets; (c) each older role must have ≤4 bullets; (d) Professional Development must have ≤3 bullets; (e) total bullets across all sections must be ≤14. Underuse is also penalised: if total bullets across experience+dev sections are ≤9 (leaving significant blank space at the bottom of the page), deduct 2 points and add a must_fix item instructing the reviser to add grounded bullets to reach at least 12 total. Score: 10 = compliant AND uses ≥12 total bullets; 7–9 = minor over/under by 1–2 bullets; 4–6 = summary has bullet list, a role is over cap by 3+, or severe underuse (≤7 total bullets); 0–3 = major overflow (total >17) or multiple sections over cap. If single_page_compliance < 7, add a must_fix item listing exactly which sections have issues and the required caps.
- fix_resolution: populate only when previous_must_fix is non-empty. For each item, assess status honestly — "made_worse" if the revision created a new credibility problem while trying to address the issue.
- Be strict. Penalise: weak JD match, vague evidence, unsupported claims, ATS issues, formatting changes, brief non-compliance, page overflow.
- Do not do arithmetic. The application calculates weighted scores.
- MUST-FIX GENERATION IS MANDATORY: For every category you score below 9.0, you MUST include at least one specific, actionable must_fix item. These items are the primary signal used by the reviser — vague or missing must_fix items make revision impossible. Each must_fix item must: (a) name the exact category it addresses, (b) cite specific text, missing keywords, or weak bullets from the resume LaTeX, (c) state precisely what change is needed. Do not write generic feedback. Write instructions a developer could execute mechanically.
- ATS KEYWORD AUDIT — jd_skills_keyword_match scoring rules:
  * Extract every concrete technology, tool, methodology, and domain term from the JD (languages, frameworks, databases, platforms, practices).
  * For each one, check whether it appears literally in the resume text (exact string match, case-insensitive).
  * Count how many are present vs absent. Score: 10 = ≥90% present; 9 = 80–89%; 8 = 70–79%; 7 = 60–69%; below 7 = <60%.
  * Every absent keyword that the candidate HAS grounded evidence for in the source of truth is a must_fix item — specify exactly where in the resume to add it and how.
  * Absent keywords with NO source of truth evidence go into missing_keywords only (do not fabricate).
  * Do not award jd_skills_keyword_match above 8 if any keyword with grounded evidence is absent from the resume text.

$rgseed$,
1, true)
on conflict (user_id, stage, version) do nothing;

insert into resume_prompts (user_id, stage, body, version, is_active)
values (null, 'revision',
$rgseed$You are making surgical, measurable fixes to the resume. You are not rewriting from scratch. Every change must directly resolve a specific must-fix item from the review, or target a low-scoring category. The cover letter will be regenerated fresh from the revised resume — do not produce it here.

Return only the complete revised resume LaTeX. Do not wrap in Markdown.

---

Company: {{COMPANY_NAME}}
Job title: {{JOB_TITLE}}

Targeting brief (original strategy — do not contradict it):
{{TARGETING_BRIEF}}

Job description:
{{JD_TEXT}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

Current resume LaTeX:
{{RESUME_TEX}}

---

SCORE CONTEXT — understand where the resume is weak before making changes:

Current score: {{RESUME_SCORE}} / 10 (target to pass: {{RESUME_TARGET_SCORE}})

Category scores (the weighted rubric that determines the overall score):
{{RESUME_CATEGORY_SCORES}}

Any category below 9.0 is underperforming. Focus your changes on the lowest-scoring categories first. The must_fix items below are your primary instructions, but if must_fix is sparse, use the category scores above to identify what to improve independently.

---

MUST-FIX ITEMS — address every single one. These are not suggestions:

{{RESUME_MUST_FIX}}

---

Fix-resolution audit from previous pass (if present — do not repeat items marked "made_worse"):
{{FIX_RESOLUTION_MATRIX}}

---

ATS CHECKER RESULTS — mechanical keyword/structural gaps to address:

Top ATS actions (address these alongside the must-fix items above):
{{ATS_TOP_ACTIONS}}

Unmet hard requirements flagged by ATS (only fix if genuinely absent — do not fabricate):
{{ATS_UNMET_HARD_REQUIREMENTS}}

---

Rules:
- Address ALL must-fix items. If you cannot address one without fabrication, explain why in a LaTeX comment and leave the original.
- For any category scoring below 9.0 that has no must_fix item, make at least one targeted improvement based on what that category measures:
  * jd_skills_keyword_match: integrate missing JD keywords into bullets or skills section with grounded evidence
  * role_domain_relevance: sharpen framing of experience to better match the role domain
  * achievement_evidence_strength: replace weak/vague bullets with quantified, outcome-focused language from source of truth
  * credibility_source_truth_compliance: remove or qualify any claim not directly supported by source of truth
  * targeting_brief_compliance: align tone, seniority verbs, and keyword strategy with the targeting brief
  * single_page_compliance: enforce bullet caps per section
  * ats_latex_formatting_safety: fix any ATS-unsafe LaTeX constructs
  * recruiter_impression_seniority_alignment: adjust seniority signals to match role level
- Do not invent experience, companies, titles, dates, degrees, certifications, projects, or metrics.
- Do not add any claim in forbidden_claims from the targeting brief.
- For learning_signal_keywords in the brief: use adjacent evidence or framing — never fabricate direct expertise.
- Preserve LaTeX validity. Preserve base resume structure and formatting.
- Each change must be traceable to a specific must-fix item or a low-scoring category. Do not make cosmetic changes that do not move the score.
- PAGE BUDGET ENFORCEMENT: Hard caps per section: Professional Summary = prose only (no itemize); most recent role ≤7 bullets; each older role ≤4 bullets; Professional Development ≤3 bullets; total bullets across all sections ≤14. If a must-fix item references page overflow, remove the weakest bullets in over-limit sections. If the resume has significant blank space at the bottom (Education section well above the page bottom), ADD impactful grounded bullets to the most recent role or older roles up to their cap — blank space at the bottom is wasted opportunity. Do not add bullets if the page is already full.

$rgseed$,
1, true)
on conflict (user_id, stage, version) do nothing;

insert into resume_prompts (user_id, stage, body, version, is_active)
values (null, 'cover_letter',
$rgseed$Generate a tailored LaTeX cover letter for this job application.

Return only a complete LaTeX document. Do not wrap it in Markdown.

Company: {{COMPANY_NAME}}
Job title: {{JOB_TITLE}}

Targeting brief (follow the cover_letter_angle and tone exactly):
{{TARGETING_BRIEF}}

Job description:
{{JD_TEXT}}

Tailored resume LaTeX (final version after all revisions):
{{RESUME_TEX}}

Candidate source of truth:
{{SOURCE_OF_TRUTH}}

Revision history (what was strengthened in the resume — use this to inform the narrative):
{{FIX_RESOLUTION_SUMMARY}}

Instructions:
- Open with the cover_letter_angle from the targeting brief — not a generic statement.
- Adopt the tone from the brief exactly.
- Do not claim anything in forbidden_claims from the brief.
- For learning_signal_keywords: use adjacent evidence or express genuine openness to learn. Do not fabricate expertise.
- Do not invent experience, dates, projects, or motivations.
- Ground every claim in the tailored resume and source of truth.
- If the revision history is not "none", use items with status "fixed" or "partial" as signals of what was emphasised in the resume — mirror those themes in the cover letter without repeating bullet text verbatim.
- Keep it to roughly one page.
$rgseed$,
1, true)
on conflict (user_id, stage, version) do nothing;

insert into resume_prompts (user_id, stage, body, version, is_active)
values (null, 'ats',
$rgseed$You are an applicant tracking system analyst.

Read the job description and the ATS findings below and return a short, ordered
list of the highest-impact changes the candidate should make to the resume.

Return strict JSON only. No prose outside the JSON object.

Job description:
{{JD_TEXT}}

ATS findings:
{{ATS_FINDINGS}}

Return: {"actions": [{"action": "...", "why": "...", "impact": "high|medium|low"}]}
$rgseed$,
1, true)
on conflict (user_id, stage, version) do nothing;
