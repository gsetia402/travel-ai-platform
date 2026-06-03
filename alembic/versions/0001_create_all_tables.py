"""create all tables — full baseline

Revision ID: 0001_create_all_tables
Revises:
Create Date: 2026-06-03

Creates all 17 TripOps tables with indexes for a fresh PostgreSQL database.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001_create_all_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- organizations ---
    op.create_table(
        'organizations',
        sa.Column('organization_id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('organization_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_organizations_organization_id', 'organizations', ['organization_id'])

    # --- users ---
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(), primary_key=True),
        sa.Column('organization_id', sa.String(), sa.ForeignKey('organizations.organization_id', ondelete='CASCADE'), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), unique=True, nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='COORDINATOR'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_users_user_id', 'users', ['user_id'])
    op.create_index('ix_users_organization_id', 'users', ['organization_id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # --- user_preferences ---
    op.create_table(
        'user_preferences',
        sa.Column('user_id', sa.String(), primary_key=True),
        sa.Column('budget', sa.Integer(), nullable=True),
        sa.Column('trip_type', sa.String(), nullable=True),
        sa.Column('accommodation', sa.String(), nullable=True),
        sa.Column('food_preference', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])

    # --- trips ---
    op.create_table(
        'trips',
        sa.Column('trip_id', sa.String(), primary_key=True),
        sa.Column('trip_name', sa.String(), nullable=False),
        sa.Column('organization_name', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=True),
        sa.Column('origin_city', sa.String(), nullable=True),
        sa.Column('origin_state', sa.String(), nullable=True),
        sa.Column('destination', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('days', sa.Integer(), nullable=False),
        sa.Column('traveller_count', sa.Integer(), nullable=False),
        sa.Column('budget', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_trips_trip_id', 'trips', ['trip_id'])
    op.create_index('ix_trips_organization_id', 'trips', ['organization_id'])
    op.create_index('ix_trips_status', 'trips', ['status'])

    # --- travellers ---
    op.create_table(
        'travellers',
        sa.Column('traveller_id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('emergency_contact_name', sa.String(), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(), nullable=True),
        sa.Column('emergency_relationship', sa.String(), nullable=True),
        sa.Column('medical_conditions', sa.String(), nullable=True),
        sa.Column('allergies', sa.String(), nullable=True),
        sa.Column('special_requirements', sa.String(), nullable=True),
        sa.Column('dietary_preferences', sa.String(), nullable=True),
        sa.Column('passport_number', sa.String(), nullable=True),
        sa.Column('nationality', sa.String(), nullable=True),
        sa.Column('participation_status', sa.String(), nullable=True, server_default='INVITED'),
    )
    op.create_index('ix_travellers_traveller_id', 'travellers', ['traveller_id'])
    op.create_index('ix_travellers_trip_id', 'travellers', ['trip_id'])
    op.create_index('ix_travellers_email', 'travellers', ['email'])
    op.create_index('ix_travellers_phone', 'travellers', ['phone'])
    op.create_index('ix_travellers_participation_status', 'travellers', ['participation_status'])

    # --- rooms ---
    op.create_table(
        'rooms',
        sa.Column('room_id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_number', sa.String(), nullable=False),
        sa.Column('room_type', sa.String(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_rooms_room_id', 'rooms', ['room_id'])
    op.create_index('ix_rooms_trip_id', 'rooms', ['trip_id'])

    # --- room_allocations ---
    op.create_table(
        'room_allocations',
        sa.Column('allocation_id', sa.String(), primary_key=True),
        sa.Column('room_id', sa.String(), sa.ForeignKey('rooms.room_id', ondelete='CASCADE'), nullable=False),
        sa.Column('traveller_id', sa.String(), sa.ForeignKey('travellers.traveller_id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('allocated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_room_allocations_allocation_id', 'room_allocations', ['allocation_id'])
    op.create_index('ix_room_allocations_room_id', 'room_allocations', ['room_id'])
    op.create_index('ix_room_allocations_traveller_id', 'room_allocations', ['traveller_id'])

    # --- consents ---
    op.create_table(
        'consents',
        sa.Column('consent_id', sa.String(), primary_key=True),
        sa.Column('traveller_id', sa.String(), sa.ForeignKey('travellers.traveller_id', ondelete='CASCADE'), nullable=False),
        sa.Column('consent_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('signed_by', sa.String(), nullable=True),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_consents_consent_id', 'consents', ['consent_id'])
    op.create_index('ix_consents_traveller_id', 'consents', ['traveller_id'])
    op.create_index('ix_consents_status', 'consents', ['status'])

    # --- traveller_documents ---
    op.create_table(
        'traveller_documents',
        sa.Column('document_id', sa.String(), primary_key=True),
        sa.Column('traveller_id', sa.String(), sa.ForeignKey('travellers.traveller_id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('upload_status', sa.String(), nullable=False, server_default='COMPLETED'),
        sa.Column('verification_status', sa.String(), nullable=False, server_default='UPLOADED'),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verified_by', sa.String(), nullable=True),
        sa.Column('remarks', sa.String(), nullable=True),
    )
    op.create_index('ix_traveller_documents_document_id', 'traveller_documents', ['document_id'])
    op.create_index('ix_traveller_documents_traveller_id', 'traveller_documents', ['traveller_id'])
    op.create_index('ix_traveller_documents_document_type', 'traveller_documents', ['document_type'])

    # --- trip_document_requirements ---
    op.create_table(
        'trip_document_requirements',
        sa.Column('requirement_id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('mandatory', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )
    op.create_index('ix_trip_document_requirements_requirement_id', 'trip_document_requirements', ['requirement_id'])
    op.create_index('ix_trip_document_requirements_trip_id', 'trip_document_requirements', ['trip_id'])

    # --- expenses ---
    op.create_table(
        'expenses',
        sa.Column('expense_id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('vendor_name', sa.String(), nullable=True),
        sa.Column('paid_by', sa.String(), nullable=True),
        sa.Column('expense_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_expenses_expense_id', 'expenses', ['expense_id'])
    op.create_index('ix_expenses_trip_id', 'expenses', ['trip_id'])

    # --- communications ---
    op.create_table(
        'communications',
        sa.Column('communication_id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('audience_type', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_communications_communication_id', 'communications', ['communication_id'])
    op.create_index('ix_communications_trip_id', 'communications', ['trip_id'])

    # --- communication_recipients ---
    op.create_table(
        'communication_recipients',
        sa.Column('recipient_id', sa.String(), primary_key=True),
        sa.Column('communication_id', sa.String(), sa.ForeignKey('communications.communication_id', ondelete='CASCADE'), nullable=False),
        sa.Column('traveller_id', sa.String(), sa.ForeignKey('travellers.traveller_id', ondelete='CASCADE'), nullable=False),
        sa.Column('read_status', sa.String(), nullable=False, server_default='UNREAD'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_communication_recipients_recipient_id', 'communication_recipients', ['recipient_id'])
    op.create_index('ix_communication_recipients_communication_id', 'communication_recipients', ['communication_id'])
    op.create_index('ix_communication_recipients_traveller_id', 'communication_recipients', ['traveller_id'])

    # --- registration_links ---
    op.create_table(
        'registration_links',
        sa.Column('registration_link_id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('registration_code', sa.String(), unique=True, nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_registration_links_registration_link_id', 'registration_links', ['registration_link_id'])
    op.create_index('ix_registration_links_trip_id', 'registration_links', ['trip_id'])
    op.create_index('ix_registration_links_registration_code', 'registration_links', ['registration_code'], unique=True)

    # --- registration_form_configs ---
    op.create_table(
        'registration_form_configs',
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('collect_emergency_contact', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('collect_medical_information', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('collect_dietary_preferences', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('collect_passport_details', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('require_consent', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('require_date_of_birth', sa.Boolean(), server_default=sa.text('false')),
    )

    # --- invitations ---
    op.create_table(
        'invitations',
        sa.Column('invitation_id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipient_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('invitation_status', sa.String(), nullable=False, server_default='SENT'),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_invitations_invitation_id', 'invitations', ['invitation_id'])
    op.create_index('ix_invitations_trip_id', 'invitations', ['trip_id'])

    # --- trip_itineraries ---
    op.create_table(
        'trip_itineraries',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('itinerary_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_trip_itineraries_id', 'trip_itineraries', ['id'])
    op.create_index('ix_trip_itineraries_trip_id', 'trip_itineraries', ['trip_id'])


def downgrade() -> None:
    op.drop_table('trip_itineraries')
    op.drop_table('invitations')
    op.drop_table('registration_form_configs')
    op.drop_table('registration_links')
    op.drop_table('communication_recipients')
    op.drop_table('communications')
    op.drop_table('expenses')
    op.drop_table('trip_document_requirements')
    op.drop_table('traveller_documents')
    op.drop_table('consents')
    op.drop_table('room_allocations')
    op.drop_table('rooms')
    op.drop_table('travellers')
    op.drop_table('trips')
    op.drop_table('user_preferences')
    op.drop_table('users')
    op.drop_table('organizations')
