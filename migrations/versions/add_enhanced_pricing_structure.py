"""Add enhanced pricing structure to Home model

Revision ID: enhanced_pricing_001
Revises: add_payment_tables
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'enhanced_pricing_001'
down_revision = 'add_payment_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add new pricing fields to Home table
    with op.batch_alter_table('home', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price_first_2_hours', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('price_per_additional_hour', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('price_overnight', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('price_daytime', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('price_per_day', sa.Float(), nullable=True))


def downgrade():
    # Remove new pricing fields from Home table
    with op.batch_alter_table('home', schema=None) as batch_op:
        batch_op.drop_column('price_per_day')
        batch_op.drop_column('price_daytime')
        batch_op.drop_column('price_overnight')
        batch_op.drop_column('price_per_additional_hour')
        batch_op.drop_column('price_first_2_hours') 