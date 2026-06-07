"""Add financial_model column to trips table

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"


def upgrade():
    op.add_column("trips", sa.Column("financial_model", sa.String(), nullable=False, server_default="SPONSORED"))


def downgrade():
    op.drop_column("trips", "financial_model")
