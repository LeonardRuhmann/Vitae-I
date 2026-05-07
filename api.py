import asyncio
import logging
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import spacy
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from config import (
    API_TITLE,
    API_VERSION,
    LOCATIONS,
    ORGANIZATIONS,
    SKILLS,
    SPACY_MODEL,
)
from db.models import BatchJob, JobStatus, ResumeResult, ResultStatus
from db.session import async_session
from utils import clean_text, is_valid_entity, normalize_skill, read_pdf

logger = logging.getLogger("vitae")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
UPLOAD_DIR = Path("/tmp/vitae_uploads")
MAX_BATCH_SIZE = 10

# Semaphore: allow only 1 concurrent spaCy call to protect CPU / RAM.
_processing_semaphore = asyncio.Semaphore(1)


# ---------------------------------------------------------------------------
# WebSocket Connection Manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        # Maps job_id -> list of active connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.debug("WebSocket connected to job '%s'. Active: %d", job_id, len(self.active_connections[job_id]))

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            try:
                self.active_connections[job_id].remove(websocket)
                logger.debug("WebSocket disconnected from job '%s'.", job_id)
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]
            except ValueError:
                logger.debug("WebSocket already removed from job '%s'. Skipping.", job_id)

    async def broadcast_to_job(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            # Create a copy of the list to iterate over safely
            connections = list(self.active_connections[job_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error("Failed to send WebSocket message for job %s: %s", job_id, e)
                    self.disconnect(connection, job_id)

manager = ConnectionManager()


# ---------------------------------------------------------------------------
# NLP helpers (unchanged)
# ---------------------------------------------------------------------------
def make_phrase_patterns(items: list[str], label: str) -> list[dict]:
    patterns = []
    for item in items:
        toks = [tok.lower() for tok in item.split()]
        patterns.append({"label": label, "pattern": [{"LOWER": t} for t in toks]})
    return patterns


def load_model_with_ruler() -> spacy.Language:
    nlp = spacy.load(SPACY_MODEL)
    ruler = nlp.add_pipe(
        "entity_ruler", config={"overwrite_ents": False}, before="ner"
    )

    patterns = []
    patterns += make_phrase_patterns(SKILLS, "SKILL")
    patterns += make_phrase_patterns(ORGANIZATIONS, "ORG")
    patterns += make_phrase_patterns(LOCATIONS, "GPE")

    ruler.add_patterns(patterns)
    return nlp


# ---------------------------------------------------------------------------
# Disaster Recovery + Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load spaCy model & recover zombie jobs.  Shutdown: clean up."""

    # 1) Load the NLP model
    app.state.nlp = load_model_with_ruler()

    # 2) Disaster Recovery — mark interrupted jobs as FAILED
    async with async_session() as session:
        result = await session.execute(
            select(BatchJob).where(
                BatchJob.status.in_([JobStatus.PENDING, JobStatus.PROCESSING])
            )
        )
        zombie_jobs = result.scalars().all()

        if zombie_jobs:
            zombie_ids = [job.id for job in zombie_jobs]
            await session.execute(
                update(BatchJob)
                .where(BatchJob.id.in_(zombie_ids))
                .values(status=JobStatus.FAILED)
            )
            await session.commit()
            logger.warning(
                "Disaster Recovery: marked %d zombie job(s) as FAILED: %s",
                len(zombie_ids),
                zombie_ids,
            )
        else:
            logger.info("Disaster Recovery: no zombie jobs found.")

    yield  # ---- app is running ----

    # Shutdown: nothing to clean up explicitly


app = FastAPI(title=API_TITLE, version=API_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Original single-file endpoint (kept for backward compatibility)
# ---------------------------------------------------------------------------
@app.post("/analyze")
async def analyze_resume(request: Request, file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()
    raw_text = read_pdf(content)

    if not raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Couldn't extract text from PDF. It might be an image scan",
        )

    processed_text = clean_text(raw_text)

    nlp = request.app.state.nlp
    doc = nlp(processed_text)

    skills = set()
    people = []
    info = set()

    for ent in doc.ents:
        if ent.label_ == "SKILL":
            skills.add(ent.text)
        elif ent.label_ == "PER" and not people and is_valid_entity(ent.text, ent.label_):
            people.append(ent.text)
        else:
            if is_valid_entity(ent.text, ent.label_):
                info.add(ent.text)

    return {
        "text_preview": processed_text,
        "skills": list(skills),
        "people": people,
        "info": list(info),
    }


# ---------------------------------------------------------------------------
# Batch upload endpoint  (Phase 2)
# ---------------------------------------------------------------------------
@app.post("/upload-batch", status_code=202)
async def upload_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    job_description: str = Form(""),
):
    # --- Auth (pragmatic) ---
    user_id = request.headers.get("X-Session-ID")
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Session-ID header.",
        )

    # --- Hard limit ---
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_BATCH_SIZE} files per batch. You sent {len(files)}.",
        )

    # --- Validate all files are PDFs ---
    for f in files:
        if f.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"File '{f.filename}' is not a PDF (got {f.content_type}).",
            )

    # --- ATS Matcher: extract skills from Job Description (pre-loop) ---
    nlp = request.app.state.nlp
    jd_skills: set[str] | None = None

    if job_description.strip():
        jd_doc = nlp(job_description)
        jd_skills = {
            normalize_skill(ent.text) for ent in jd_doc.ents if ent.label_ == "SKILL"
        }

        if not jd_skills:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Could not identify any technologies in the job description. "
                    "Please provide a more detailed description with specific "
                    "skills and technologies."
                ),
            )

    # --- Create the job in the DB ---
    job_id = uuid.uuid4()

    async with async_session() as session:
        job = BatchJob(
            id=job_id,
            user_id=user_id,
            status=JobStatus.PROCESSING,
            total_files=len(files),
            processed_files=0,
            job_description_text=job_description.strip() or None,
            job_requirements=list(jd_skills) if jd_skills else None,
        )
        session.add(job)
        await session.commit()

    # --- Save PDFs to disk ---
    job_dir = UPLOAD_DIR / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    file_paths: list[tuple[str, Path]] = []  # (original_name, disk_path)
    seen_names: dict[str, int] = {}

    for f in files:
        original_name = f.filename or "unnamed.pdf"

        # Handle duplicate names within the same batch
        if original_name in seen_names:
            seen_names[original_name] += 1
            stem = Path(original_name).stem
            suffix = Path(original_name).suffix or ".pdf"
            disk_name = f"{stem}_{seen_names[original_name]}{suffix}"
        else:
            seen_names[original_name] = 0
            disk_name = original_name

        dest = job_dir / disk_name
        content = await f.read()
        dest.write_bytes(content)
        file_paths.append((original_name, dest))

    # --- Delegate processing ---
    background_tasks.add_task(
        process_batch,
        job_id=job_id,
        file_paths=file_paths,
        nlp=nlp,
        jd_skills=jd_skills,
    )

    return {"job_id": str(job_id)}


# ---------------------------------------------------------------------------
# Background batch processor
# ---------------------------------------------------------------------------
async def process_batch(
    job_id: uuid.UUID,
    file_paths: list[tuple[str, Path]],
    nlp: spacy.Language,
    jd_skills: set[str] | None = None,
) -> None:
    """Process every PDF in the batch, saving results one-by-one."""
    total_files = len(file_paths)
    processed_count = 0

    for original_name, path in file_paths:
        try:
            # Read PDF from disk
            pdf_bytes = path.read_bytes()
            raw_text = read_pdf(pdf_bytes)

            if not raw_text.strip():
                raise ValueError("Could not extract text (possibly an image scan)")

            processed_text = clean_text(raw_text)

            # Run spaCy inside the semaphore, offloaded to a thread
            async with _processing_semaphore:
                doc = await asyncio.to_thread(nlp, processed_text)

            # Extract entities
            skills: set[str] = set()
            people: list[str] = []
            info: set[str] = set()

            for ent in doc.ents:
                if ent.label_ == "SKILL":
                    skills.add(ent.text)
                elif (
                    ent.label_ == "PER"
                    and not people
                    and is_valid_entity(ent.text, ent.label_)
                ):
                    people.append(ent.text)
                else:
                    if is_valid_entity(ent.text, ent.label_):
                        info.add(ent.text)

            # ATS Matcher: compute score if JD skills were provided
            match_score: float | None = None
            if jd_skills:
                resume_skills_normalized = {normalize_skill(s) for s in skills}
                common = jd_skills & resume_skills_normalized
                match_score = round((len(common) / len(jd_skills)) * 100, 1)

            # Save successful result
            async with async_session() as session:
                session.add(
                    ResumeResult(
                        job_id=job_id,
                        file_name=original_name,
                        status=ResultStatus.SUCCESS,
                        text_preview=processed_text,
                        skills=list(skills),
                        people=people,
                        info=list(info),
                        match_score=match_score,
                    )
                )
                await session.commit()
            
            # Local status tracking for WebSocket
            current_status = ResultStatus.SUCCESS

        except Exception as exc:
            logger.error(
                "Failed to process '%s' in job %s: %s",
                original_name,
                job_id,
                exc,
            )
            # Save failed result
            async with async_session() as session:
                session.add(
                    ResumeResult(
                        job_id=job_id,
                        file_name=original_name,
                        status=ResultStatus.FAILED,
                        error_message=str(exc),
                        text_preview="",
                        skills=[],
                        people=[],
                        info=[],
                    )
                )
                await session.commit()
            
            # Local status tracking for WebSocket
            current_status = ResultStatus.FAILED

        finally:
            # Clean up temp file
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

            # Increment local counter
            processed_count += 1

            # Update DB processed counter
            async with async_session() as session:
                await session.execute(
                    update(BatchJob)
                    .where(BatchJob.id == job_id)
                    .values(processed_files=processed_count)
                )
                await session.commit()
            
            # Broadcast progress event to WebSockets
            await manager.broadcast_to_job(
                str(job_id),
                {
                    "type": "progress",
                    "processed_files": processed_count,
                    "total_files": total_files,
                    "latest_file": original_name,
                    "status": current_status.value,
                }
            )

    # --- All files processed → mark job as COMPLETED ---
    async with async_session() as session:
        await session.execute(
            update(BatchJob)
            .where(BatchJob.id == job_id)
            .values(status=JobStatus.COMPLETED)
        )
        await session.commit()
    
    # Broadcast completion event to WebSockets
    await manager.broadcast_to_job(
        str(job_id),
        {
            "type": "completed",
            "job_id": str(job_id)
        }
    )

    # Clean up empty job directory
    job_dir = UPLOAD_DIR / str(job_id)
    try:
        shutil.rmtree(job_dir, ignore_errors=True)
    except OSError:
        pass

    logger.info("Job %s completed.", job_id)


# ---------------------------------------------------------------------------
# WebSocket Endpoint (Phase 3.5)
# ---------------------------------------------------------------------------
@app.websocket("/ws/jobs/{job_id}")
async def websocket_job_status(websocket: WebSocket, job_id: str):
    """Real-time progress updates for a specific batch job."""
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive, wait for client messages if any
            # (Though currently we only push from server to client)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)


# ---------------------------------------------------------------------------
# REST Results Endpoint (Phase 3.5)
# ---------------------------------------------------------------------------
@app.get("/jobs/{job_id}")
async def get_job_results(job_id: uuid.UUID):
    """Fetch the final results for a completed batch job."""
    async with async_session() as session:
        # Eager load the results using selectinload
        result = await session.execute(
            select(BatchJob)
            .options(selectinload(BatchJob.results))
            .where(BatchJob.id == job_id)
        )
        job = result.scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Build response payload
    results_payload = [
        {
            "file_name": r.file_name,
            "status": r.status.value,
            "error_message": r.error_message,
            "skills": r.skills,
            "people": r.people,
            "info": r.info,
            "match_score": r.match_score,
        }
        for r in job.results
    ]

    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "total_files": job.total_files,
        "processed_files": job.processed_files,
        "job_requirements": job.job_requirements,
        "results": results_payload,
    }
