"""add error tracking to resume results

Revision ID: ed0b08ebec92
Revises: 7849be8789e6
Create Date: 2026-03-10 00:09:27.575382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ed0b08ebec92'
down_revision: Union[str, Sequence[str], None] = '7849be8789e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define enum types explicitly
jobstatus_enum = postgresql.ENUM(
    'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED',
    name='jobstatus', create_type=False,
)
resultstatus_enum = postgresql.ENUM(
    'SUCCESS', 'FAILED',
    name='resultstatus', create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Create PostgreSQL enum types
    jobstatus_enum.create(op.get_bind(), checkfirst=True)
    resultstatus_enum.create(op.get_bind(), checkfirst=True)

    # 2) Convert batch_jobs.status: VARCHAR → jobstatus enum
    #    Must drop the default first (it's a VARCHAR literal that can't auto-cast)
    op.execute("ALTER TABLE batch_jobs ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE batch_jobs "
        "ALTER COLUMN status TYPE jobstatus USING status::jobstatus"
    )
    op.execute("ALTER TABLE batch_jobs ALTER COLUMN status SET DEFAULT 'PENDING'")

    # 3) Add new columns to resume_results
    op.add_column(
        'resume_results',
        sa.Column('status', resultstatus_enum, nullable=False, server_default='SUCCESS'),
    )
    op.add_column(
        'resume_results',
        sa.Column('error_message', sa.Text(), nullable=True),
    )

    # 4) Tighten JSON columns to NOT NULL (matching updated model)
    op.alter_column('resume_results', 'skills',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.alter_column('resume_results', 'people',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.alter_column('resume_results', 'info',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)

    # 5) Swap index: drop job_id index, add status index
    op.drop_index(op.f('ix_resume_results_job_id'), table_name='resume_results')
    op.create_index(op.f('ix_resume_results_status'), 'resume_results', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse index swap
    op.drop_index(op.f('ix_resume_results_status'), table_name='resume_results')
    op.create_index(op.f('ix_resume_results_job_id'), 'resume_results', ['job_id'], unique=False)

    # Loosen JSON columns back to nullable
    op.alter_column('resume_results', 'info',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('resume_results', 'people',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('resume_results', 'skills',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)

    # Drop new columns
    op.drop_column('resume_results', 'error_message')
    op.drop_column('resume_results', 'status')

    # Convert batch_jobs.status back to VARCHAR
    op.execute("ALTER TABLE batch_jobs ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE batch_jobs "
        "ALTER COLUMN status TYPE VARCHAR(20) USING status::text"
    )
    op.execute("ALTER TABLE batch_jobs ALTER COLUMN status SET DEFAULT 'PENDING'")

    # Drop enum types
    resultstatus_enum.drop(op.get_bind(), checkfirst=True)
    jobstatus_enum.drop(op.get_bind(), checkfirst=True)
