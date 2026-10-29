# Resume Generator v2 — implementation plan

This folder is the **source material for Linear tickets**. Every file in `tickets/` is one
Linear issue: paste the whole file body into the issue description, use the H1 as the title.

## Why the tickets look like this

The plan is split so that a **premium model plans** and a **small model (Sonnet / GPT-5.4-mini)
implements**. Each ticket therefore has two halves:

1. **Product requirement** — the user-facing outcome, written as a PRD slice. No code.
2. **Technical plan** — exact files, contracts, steps, and a definition of done. No ambiguity.

A ticket is correctly sized when a small model can open it, read the two or three linked
files, and finish it in one session without asking a design question.

## Rules for the implementing model (put this in the repo's AGENTS.md too)

- Do not invent scope. If the ticket does not list a file, do not create it.
- Do not restyle. All visual values come from design tokens (see `02-design-system-strategy.md`).
- Every ticket ships with its tests. A ticket with no passing test is not done.
- If a ticket's assumption is wrong, stop and comment on the issue — do not improvise.
- Reuse the v1 code named in the **Reuse from v1** section verbatim where possible. v1 is
  working software; v2 is a re-platform, not a rewrite of the domain logic.

## Reading order

| File | What it settles |
| --- | --- |
| `00-architecture.md` | Stack, repo layout, service boundaries, data flow |
| `01-v1-reuse-map.md` | What in v1 is kept, ported, or dropped |
| `02-design-system-strategy.md` | How the external arey design-system repo is consumed |
| `03-open-decisions.md` | Things still unresolved, with a recommendation each |
| `tickets/` | The issues themselves |

## Epics

| Epic | Range | Theme |
| --- | --- | --- |
| A — Foundations | RG-001…009 | Repo, Supabase, auth, API/web skeletons, storage, local env, CI |
| B — Design system | RG-010…013 | Token pipeline, UI primitives, app shell |
| C — User data | RG-020…024 | Source of truth, templates, prompts, BYOK keys |
| D — Pipeline | RG-030…037 | Generation graph, ATS, scoring, LaTeX, evidence gate |
| E — Product screens | RG-040…048 | Pipeline, generate, result, import, settings, landing |
| F — Operations | RG-050…054 | Cost accounting, admin/invites, v1 migration, cloud |

## Dependency spine

```
RG-001 ─┬─ RG-002 ─ RG-003 ─┬─ RG-005 ─ RG-011 ─ RG-012 ─ RG-013 ─ RG-04x
        ├─ RG-004 ──────────┘
        ├─ RG-006 (storage)
        └─ RG-010 (tokens, parallel from day 1)

RG-004 ─ RG-030 ─ RG-031 ─ RG-032 ─┬─ RG-033 (ATS)
                                   ├─ RG-034 (scoring)
                                   └─ RG-035 (LaTeX compile)
```
