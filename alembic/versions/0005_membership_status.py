"""Add membership_status, membership_updated_at, membership_updated_by, opt_out_reason to travellers.
Also create membership_audit table.

Revision ID: 0005_membership_status
Revises: 0004_traveller_directory_groups
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_membership_status'
down_revision = '0004_traveller_directory_groups'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('travellers', sa.Column('membership_status', sa.String(), nullable=True, server_default='ACTIVE'))
    op.add_column('travellers', sa.Column('membership_updated_at', sa.DateTime(), nullable=True))
    op.add_column('travellers', sa.Column('membership_updated_by', sa.String(), nullable=True))
    op.add_column('travellers', sa.Column('opt_out_reason', sa.String(), nullable=True))
    op.create_index('ix_travellers_membership_status', 'travellers', ['membership_status'])

    # Migrate existing participation_status values to membership_status
    op.execute("UPDATE travellers SET membership_status = 'ACTIVE' WHERE membership_status IS NULL")
    op.execute("UPDATE travellers SET participation_status = 'ACTIVE' WHERE participation_status IN ('INVITED', 'CONFIRMED', 'WAITLISTED')")
    op.execute("UPDATE travellers SET participation_status = 'ACTIVE', membership_status = 'ACTIVE' WHERE participation_status = 'CONFIRMED'")

    # Create audit trail table
    op.create_table(
        'membership_audit',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('traveller_id', sa.String(), sa.ForeignKey('travellers.traveller_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('trip_id', sa.String(), nullable=False, index=True),
        sa.Column('old_status', sa.String(), nullable=True),
        sa.Column('new_status', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('membership_audit')
    op.drop_index('ix_travellers_membership_status', table_name='travellers')
    op.drop_column('travellers', 'opt_out_reason')
    op.drop_column('travellers', 'membership_updated_by')
    op.drop_column('travellers', 'membership_updated_at')
    op.drop_column('travellers', 'membership_status')
