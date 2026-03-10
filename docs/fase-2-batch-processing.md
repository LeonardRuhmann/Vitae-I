# Phase 2 — Batch Processing & Production Architecture

> **Date**: 2026-03-10  
> **Status**: Implemented  
> **Migration**: `ed0b08ebec92` (add error tracking to resume results)

---

## 1. Overview

Evolution from the single-file, synchronous `/analyze` endpoint to support **batch upload** of up to 10 resumes per request, with asynchronous background processing and automatic disaster recovery.

### Architecture Summary

```
Client                           Server (Free Tier)
──────                           ──────────────────
POST /upload-batch ──────► Validation (max 10, PDF only)
  - X-Session-ID                      │
  - files[]                           ▼
                              Save PDFs to /tmp/
                              Create BatchJob (PROCESSING)
  ◄── HTTP 202 { job_id }            │
                                      ▼
                              BackgroundTask → process_batch()
                                 ┌── Semaphore(1) ──┐
                                 │  asyncio.to_thread(nlp, text)  │
                                 └──────────────────┘
                                      │
                              For each PDF:
                                try → ResumeResult(SUCCESS)
                                except → ResumeResult(FAILED)
                                finally → delete PDF, increment counter
                                      │
                              BatchJob.status = COMPLETED
```

---

## 2. Architecture Decisions

### 2.1 Background Processing: `BackgroundTasks` + `asyncio.to_thread()`

**Alternatives considered:**

| Option | Discarded because |
|---|---|
| Celery + Redis | Adds 2 heavy dependencies; not viable on Free Tier |
| Pure `asyncio.create_task()` | spaCy is CPU-bound — would block the Event Loop |
| `ProcessPoolExecutor` | Duplicates the spaCy model in RAM (~500MB) per worker |

**Decision**: `BackgroundTasks` (native to FastAPI) with `asyncio.to_thread()` to offload the synchronous spaCy call. The `Semaphore(1)` ensures only one NLP inference runs at a time, protecting CPU and RAM.

**Trade-off**: If the API process dies, in-flight Background Tasks are **lost**. This is mitigated by Disaster Recovery (section 2.4).

---

### 2.2 Ephemeral Disk Storage

Uploaded PDFs are saved to `/tmp/vitae_uploads/{job_id}/` before processing.

**Why?**
- **RAM efficiency**: Avoids keeping N PDFs in memory simultaneously
- **Intra-process resilience**: If one PDF crashes, the others are still on disk

**Trade-off**: On Free Tier, the disk is **ephemeral** — wiped on every container restart. The PDFs only serve as RAM relief during the process lifetime, **not for cross-restart recovery**.

---

### 2.3 Per-File Status (`ResultStatus`)

Each `ResumeResult` has its own `status` (SUCCESS/FAILED) and `error_message`. The parent `BatchJob` is always marked `COMPLETED` when the loop finishes, regardless of how many individual files failed.

**Why?** `COMPLETED` means "the job finished processing", not "everything succeeded". The per-file status gives the frontend granularity to show which resumes need to be re-uploaded.

---

### 2.4 Disaster Recovery ("Accept the Loss")

On API startup (via `lifespan`), all `BatchJob` records with status `PENDING` or `PROCESSING` are marked as `FAILED`.

**Premise**: Free Tier disk is wiped on every restart. There are no PDFs to reprocess. The strategy is to **accept the loss** and notify the frontend, which tells the user to re-upload.

**Trade-off**: Jobs partially processed before a crash will have some `ResumeResult` entries saved and others missing. The frontend should treat `FAILED` as "incomplete batch — please re-upload".

---

### 2.5 Pragmatic Authentication (`X-Session-ID`)

The `user_id` is extracted from the `X-Session-ID` header with no authenticity validation.

**Accepted risks:**
- Any client can forge any `user_id`
- No real isolation between users

**Justification**: For an MVP/portfolio project, real authentication (JWT, OAuth) would add disproportionate complexity relative to the value delivered. This is the most significant technical debt from Phase 2.

---

## 3. Technical Debts

| # | Debt | Severity | When to address |
|---|---|---|---|
| **TD-01** | `X-Session-ID` with no real authentication | 🔴 High | Before production with real data |
| **TD-02** | `api.py` bundles endpoint, processing engine, and lifespan (~350 lines) | 🟡 Medium | When it exceeds ~500 lines, extract into `routes/`, `services/` |
| **TD-03** | No job status query endpoint (`GET /jobs/{id}`) | 🟡 Medium | Phase 3 (frontend polling) |
| **TD-04** | Integration tests (with real DB) not implemented | 🟡 Medium | When CI/CD is configured |
| **TD-05** | No rate limiting per `user_id` | 🟢 Low | When there are multiple real users |
| **TD-06** | No pagination for listing job results | 🟢 Low | When batches larger than 10 are supported |

---

## 4. Files Modified

| File | What changed |
|---|---|
| `db/models.py` | Added `ResultStatus` enum; `status` and `error_message` columns on `ResumeResult` |
| `api.py` | Disaster Recovery in lifespan; `POST /upload-batch` endpoint; `process_batch()` engine |
| `tests/test_api.py` | 4 new tests (missing session ID, exceeds limit, non-PDF, success) |
| `alembic/versions/ed0b08ebec92_*.py` | Migration with PostgreSQL enum creation and VARCHAR→enum conversion |

---

## 5. How to Test

```bash
# Unit tests (no database required)
pytest tests/test_api.py -v

# Manual smoke test (with database)
uvicorn api:app --reload
curl -X POST http://localhost:8000/upload-batch \
  -H "X-Session-ID: test-user" \
  -F "files=@resume.pdf"
# Expected: HTTP 202 {"job_id": "..."}
```
