"""Add LLM settings to businesses.

Revision ID: a19f4c2d7e31
Revises: ccd3ae6edeb7
Create Date: 2026-09-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a19f4c2d7e31"
down_revision: Union[str, None] = "ccd3ae6edeb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "businesses",
        sa.Column("llm_provider", sa.String(length=20), nullable=True, server_default="gemini"),
    )
    op.alter_column("businesses", "llm_provider", server_default=None)
    op.add_column("businesses", sa.Column("llm_api_key", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("businesses", "llm_api_key")
    op.drop_column("businesses", "llm_provider")
