"""create batch_jobs and resume_results tables

Revision ID: 7849be8789e6
Revises: 
Create Date: 2026-03-06 20:02:51.773277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7849be8789e6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create batch_jobs and resume_results tables."""
    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "resume_results",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("job_id", sa.UUID(), sa.ForeignKey("batch_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("text_preview", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("people", sa.JSON(), nullable=True),
        sa.Column("info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_resume_results_job_id", "resume_results", ["job_id"])


def downgrade() -> None:
    """Drop resume_results and batch_jobs tables."""
    op.drop_table("resume_results")
    op.drop_table("batch_jobs")

