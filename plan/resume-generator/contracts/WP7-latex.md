# WP7 — LaTeX compilation

Discharges RG-035, plus the macro denylist half of RG-021.

This is the one place in the system where a shortcut becomes a security incident. The `.tex` being
compiled is user input, and `\write18`, `\input{/etc/passwd}` and `\openout` are real escapes. v1
shelled out to a local `latexmk`; v2 must not.

Two roots:
- `apps/resume-latex/` — the containerised compiler. Already has `Dockerfile`, `warmup.tex` and
  `healthcheck`; the `tectonic` build stage is verified working and the TeXLive package cache is
  pre-warmed into the image, so the running container needs no network at all.
- `apps/resume-pipeline/` — the validator and the client.

Defence is in three layers and all three are required:
1. `validate.py`'s denylist, applied before a request is ever sent (and on every template write);
2. `tectonic -X compile --untrusted`, which disables shell-escape and external commands;
3. the container constraints already in `docker-compose.dev.yml` — read-only root filesystem,
   tmpfs scratch, all capabilities dropped, non-root user, 512 MB, 1 CPU.

---

## 1. `resume_pipeline/latex/validate.py`

```python
@dataclass(frozen=True)
class Problem:
    line: int          # 1-indexed; 0 when the problem is about the document as a whole
    message: str       # arey voice: what is wrong, then what to do

MAX_TEX_BYTES = 200 * 1024

def validate_tex(tex: str) -> list[Problem]: ...
def assert_valid_tex(tex: str) -> None: ...   # raises ValidationFailed with details.problems
```

`validate_tex` returns **every** problem it finds, never just the first — a user fixing one
rejection at a time is a bad experience and RG-021 calls it out explicitly.

Structural requirements (each a problem when absent):
- contains `\documentclass`
- contains `\begin{document}`
- contains `\end{document}`

Denied constructs (each occurrence a problem, with its line number):
- `\write18` and `\immediate\write18`
- `\input` or `\include` with an absolute path (`{/…}`) or any parent traversal (`..`)
- `\openout`, `\openin`, `\read`, `\write` to a stream
- `\catcode` reassignment of `\`, `{`, `}` — the standard way to smuggle past a naive scanner
- `\usepackage{shellesc}`, `\ShellEscape`, `\directlua`, `\immediate\write` to an open stream
- `\special{...}` containing `dvipdfmx:` or a shell invocation

Rules that make the scanner honest rather than decorative:
- A construct inside a comment (an unescaped `%` to end of line) is **not** a problem. A `\%` is a
  literal percent and does not start a comment.
- Matching ignores whitespace between the control sequence and its brace, so `\write18`,
  `\write 18` and `\write\n18` all trip.
- Over `MAX_TEX_BYTES` is a problem at line 0.
- The message names the line and what to do, e.g. `"Line 40 uses \\write18. Remove it and save
  again."` Sentence case, no exclamation mark.

## 2. `apps/resume-latex/parse_log.py`

```python
@dataclass(frozen=True)
class TexError:
    line: int | None
    message: str      # one sentence
    raw: str          # the log excerpt, for details only — never shown to the user

def parse_log(log: str) -> TexError | None: ...
def page_count(log: str) -> int | None: ...
```

A TeX log is hundreds of lines and the useful part is small. `parse_log` returns the **first**
meaningful error: the first line beginning `! `, with the line number from the nearest following
`l.NNN` marker, and a one-sentence summary. It returns `None` when the log holds no error.

It must recognise and summarise at least: `! Undefined control sequence`, `! LaTeX Error: File
'x.sty' not found`, `! Missing $ inserted`, `! Emergency stop`, `! TeX capacity exceeded`, and
`! Package … Error:`. An unrecognised `! ` line is returned with its own text as the summary
rather than a generic message.

`page_count` reads the `Writing 'x.pdf' (N pages)` / `Output written on … (N pages` form and
returns `None` when absent.

## 3. `apps/resume-latex/app.py`

A FastAPI app with exactly two routes. It holds no state, no database, and no knowledge of users.

```
GET  /health          → {"status": "ok", "tectonic": "<version>"}
POST /compile         {"tex": str, "passes": int = 2} → application/pdf
                                                      → 422 {"error": {...}} on a TeX error
```

- Writes the source to a fresh directory under `/tmp` (tmpfs), compiles with
  `tectonic -X compile --untrusted --keep-logs --outdir <dir>`, and reads back the PDF.
- Two passes by default: cross-references and page counts need them.
- 20 second wall-clock timeout on the subprocess. On timeout, kill the process group and return
  422 with code `compile_timeout`. It must never wait for input — `--untrusted` plus a closed
  stdin, and no interactive prompt can hang it.
- Input over 200 KB returns 413 before doing anything.
- Success returns the PDF bytes with `X-Page-Count` and `X-Compile-Ms` headers.
- Failure returns the envelope `{"error":{"code":"compile_failed","message":…,"details":{"line":N,
  "log":"…"}}}`. The `message` is the one-sentence summary; the full log goes in `details` only.
- The scratch directory is deleted whether the compile succeeded or failed.

## 4. `resume_pipeline/services/latex.py`

```python
@dataclass(frozen=True)
class CompileResult:
    ok: bool
    pdf: bytes | None
    pages: int | None
    error: str | None          # one sentence, user-facing
    error_line: int | None
    log: str | None            # operator-facing
    cached: bool

async def compile_tex(tex: str, *, client=None) -> CompileResult: ...
def cache_key(tex: str) -> str: ...     # sha256 of the source
```

- Runs `assert_valid_tex` first. A denylisted macro never reaches Tectonic — that is the point of
  having the check on this side too.
- Calls the service at `settings.latex_service_url`. A transport failure or a 5xx becomes
  `UpstreamFailed` with a retryable message, not a stack trace.
- Caches by `sha256(tex)`: an identical source returns the stored PDF without invoking Tectonic.
  The cache is the `resume_documents` table keyed on `content_hash` plus the blob store, so it
  survives a restart. A cache hit sets `cached=True`.
- `client` is injectable so tests drive it through an httpx `MockTransport` with no container
  running.

## 5. `compile_pdfs` behaviour contract (consumed by WP5)

This function is not yours to write, but the behaviour it depends on is yours to guarantee, and it
is v1 behaviour that must not be lost: **a PDF failure never loses the `.tex`.** A compile error
populates `compile_errors` and the run still ends in a complete state, distinguished as
`complete_with_compile_errors`. `compile_tex` therefore returns a `CompileResult` with `ok=False`
rather than raising, for every failure that is the document's fault. It raises only when the
service itself is unreachable.

## Acceptance criteria

1. A known-good seeded template compiles to a PDF with a plausible page count.
2. A `.tex` with a deliberate error returns `ok=False` with the correct line number and a
   one-sentence message; the full log is present but not in the message.
3. Every denylisted construct is rejected by `validate_tex`, one test per construct, each
   reporting the right line.
4. The same construct inside a comment is **not** rejected; `\%` does not start a comment.
5. `validate_tex` on a file with three distinct problems returns all three.
6. A `\write18` payload never reaches the service — assert with a transport stub that counts calls.
7. An infinite `\loop` is killed by the timeout and returns a timeout error rather than hanging.
   Drive this against the real container; skip cleanly when it is not running.
8. The hash cache returns a second identical request without invoking Tectonic — assert with a
   call counter.
9. `parse_log` extracts the right line and summary for each of the six named error classes.
10. The container image builds, and its root filesystem is read-only and its user non-root —
    assert from `docker inspect` / a probe, skipping cleanly when Docker is unavailable.

## Test paths (test agent writes only here)

```
tests/latex/test_validate.py
tests/latex/test_parse_log.py
tests/latex/test_compile_client.py
tests/latex/test_container_integration.py     # skips unless the container is up
```

`tests/conftest.py` already exists (WP2) and holds the socket guard. To import `parse_log` from
`apps/resume-latex`, add that directory to `sys.path` from a **new** `tests/latex/conftest.py`
rather than editing the shared one. Container tests read `RESUME_LATEX_URL` and skip when absent.

## Source paths (implementing agent writes only here)

```
resume_pipeline/latex/__init__.py
resume_pipeline/latex/validate.py
resume_pipeline/services/latex.py
apps/resume-latex/app.py
apps/resume-latex/parse_log.py
```

`apps/resume-latex/Dockerfile`, `warmup.tex` and `healthcheck` already exist and are verified —
do not rewrite them. You may add a package to `warmup.tex` if a seeded template needs one that is
missing, and you must say so if you do.
