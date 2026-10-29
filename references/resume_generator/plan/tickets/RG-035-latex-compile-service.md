# RG-035 — LaTeX compilation service

**Epic:** D — Pipeline · **Depends on:** RG-006 · **Estimate:** L · **Labels:** pipeline, infra, security

## Product requirement

**Problem.** v1 shells out to a local LaTeX install. Most machines do not have one, and in a
multi-user product the `.tex` being compiled is untrusted user input.

**User story.** As a user I edit the LaTeX of my resume, press compile, and get a PDF in a few
seconds — or a readable error pointing at the line that broke.

**Acceptance criteria**
- Compilation works with no LaTeX installed on the API host or the user's machine.
- A malicious `.tex` cannot read the filesystem, reach the network, or run a shell.
- Compilation fails fast — no run hangs on a LaTeX error prompt.
- A failure shows the first meaningful error line, not 400 lines of log.

## Technical plan

Decision D2: a Tectonic container as a separate service.

### Files
```
services/latex/Dockerfile              tectonic on a slim base
services/latex/app.py                  POST /compile → application/pdf | 422 + parsed error
services/latex/parse_log.py            TeX log → first meaningful error {line, message}
apps/api/resume_api/services/latex.py  client
apps/api/resume_api/routers/compile.py
```

### Routes
```
POST /v1/documents/{id}/compile    → { document_id (pdf), pages, warnings[] }
POST /v1/compile/preview           { tex } → same, not persisted (LaTeX editor preview)
```

### Hardening (all required)
- `tectonic -X compile --untrusted`, which disables shell-escape and external commands.
- Container runs as a non-root user, read-only root filesystem, scratch on a tmpfs.
- No network egress from the container except the Tectonic package cache, which is **pre-warmed
  into the image** at build time so runtime egress can be blocked entirely.
- 20 s wall-clock timeout, 512 MB memory, 1 CPU. `-halt-on-error` so it never waits for input.
- Input capped at 200 KB, and re-run through the RG-021 macro denylist before compiling.

### Steps
1. Two-pass compile (references and page counts need it); parse the log after the final pass.
2. `parse_log.py` returns the first `! ` line with its `l.NNN` line number and a one-sentence
   summary. Full log goes to the response `details`, never into the user-facing message.
3. On success, store the PDF via `BlobStore` and insert a `documents` row of kind `*_pdf`.
4. `compile_pdfs` in the graph calls this service and preserves v1's behaviour exactly: failures
   populate `compile_errors` and the run still ends `complete_with_compile_errors` — a PDF failure
   never loses the `.tex`.
5. Cache by `sha256(tex)`: identical source returns the stored PDF without recompiling.

### Reuse from v1
`resume_agent/latex_compile.py` for the interface shape (`compile_tex_file(src, out, requested)`
→ `success`/`error`) and `graph.compile_pdfs` for the error-tolerance contract. The subprocess
implementation itself is replaced.

### Tests
- A known-good template compiles to a PDF with the expected page count.
- A `.tex` with a deliberate error returns 422 with the correct line number.
- A `\write18{...}` payload is rejected before reaching Tectonic.
- An infinite `\loop` is killed by the timeout and returns a timeout error, not a hang.
- The hash cache returns the second request without invoking Tectonic (assert via a call counter).

### Definition of done
All five tests green; the container image builds in CI.

### Out of scope
The LaTeX editor UI (RG-043).
