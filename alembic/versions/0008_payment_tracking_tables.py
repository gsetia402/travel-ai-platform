"""Create payments and trip_payment_config tables"""
from alembic import op
import sqlalchemy as sa

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payments',
        sa.Column('payment_id', sa.String(), primary_key=True),
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), nullable=False),
        sa.Column('traveller_id', sa.String(), sa.ForeignKey('travellers.traveller_id', ondelete='CASCADE'), nullable=True),
        sa.Column('payment_type', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('proof_path', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='APPROVED'),
        sa.Column('rejected_reason', sa.String(), nullable=True),
        sa.Column('sponsor_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'trip_payment_config',
        sa.Column('trip_id', sa.String(), sa.ForeignKey('trips.trip_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('expected_amount_per_traveller', sa.Float(), server_default='0'),
        sa.Column('registration_fee_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('registration_fee_amount', sa.Float(), server_default='0'),
        sa.Column('sponsor_name', sa.String(), nullable=True),
        sa.Column('sponsor_commitment', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('trip_payment_config')
    op.drop_table('payments')
