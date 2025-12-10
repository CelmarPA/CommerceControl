"""add credit columns and policies

Revision ID: add_credit_engine
Revises: <prev_rev>
Create Date: 2025-12-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_credit_engine'
down_revision = '<prev_rev>'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('customers', sa.Column('credit_limit', sa.Numeric(12,2), nullable=True))
    op.add_column('customers', sa.Column('credit_profile', sa.String(length=1), nullable=False, server_default='C'))
    op.add_column('customers', sa.Column('credit_score', sa.Integer(), nullable=False, server_default='600'))
    op.add_column('customers', sa.Column('max_overdue_days', sa.Integer(), nullable=True))

    op.create_table(
        'credit_policies',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('profile', sa.String(length=1), unique=True, nullable=False),
        sa.Column('max_installments', sa.Integer, nullable=False, server_default='6'),
        sa.Column('max_sale_amount', sa.Numeric(12,2), nullable=True),
        sa.Column('max_percentage_of_limit', sa.Numeric(5,2), nullable=False, server_default='100'),
        sa.Column('max_delay_days', sa.Integer, nullable=False, server_default='30'),
        sa.Column('max_open_invoices', sa.Integer, nullable=False, server_default='5'),
        sa.Column('allow_credit', sa.Boolean, nullable=False, server_default='1'),
    )

def downgrade():
    op.drop_table('credit_policies')
    op.drop_column('customers', 'max_overdue_days')
    op.drop_column('customers', 'credit_score')
    op.drop_column('customers', 'credit_profile')
    op.drop_column('customers', 'credit_limit')
