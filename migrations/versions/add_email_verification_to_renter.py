"""add email verification to renter

Revision ID: add_email_verification_to_renter
Revises: add_payment_tables
Create Date: 2025-07-11 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_email_verification_to_renter'
down_revision = 'add_payment_tables'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('renter', sa.Column('email_verified', sa.Boolean(), nullable=True, default=False))
    op.add_column('renter', sa.Column('first_login', sa.Boolean(), nullable=True, default=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('renter', 'first_login')
    op.drop_column('renter', 'email_verified')
    # ### end Alembic commands ### 