# Ticket index — 39 issues

Paste order = build order. Title = the ticket file's H1. Description = the rest of the file.

| # | Title | Epic | Est | Depends on |
| --- | --- | --- | --- | --- |
| RG-001 | Scaffold the resume-generator monorepo | A | M | — |
| RG-002 | Supabase schema, migrations, and RLS | A | L | 001 |
| RG-003 | Google sign-in with invite-only access | A | M | 002 |
| RG-004 | FastAPI application skeleton and API contract | A | M | 001, 002 |
| RG-005 | Next.js app skeleton and routing | A | M | 001, 003 |
| RG-006 | Document storage abstraction | A | S | 002 |
| RG-007 | Structured logging, errors, and run telemetry | A | S | 004 |
| RG-008 | One-command local development environment | A | M | 001, 002 |
| RG-009 | Continuous integration and quality gates | A | M | 001, 004, 005, 008 |
| RG-010 | Design token pipeline from the external repo | B | M | 001 |
| RG-011 | Rebuild arey primitives as typed React components | B | L | 010 |
| RG-012 | Theming, dark mode, and responsive foundations | B | S | 010, 005 |
| RG-013 | Authenticated app shell | B | M | 011, 012 |
| RG-020 | Source of truth: structured model and API | C | L | 002, 004 |
| RG-021 | LaTeX template library | C | M | 002, 006 |
| RG-022 | User-editable prompts for the six run stages | C | M | 002, 004 |
| RG-023 | BYOK provider keys | C | M | 002, 007 |
| RG-030 | Port the LangGraph pipeline to the API | D | L | 004, 020, 021, 022 |
| RG-031 | Provider abstraction and per-user model budgets | D | M | 023, 030 |
| RG-032 | Run orchestration and live progress | D | L | 030, 031, 006 |
| RG-033 | ATS checker as a service module | D | M | 030 |
| RG-034 | Review rubric and scoring service | D | S | 030 |
| RG-035 | LaTeX compilation service | D | L | 006 |
| RG-036 | Evidence-gated ATS keyword fixes | D | L | 020, 033 |
| RG-037 | Import an existing resume for scoring | D | M | 033, 006 |
| RG-040 | Pipeline screen (application tracker) | E | L | 013, 032, 037 |
| RG-041 | New application: input and launch | E | M | 021, 032 |
| RG-042 | Live run view | E | M | 032 |
| RG-043 | Result view: scores, ATS panel, LaTeX editor | E | XL | 034, 035, 036 |
| RG-044 | Import flow UI | E | M | 037, 040 |
| RG-045 | Source of truth and prompts screen | E | L | 020, 022 |
| RG-046 | Templates screen | E | M | 021, 035 |
| RG-047 | Settings screen | E | M | 023, 031, 012 |
| RG-048 | Landing page and access screens | E | M | 003, 011 |
| RG-050 | Run cost accounting | F | S | 007, 031 |
| RG-051 | Admin portal: invites and users | F | M | 003 |
| RG-052 | Move run execution to a queue (conditional) | F | M | 032 |
| RG-053 | Migrate v1 data into v2 | F | M | 020, 021, 037 |
| RG-054 | Promote to cloud environments | F | L | 009, 008 |

## Suggested milestones

**M1 — Walking skeleton.** 001–009, 010–013. Signed-in, themed, empty app with a green pipeline.
**M2 — Domain.** 020–023, 030, 031, 033, 034. The pipeline runs end to end from the API.
**M3 — Product.** 032, 035, 040–043, 045–047. The six screens work.
**M4 — Completeness.** 036, 037, 044, 048, 050, 051, 053, 054.
**M5 — Conditional.** 052, only when its trigger fires.

## Tickets that carry the most risk

- **RG-030** — the port. If v1's routing behaviour is not preserved exactly, quality regresses
  invisibly. Its ported test suite is the only thing that catches it.
- **RG-036** — the evidence gate. No v1 precedent, and the feature is the product's position.
- **RG-043** — XL. Split along its three panels if it stalls.
- **RG-035** — untrusted LaTeX. The one place where a shortcut becomes a security incident.
- **RG-054** — cloud promotion. A leaked service-role key or an internet-reachable LaTeX
  container is the most expensive mistake available in this plan.
