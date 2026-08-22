# PRD — RepoChat Backend Hardening & Frontend Build

**Product**: GitHub-repository RAG chat assistant (user logs in, connects a GitHub repo, backend clones/parses/chunks/embeds it, user asks questions answered via retrieval + Groq LLM).

**Status quo**: Functionally works for a single user, single request at a time. Will not survive concurrent usage. No logging/observability. No error boundaries. Frontend in the repo is for an unrelated old project ("Webhook Inspector") and must be rebuilt from scratch against the real API.

This doc is organized as: (1) architecture problem, (2) critical bugs, (3) concurrency risk, (4) exception handling & logging plan, (5) security, (6) file-by-file change list, (7) new feature ideas, (8) frontend plan, (9) suggested phasing.

---

## 1. Root architecture problem

`router.py` mixes three concerns in every handler: HTTP I/O, business logic, and DB access. There is no service/repository layer for repositories or chat, so:

- Logic can't be unit tested without spinning up FastAPI.
- The same duplicate-checking / validation would have to be copy-pasted anywhere else it's needed.
- Handlers are doing things like string-parsing GitHub URLs and looping DB inserts — that's why they "feel too big."

**Target layering:**

```
router.py            -> thin: parse request, call service, return response
services/repository_service.py   -> business logic: create, validate, orchestrate processing
services/chat_service.py         -> query + chat history logic
services/processor.py            -> chunking + embedding pipeline (fixed for async safety)
models.py / db.py                -> persistence only
```

No route handler should contain a `for` loop over DB inserts, string parsing of external identifiers, or try/except around a whole workflow. That all belongs in a service function the route calls once.

---

## 2. Critical / correctness bugs (fix regardless of anything else)

| # | File:Line | Bug | Impact |
|---|-----------|-----|--------|
| 1 | `github_parser/tarfile.py:98-103` | `file_obj` is set inside `if member.size < 500*1024:` but read/checked outside it. If a large file appears before any small file, `file_obj` is unset → `UnboundLocalError` crashes the entire import. If a large file follows a small one, the **previous file's content gets silently reused** for the skipped file. | Repo import randomly crashes or saves wrong file content, depending on file order. |
| 2 | `router.py:52` (`background_tasks.add_task(process_repository, ...)`) + `services/processor.py:16` (`db = next(get_db())`) | Background task session is never closed — `finally` in `get_db()` only fires on generator close, not after one `next()`. | Every repository import leaks one DB connection. Under concurrent users, pool exhausts and the whole app starts failing/hanging. |
| 3 | `models.py` (`Repositories.status`) | Set to `"processing"` at creation, never updated anywhere in `services/processor.py`. | Frontend has no reliable way to show "ready" vs "failed" — repos appear stuck forever, including on real failures. |
| 4 | `router.py:32` (`owner_repo = github_url.rstrip("/").split("/")[-2:]`) | No validation of `github_url` shape. A URL without at least 2 path segments → `IndexError`, unhandled → raw 500. | Bad user input crashes the request instead of a clean 400. |
| 5 | `services/processor.py:27-48` (`process_chunks`) | Single `db.commit()` at the very end of the loop; no try/except around embedding generation. | If embedding fails on chunk 500 of 800, **all** chunks for that repo are lost (nothing partial is saved), and the repo is left in `"processing"` forever (see #3). |
| 6 | `github_parser/tarfile.py:6` | `from passlib import ext` — unused, unrelated import, clearly leftover/copy-paste. | Dead code, confusing to read, minor but a "smell" worth cleaning. |
| 7 | `github_parser/tarfile.py` filename | File is named `tarfile.py` inside `github_parser/`, shadowing Python's stdlib `tarfile` module that the file itself imports. Currently works because of absolute-import semantics, but is a landmine for any future refactor/tooling. | Rename to `github_archive.py` or `repo_fetcher.py`. |

---

## 3. Concurrency — why it breaks under multiple users

FastAPI's async event loop is single-threaded for CPU work. Every blocking call inside an `async def` stalls **all** concurrent requests, not just the one that made the call.

| File | Blocking call | Fix |
|------|----------------|-----|
| `services/embeddings.py:9` | `model.encode(text)` — CPU-bound, synchronous, awaited directly | Wrap in `await asyncio.to_thread(model.encode, text)`, or run a dedicated embedding worker/queue |
| `chunker.py:31-33` | `get_parser(language)` + `parser.parse(...)` — synchronous tree-sitter calls inside `async def` | Same: `asyncio.to_thread(...)` |
| `github_parser/tarfile.py:45-104` | `tarfile.open(...)` + iterating/decoding members — synchronous, plus `response.content` loads the whole archive into memory | `asyncio.to_thread` for the tar extraction; stream/size-cap the download |
| `services/processor.py:33-47` | Sequential `await generate_embedding(...)` per chunk, one at a time | Batch embeddings (SentenceTransformer supports batch `.encode(list)`), or bound concurrency with `asyncio.Semaphore` + `asyncio.gather` |
| `services/llm.py:72` | New `AsyncGroq(api_key=...)` client created on every single query | Module-level singleton client, reused across requests (connection reuse, less overhead per request) |

**Also:**
- `services/embeddings.py:4` loads the SentenceTransformer model at import time. If you ever run multiple uvicorn workers, each process loads its own full copy into memory — budget for that or move embedding to a single shared service.
- `db.py:7` defaults `DATABASE_URL` to `sqlite:///webhook.db`, but `models.py` uses `pgvector.sqlalchemy.Vector`, which **does not work on SQLite at all**. Your actual `.env` correctly points at Postgres/Neon, but the fallback default is broken — anyone running this without the env var set gets a confusing crash, not a clear error.
- No connection pool sizing (`pool_size`, `max_overflow`) configured in `db.py` — under concurrent load with default SQLAlchemy pool settings, this can bottleneck quickly once #2 above (leaked sessions) is also happening.

---

## 4. Exception handling & logging plan

Currently: zero use of `logging`, two `print()` statements, no global exception handler, no request IDs, no error tracking despite `sentry-sdk` already sitting unused in `requirements.txt`.

**Plan:**
1. Add `backend/logging_config.py` — configures root logger (structured, includes timestamp/level/module), attach to Uvicorn's loggers so all output is consistent.
2. `main.py`: add
   - `@app.exception_handler(Exception)` — catch-all that logs the full traceback server-side and returns a generic `{"detail": "Internal server error"}` (never leak tracebacks to the client).
   - `@app.exception_handler(RequestValidationError)` — clean 422 body for bad input.
   - Optionally initialize `sentry_sdk.init(dsn=...)` since the dependency is already installed — gives you error aggregation for free.
3. Every `except Exception as e:` block across `router.py`, `services/*.py`, `github_parser/tarfile.py` should `logger.exception(...)` before re-raising as an `HTTPException`, instead of silently swallowing or just wrapping the message.
4. Background task (`process_repository`) must catch its own exceptions (it runs outside the request/response cycle — FastAPI does not surface its errors to any client), log them, and **update `repository.status = "failed"`** so the failure is visible in the product, not just the logs.

---

## 5. Security

| Issue | File | Fix |
|-------|------|-----|
| JWT secret silently defaults to `"dev-secret-change-me"` | `auth.py:13` | Fail fast at startup if `JWT_SECRET_KEY` is not set (raise in `db.py`/`main.py` startup, don't silently fall back) |
| No rate limiting on `/auth/login` | `main.py` | Add slowapi or simple in-memory limiter — brute force is trivial otherwise |
| No password policy | `schemas.py:UserCreate` | Minimum length / complexity validator |
| `github_url` not validated as a URL | `schemas.py:RepositoryCreate` | Use `pydantic.AnyUrl` or a custom validator, reject non-GitHub hosts explicitly |
| `QueryRequest.top_k` unbounded | `schemas.py:QueryRequest` | `top_k: int = Field(5, ge=1, le=20)` — an unbounded value lets one user force a huge, expensive context/LLM call |
| No CORS config | `main.py` | Add `CORSMiddleware` scoped to your actual frontend origin(s) once frontend is served separately (or same-origin if served by FastAPI's `StaticFiles`, in which case CORS isn't needed) |

---

## 6. File-by-file change list

### `backend/main.py`
- Add global exception handlers (see §4).
- Add `logging` setup call at startup.
- Add `CORSMiddleware` if frontend is served from a different origin/port than the API.
- Move `/auth/*` endpoints into their own `auth_router.py` (currently the only routes not in `router.py` — inconsistent).
- Mount `frontend/` via `StaticFiles` (the import already exists but is unused) if you want FastAPI to serve the UI directly, or drop the import if the frontend will be served separately (e.g. Vite dev server / static host).
- Add a `GET /health` endpoint (DB connectivity check) — needed for any real deployment/monitoring.

### `backend/router.py`
- Split into `routers/repositories.py` and `routers/chat.py` (currently one file doing both concerns).
- `create_repository`: move URL-parsing + file-saving + background-task kickoff into `services/repository_service.py::create_repository(...)`. Route becomes ~8 lines.
- Validate `github_url` shape before parsing; return 400 with a clear message instead of letting `IndexError` bubble up.
- Add duplicate-repo check (same `github_url` + `user_id`) before creating a new row.
- Bulk-insert `RepositoryFiles` (`db.add_all(...)` + one `db.flush()`) instead of one `db.flush()` per file.
- Add `GET /repositories/{id}` (single repo detail incl. status) — needed for the frontend to poll processing state.
- Add `DELETE /repositories/{id}` (cascade already configured in `models.py`, just missing the route).
- Add pagination (`limit`/`offset` or cursor) to `GET /repositories` and `GET /chat_history` — unbounded `.all()` will not scale.

### `backend/db.py`
- Fail fast if `DATABASE_URL` isn't set rather than silently defaulting to an incompatible SQLite URL.
- Configure `pool_size`/`max_overflow`/`pool_pre_ping=True` on `create_engine`.
- Replace `Base.metadata.create_all` with Alembic migrations once schema stabilizes (fine to defer past MVP).

### `backend/auth.py`
- Raise at import time if `JWT_SECRET_KEY` is missing (no default fallback).
- Add basic password strength validation (delegate to `schemas.py` validator).

### `backend/schemas.py`
- `RepositoryCreate.github_url`: validate as URL / GitHub host.
- `QueryRequest.top_k`: bound with `Field(ge=1, le=20)`.
- `QueryRequest.query`: bound max length (e.g. `Field(max_length=2000)`).

### `backend/models.py`
- Add unique constraint on (`user_id`, `github_url`) to prevent duplicate repo rows.
- Add explicit index on `RepositoryChunks.repository_id` (frequently filtered).
- Define the embedding dimension (`384`) as a shared constant used by both `models.py` and `services/embeddings.py`, so changing the embedding model can't silently desync the column size.

### `backend/chunker.py`
- Wrap `parser.parse(...)` in `asyncio.to_thread` (see §3).
- Add a max-file-size guard before parsing (skip/log files above a threshold instead of parsing arbitrarily large files).
- Wrap parse errors in try/except — log and skip the file rather than failing the whole repo.

### `backend/services/embeddings.py`
- Wrap `model.encode` in `asyncio.to_thread`.
- Support batch encoding (`model.encode(list_of_texts)`) and call it from `process_chunks` in batches instead of one at a time.

### `backend/services/processor.py`
- Fix the session leak: use `with SessionLocal() as db:` (or a proper context-managed session) instead of `next(get_db())`.
- Wrap the whole pipeline in try/except: on failure, set `repository.status = "failed"`, log the exception, `db.rollback()`.
- On success, set `repository.status = "completed"`.
- Commit in batches (e.g. every 100 chunks) instead of one commit at the very end, so partial progress survives a mid-run crash.

### `backend/services/llm.py`
- Move `AsyncGroq(api_key=...)` client construction to module level (singleton), not per-call.
- Wrap the API call in try/except with a timeout; raise a clean, typed error the route layer can turn into a proper HTTP response instead of an unhandled 500.

### `backend/services/rag.py`
- No structural issues; once `answer_query` is called from a properly error-handled route, this is fine as-is.

### `backend/github_parser/tarfile.py`
- **Rename file** to `github_archive.py` (avoid shadowing stdlib `tarfile`).
- Fix the `file_obj` bug (§2, item 1) — initialize `file_obj = None` at the top of each loop iteration.
- Remove the dead `from passlib import ext` import.
- Replace `print(...)` with `logger.info(...)`.
- Add a timeout to the `httpx.AsyncClient` (e.g. `timeout=30.0`).
- Add a max archive size check on `response.content` before buffering into memory.
- Wrap the synchronous tar extraction in `asyncio.to_thread`.

### `backend/requirements.txt`
- `sentry-sdk` is installed but unused — either wire it up (§4) or remove it to stop tracking a dependency you don't use.

---

## 7. Feature ideas (beyond fixing what exists)

- **Live processing status**: WebSocket or polling endpoint (`GET /repositories/{id}/status`) so the frontend can show a progress indicator instead of guessing.
- **Re-index button**: re-run processing for a repo whose branch has moved or that previously failed.
- **Streaming answers**: Groq supports streaming completions — stream the LLM response to the frontend token-by-token instead of waiting for the full answer (much better perceived latency).
- **Clickable sources**: `answer_query` already returns `file_path` + `chunk_id` per source — surface these as clickable references that show the actual chunk content.
- **Per-repo chat threads**: currently chat history is a flat list per user; consider scoping/grouping by repository in the UI (the data already supports it).
- **Usage limits**: cap repos-per-user and queries-per-day to control Groq API cost, especially before this is opened to more users.
- **Private repo support**: `fetch_repo_tree_and_files` already accepts a `github_token` param but nothing in the API/schema passes one through — wire up GitHub OAuth or a PAT input if private repos are in scope.

---

## 8. Frontend plan

Existing `frontend/*.html|js` targets a different, unrelated API and will be replaced.

**Pages:**
1. **Login / Register** — single page, toggle between modes (reuse the existing pattern from `auth.js`, just repointed — that part of the old frontend's approach was actually fine).
2. **Dashboard** — list of connected repositories with status badges (processing/completed/failed), "+ Add repository" form (name, GitHub URL, branch).
3. **Repository chat** — chat interface scoped to one repository: message list, input box, source citations under each answer, loading state while waiting on the LLM.
4. **Chat history** — list of past Q&A across all repos (or per-repo), with delete.

**Behavior notes given current API:**
- Since `GET /repositories` doesn't yet expose live status transitions (bug #3 above), the frontend will poll `GET /repositories` every few seconds and show "Processing…" for any repo whose status isn't `completed`/`failed` — this is a stopgap until the backend fix lands.
- All requests go through a shared `apiFetch` helper (token attach, 401 → redirect to login, error message surfacing) — same pattern as the old `api.js`, just pointed at the real endpoints.

---

## 9. Suggested phasing

1. **Now**: Build frontend against the current (as-is) API — functional, but inherits the backend's rough edges (stuck "processing" state, occasional 500s on bad input, slow chat responses under load).
2. **Next**: Fix the critical bugs in §2 (these are correctness bugs, not style) — especially the `file_obj` crash, the session leak, and the missing status updates, since the frontend directly depends on `status` being accurate.
3. **Then**: Concurrency fixes (§3) — required before more than one user can use this comfortably at the same time.
4. **Then**: Logging/exception handling (§4) and security hardening (§5).
5. **Ongoing**: Feature ideas (§7) as prioritized by you.
