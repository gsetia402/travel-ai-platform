"""add unique constraint and index on users.phone

Revision ID: 0002_phone_unique_index
Revises: 0001_create_all_tables
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_phone_unique_index'
down_revision = '0001_create_all_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_users_phone', 'users', ['phone'], unique=True)


def downgrade():
    op.drop_index('ix_users_phone', table_name='users')
