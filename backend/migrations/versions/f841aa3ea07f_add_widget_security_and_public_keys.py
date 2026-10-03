"""add_widget_security_and_public_keys

Revision ID: f841aa3ea07f
Revises: ea2363451b55
Create Date: 2026-09-26 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f841aa3ea07f'
down_revision: Union[str, None] = 'ea2363451b55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add public_key column to businesses (nullable=True initially)
    op.add_column(
        'businesses',
        sa.Column('public_key', sa.String(length=64), nullable=True)
    )

    # 2. Backfill existing businesses with public_key (pk_<32_hex_chars>)
    op.execute(
        "UPDATE businesses SET public_key = 'pk_' || substr(md5(random()::text || id::text), 1, 32) WHERE public_key IS NULL"
    )

    # 3. Enforce nullable=False on public_key
    op.alter_column('businesses', 'public_key', nullable=False)

    # 4. Create unique index on businesses.public_key
    op.create_index(
        op.f('ix_businesses_public_key'),
        'businesses',
        ['public_key'],
        unique=True
    )

    # 5. Add allowed_domains and allow_localhost columns to widget_configs
    op.add_column(
        'widget_configs',
        sa.Column('allowed_domains', sa.JSON(), nullable=True, server_default='[]')
    )
    op.add_column(
        'widget_configs',
        sa.Column('allow_localhost', sa.Boolean(), nullable=False, server_default=sa.true())
    )


def downgrade() -> None:
    # 1. Drop widget_configs columns
    op.drop_column('widget_configs', 'allow_localhost')
    op.drop_column('widget_configs', 'allowed_domains')

    # 2. Drop unique index and public_key column from businesses
    op.drop_index(op.f('ix_businesses_public_key'), table_name='businesses')
    op.drop_column('businesses', 'public_key')
