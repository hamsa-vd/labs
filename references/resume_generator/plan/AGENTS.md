# AGENTS.md — rules for models implementing this repo

Copy this file to the root of `resume-generator`. Every implementing model reads it before
touching code. It exists because the planning and the implementation are done by different
models: the plan is complete, so improvisation is a regression, not an improvement.

## Before you write anything

1. Read the ticket in `plan/tickets/` in full — both halves. The product requirement tells you
   what is true when you are done; the technical plan tells you how.
2. Read the files the ticket's **Reuse from v1** section names. v1 is working software. Porting
   it is the job; rewriting it is not.
3. Read `plan/00-architecture.md` and `plan/02-design-system-strategy.md` once, ever.

## Hard rules

**Scope.** Create only the files the ticket lists. If you believe another file is needed, comment
on the issue and stop. Do not add a "small helper", a "quick refactor", or a file the plan omits.

**Styling.** Never write a hex colour, an rgb/hsl literal, a px radius, a box-shadow literal, a
transition duration, or a font-family string. Every visual value is `var(--token)`. The lint rule
`no-raw-design-values` will fail your build; do not disable it.

**Components.** Compose from `@repo/ui`. Do not restyle a primitive at the call site to make it
look different. If a screen needs something `@repo/ui` does not have, and the ticket does not
list it, stop and comment.

**Copy.** Sentence case. Second person. No emoji. No exclamation marks. Errors say what happened
then what to do. Machine-produced values (scores, durations, timestamps, IDs) render in
`--font-mono`. When in doubt, write it the way a changelog entry would read.

**Domain logic.** Do not change a rubric weight, a budget constant, a threshold, a graph node, or
a routing condition. Those numbers came from a working system. If one looks wrong, comment.

**Contracts.** The API's error envelope, list shape, and generated TypeScript client are fixed by
RG-004. Do not hand-write a fetch call to the API. Do not invent a new error shape.

**Tests.** Every ticket names its tests. A ticket without its passing tests is not done. Do not
weaken an assertion to make a test pass. Do not mark a test `skip`.

**Secrets.** Never log, serialise, or include in an error message: an API key, a resume body, a
job description, or any `ciphertext` value.

## When you are stuck

Comment on the issue with: what you tried, what the ticket says, and the specific decision you
cannot make. Then stop. A stalled ticket costs an hour; a wrong guess propagated through four
dependent tickets costs a week.

## Definition of done, every time

- [ ] Every acceptance criterion in the ticket is demonstrably true
- [ ] Every test the ticket names exists and passes
- [ ] `pnpm lint && pnpm typecheck && pnpm test` green across the workspace
- [ ] No file created that the ticket does not list
- [ ] No token rule, contract, or domain constant changed
