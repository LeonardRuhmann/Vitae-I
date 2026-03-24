import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all models."""


class JobStatus(str, enum.Enum):
    """Strict enum for BatchJob.status — guarantees data integrity."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ResultStatus(str, enum.Enum):
    """Per-file outcome inside a batch — SUCCESS or FAILED."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(default=JobStatus.PENDING)
    total_files: Mapped[int] = mapped_column(default=0)
    processed_files: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship: one job → many results
    results: Mapped[list["ResumeResult"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<BatchJob {self.id} status={self.status.value}>"


class ResumeResult(Base):
    __tablename__ = "resume_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batch_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[ResultStatus] = mapped_column(
        default=ResultStatus.SUCCESS, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_preview: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[dict] = mapped_column(JSON, default=dict)
    people: Mapped[list] = mapped_column(JSON, default=list)
    info: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship back to parent job
    job: Mapped["BatchJob"] = relationship(back_populates="results")

    def __repr__(self) -> str:
        return f"<ResumeResult {self.id} file={self.file_name!r}>"
