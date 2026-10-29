# RG-006 — Document storage abstraction

**Epic:** A — Foundations · **Depends on:** RG-002 · **Estimate:** S · **Labels:** foundation, data

## Product requirement

**Problem.** v1 writes `.tex`, `.pdf`, `JD.txt`, and `review.json` to a local folder tree. That is
not shareable, not backed up, and not multi-user.

**Outcome.** Documents are stored per user, downloadable by the owner and nobody else, with a
storage backend the product is not married to.

**Acceptance criteria**
- A user can download their own resume PDF; the same URL fails for anyone else.
- Download links expire.
- Swapping the storage provider touches exactly one class.

## Technical plan

Decision D1 in `plan/03-open-decisions.md`: Supabase Storage, private bucket `documents`.

### Files
```
apps/api/resume_api/storage/base.py        BlobStore protocol
apps/api/resume_api/storage/supabase.py    SupabaseBlobStore
apps/api/resume_api/storage/paths.py       canonical path builder
apps/api/resume_api/routers/documents.py   GET /v1/documents/{id}/url
supabase/migrations/0012_storage_bucket.sql
```

### Contracts
```python
class BlobStore(Protocol):
    async def put(self, path: str, data: bytes, content_type: str) -> str: ...
    async def get(self, path: str) -> bytes: ...
    async def signed_url(self, path: str, ttl_seconds: int = 60) -> str: ...
    async def delete(self, path: str) -> None: ...
```
Path shape: `{user_id}/{application_id}/{run_id}/{kind}.{ext}`. Built only by `paths.py` —
no string concatenation at call sites.

### Steps
1. Create the private bucket in a migration with a storage policy scoped to
   `(storage.foldername(name))[1] = auth.uid()::text`.
2. Every `put` also inserts a `documents` row (path, byte size, sha256). The row is the index;
   the bucket is the bytes. Never list the bucket to find a file.
3. `GET /v1/documents/{id}/url` checks ownership via the `documents` row, then returns a 60 s
   signed URL. PDF bytes never pass through FastAPI.

### Reuse from v1
The file *names* v1 chose (`hamsa_resume.tex`, `cover_letter.tex`, `JD.txt`, `review.json`) map to
the `documents.kind` enum. `review.json` becomes the `runs` row, not a blob.

### Tests
- Round-trip put/get/delete against a local Supabase.
- Ownership: user B requesting user A's document id gets 404 (not 403 — do not leak existence).
- A signed URL is unusable after its TTL.

### Definition of done
All three tests green; no call site imports `supabase.py` directly.

### Out of scope
PDF generation (RG-035).
