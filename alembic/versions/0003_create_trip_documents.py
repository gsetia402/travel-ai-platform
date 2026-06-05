"""create trip_documents table

Revision ID: 0003_create_trip_documents
Revises: 0002_phone_unique_index
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_create_trip_documents'
down_revision = '0002_phone_unique_index'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'trip_documents',
        sa.Column('document_id', sa.String(), primary_key=True),
        sa.Column('organization_id', sa.String(), nullable=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('storage_provider', sa.String(), nullable=False, server_default='local'),
        sa.Column('storage_key', sa.String(), nullable=False),
        sa.Column('visibility', sa.String(), nullable=False, server_default='ALL_TRAVELLERS'),
        sa.Column('uploaded_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_trip_documents_document_id', 'trip_documents', ['document_id'])
    op.create_index('ix_trip_documents_trip_id', 'trip_documents', ['trip_id'])
    op.create_index('ix_trip_documents_organization_id', 'trip_documents', ['organization_id'])
    op.create_index('ix_trip_documents_document_type', 'trip_documents', ['document_type'])


def downgrade() -> None:
    op.drop_index('ix_trip_documents_document_type')
    op.drop_index('ix_trip_documents_organization_id')
    op.drop_index('ix_trip_documents_trip_id')
    op.drop_index('ix_trip_documents_document_id')
    op.drop_table('trip_documents')
