# Rules for agents implementing the resume generator

Read this once, fully, before touching a file. It exists because the tests and the implementation
for each work package are written by different agents that cannot see each other's output. The
contract is the only shared artefact, so improvisation on either side shows up as a false failure.

## The blind protocol

- **If you are the test-authoring agent:** write only under the test paths your task names. Do not
  read, create, or edit anything under the source paths. Do not guess at an implementation and
  test the guess — test the contract's observable behaviour.
- **If you are the implementing agent:** write only under the source paths your task names. Do not
  read, create, or edit anything under the test paths. Do not write your own tests there.
  Verify your work with scratch scripts in the scratchpad directory instead.
- **Test agents: the implementation has side channels, and they are out of bounds too.** Do not
  introspect a running database's schema, call a running service, or read a generated artefact to
  decide what to assert. Derive every assertion from the contract and the named v1 sources. If the
  implementation has already landed by the time you run, your suite is still only meaningful if it
  encodes what the contract says — a test that mirrors whatever it found is worth nothing.
- **Both:** the contract is authoritative. Where it is silent, the named v1 source file is
  authoritative. Where both are silent, stop and report the ambiguity in your final message
  rather than choosing — that ambiguity is a finding worth having.
- **Both: do not run `make reset` or otherwise rebuild the shared dev database.** Another agent is
  very likely using it at the same time. If you need a clean database, create your own with a
  distinct name and say so.

## Hard rules

**Scope.** Create only the files your contract lists. If you believe another file is needed, say
so in your final message and stop. No "small helper" outside the listed paths.

**Port, do not rewrite.** Where the contract says a file comes from v1, move it across with the
changes the contract names and nothing else. v1 is working software. Do not rename a node, change
a rubric weight, adjust a threshold, reorder a routing condition, or "simplify" a branch. Those
numbers came from a system that produces good resumes.

**Styling.** No hex colour, `rgb()`/`hsl()` literal, px radius, box-shadow literal, transition
duration, or font-family string in app code. Every visual value is `var(--token)` from the arey
system. Compose from `@labs/design/arey`; do not restyle a primitive at the call site.

**Copy.** Sentence case. Second person. No emoji. No exclamation marks. An error says what
happened, then what to do. Machine-produced values — scores, durations, timestamps, IDs, counts —
render in `--font-mono`.

**Secrets.** Never log, serialise, return, or put in an exception message: an API key, a resume
body, a job description, or any ciphertext. The redaction processor is a second line of defence,
not a licence to be careless.

**Tests.** Never weaken an assertion to make a test pass. Never mark a test skipped or xfail to
get a green run. If a test and the code disagree, report it; do not resolve it by deleting the
disagreement.

**Network.** Tests make no network calls, ever. LLM access in tests goes through the fake client.

## Definition of done

- Every acceptance criterion in the contract is demonstrably true.
- `make check` is green in `apps/resume-pipeline`, or `pnpm check` in `apps/ascend`.
- No file created that the contract does not list.
- Your final message states: what you built, anything in the contract you found ambiguous, and
  anything you could not do.
