"""Add receipt_path column to expenses table

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"


def upgrade():
    op.add_column("expenses", sa.Column("receipt_path", sa.String(), nullable=True))


def downgrade():
    op.drop_column("expenses", "receipt_path")
