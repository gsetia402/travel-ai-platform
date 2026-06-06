"""create traveller_master, traveller_groups, group_members, trip_travellers tables

Revision ID: 0004_traveller_directory_groups
Revises: 0003_create_trip_documents
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_traveller_directory_groups'
down_revision = '0003_create_trip_documents'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Traveller Master Directory
    op.create_table(
        'traveller_master',
        sa.Column('master_id', sa.String(), primary_key=True),
        sa.Column('organization_id', sa.String(), sa.ForeignKey('organizations.organization_id', ondelete='CASCADE'), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('nationality', sa.String(), nullable=True),
        sa.Column('emergency_contact_name', sa.String(), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(), nullable=True),
        sa.Column('emergency_relationship', sa.String(), nullable=True),
        sa.Column('medical_conditions', sa.Text(), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('special_requirements', sa.Text(), nullable=True),
        sa.Column('dietary_preferences', sa.String(), nullable=True),
        sa.Column('passport_number', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_traveller_master_master_id', 'traveller_master', ['master_id'])
    op.create_index('ix_traveller_master_organization_id', 'traveller_master', ['organization_id'])
    op.create_index('ix_traveller_master_phone', 'traveller_master', ['phone'])
    op.create_index('ix_traveller_master_email', 'traveller_master', ['email'])

    # Traveller Groups
    op.create_table(
        'traveller_groups',
        sa.Column('group_id', sa.String(), primary_key=True),
        sa.Column('organization_id', sa.String(), sa.ForeignKey('organizations.organization_id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_traveller_groups_group_id', 'traveller_groups', ['group_id'])
    op.create_index('ix_traveller_groups_organization_id', 'traveller_groups', ['organization_id'])

    # Group Members (many-to-many)
    op.create_table(
        'group_members',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('group_id', sa.String(), sa.ForeignKey('traveller_groups.group_id', ondelete='CASCADE'), nullable=False),
        sa.Column('master_id', sa.String(), sa.ForeignKey('traveller_master.master_id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'])
    op.create_index('ix_group_members_master_id', 'group_members', ['master_id'])
    op.create_index('ix_group_members_unique', 'group_members', ['group_id', 'master_id'], unique=True)

    # Trip Travellers (many-to-many: trips <-> traveller_master)
    op.create_table(
        'trip_travellers',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('master_id', sa.String(), sa.ForeignKey('traveller_master.master_id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_via', sa.String(), nullable=True),
        sa.Column('added_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_trip_travellers_trip_id', 'trip_travellers', ['trip_id'])
    op.create_index('ix_trip_travellers_master_id', 'trip_travellers', ['master_id'])
    op.create_index('ix_trip_travellers_unique', 'trip_travellers', ['trip_id', 'master_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_trip_travellers_unique')
    op.drop_index('ix_trip_travellers_master_id')
    op.drop_index('ix_trip_travellers_trip_id')
    op.drop_table('trip_travellers')

    op.drop_index('ix_group_members_unique')
    op.drop_index('ix_group_members_master_id')
    op.drop_index('ix_group_members_group_id')
    op.drop_table('group_members')

    op.drop_index('ix_traveller_groups_organization_id')
    op.drop_index('ix_traveller_groups_group_id')
    op.drop_table('traveller_groups')

    op.drop_index('ix_traveller_master_email')
    op.drop_index('ix_traveller_master_phone')
    op.drop_index('ix_traveller_master_organization_id')
    op.drop_index('ix_traveller_master_master_id')
    op.drop_table('traveller_master')
