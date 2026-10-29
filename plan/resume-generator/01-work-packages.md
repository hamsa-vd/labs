# Work packages

Each package has a `CONTRACT.md` under `plan/resume-generator/contracts/`. That file is the only
thing both the test-authoring agent and the implementing agent see. Tickets in brackets are the
`resume_generator_v2_plan` issues the package discharges.

| WP | Name | Tickets | Blind-tested |
| --- | --- | --- | --- |
| 0 | Workspace scaffold | RG-001, RG-008 (partial) | no — no behaviour |
| 1 | Schema and repositories | RG-002†, RG-006† | yes |
| 2 | Deterministic core (ATS, scoring, template select, JD loader, renderers) | RG-020†, RG-021†, RG-022†, RG-033, RG-034 | yes |
| 3 | API skeleton, errors, logging, telemetry | RG-004, RG-007 | yes |
| 4 | LLM providers, BYOK crypto, budgets, fake client | RG-023, RG-031, RG-008 (fake) | yes |
| 5 | LangGraph port | RG-030 | yes |
| 6 | Run orchestration and SSE | RG-032 | yes |
| 7 | LaTeX compile service | RG-035 | yes |
| 8 | Domain routes: SoT, templates, prompts, keys, ATS, import, evidence gate, usage, admin | RG-020, RG-021, RG-022, RG-023, RG-036, RG-037, RG-050, RG-051 | yes |
| 9 | Ascend shell extension and token lint | RG-010†, RG-011†, RG-012†, RG-013† | yes |
| 10 | Screens | RG-040…047 | yes |
| 11 | Landing and access copy | RG-048† | yes |
| 12 | v1 data migration | RG-053 | yes |
| 13 | CI, images, deployment runbook | RG-009, RG-054† | partial |

† adapted by ADR-100.

## Dependency order

```
WP0 ─┬─ WP1 ─┬─ WP3 ─ WP4 ─ WP5 ─ WP6 ─┬─ WP8 ─ WP10
     │       │                          │
     └─ WP2 ─┘                   WP7 ───┘
     └─ WP9 ─────────────────────────────── WP10 ─ WP11
                                                  WP12, WP13
```

WP2 and WP9 have no dependency on each other and start immediately after WP0.

## The blind protocol, precisely

For each package:

1. **Contract.** Written by the orchestrator from the ticket, the v1 source, and ADR-100. It
   fixes module paths, function and class signatures, field names, error codes, and observable
   behaviour — everything a test could legitimately assert. It never contains an implementation.
2. **Test agent.** Reads the contract and the named v1 reference files. Writes only under the
   package's test paths. Instructed not to open the implementation paths; they are usually empty
   when it starts anyway.
3. **Implementation agent.** Reads the contract and the same v1 reference files. Writes only under
   the package's source paths. Instructed not to open the test paths.
4. **Reconciliation.** The orchestrator runs the suite. Every failure is triaged into one of:
   the implementation is wrong; the test misread the contract; the contract was ambiguous. Only
   the third kind results in a contract edit, and the edit is recorded in the package's row below.

A test is never weakened to make it pass. A contract ambiguity is a finding worth keeping — it is
the part of the specification that a careful reader could take two ways.

## Reconciliation log

| WP | Contract edits after reconciliation | Notes |
| --- | --- | --- |
| 1 | AC4 "body starts with `\documentclass`" relaxed to "contains"; "eleven new tables" corrected to twelve | Three `multi_page` templates begin with blank lines, so the literal criterion conflicted with porting the bytes verbatim. Implementation strips leading whitespace only. `resume_run_events` is the twelfth table and reaches a user through `resume_runs`, not a `user_id`. Both found independently by the test agent; the implementer independently chose `nulls not distinct` for the prompt indexes, which fixes a real bug the contract's literal DDL would have shipped. |
| 2 | §6 comment stripping made conditional on the input being LaTeX | The contract required unconditional stripping *and* that plain text pass through. Both agents flagged the conflict. Settled toward the import flow: deleting the tail of "cut latency by 45% across 12 services" from a pasted resume is silent data loss in the exact field the ATS structural score measures. Two tests encoding the unconditional reading were updated to the amended rule and a prose-preservation test added. |
| 2 | §8 `ats_error` no longer carries `str(exc)` | The blind test suite caught a real leak: `ats_error` is persisted on the run and rendered in the result view, so a scorer exception quoting the resume body would publish it. AGENTS.md's secrets rule outranks the contract wording. Now returns the exception type and a fixed sentence; the detail stays in the log. |
