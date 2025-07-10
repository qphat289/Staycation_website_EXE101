"""Merge heads

Revision ID: 0b9cdf6d327e
Revises: add_accommodation_type, add_email_verification_to_owner
Create Date: 2025-07-10 19:10:32.781310

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b9cdf6d327e'
down_revision = ('add_accommodation_type', 'add_email_verification_to_owner')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
