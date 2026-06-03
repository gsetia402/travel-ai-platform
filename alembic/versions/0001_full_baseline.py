"""full baseline — create all tables for fresh PostgreSQL databases

Revision ID: 0001_full_baseline
Revises: 0e132d0c667b
Create Date: 2026-06-03

This migration is a no-op when run against a database that already has the
tables (e.g. SQLite dev). For a fresh PostgreSQL database, run
  Base.metadata.create_all()
at startup (which the app already does), then stamp Alembic:
  alembic stamp head
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001_full_baseline'
down_revision: Union[str, None] = '0e132d0c667b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables are created by Base.metadata.create_all() at startup.
    # This revision exists so Alembic's version history starts from
    # a known baseline. Future migrations will build on top of this.
    pass


def downgrade() -> None:
    pass
