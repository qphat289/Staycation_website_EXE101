"""Add accommodation_type to home table

Revision ID: add_accommodation_type
Revises: 89f02cf4884e
Create Date: 2024-12-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_accommodation_type'
down_revision = '89f02cf4884e'
branch_labels = None
depends_on = None

def upgrade():
    # Add accommodation_type column to home table
    op.add_column('home', sa.Column('accommodation_type', sa.String(50), nullable=False, server_default='entire_home'))

def downgrade():
    # Remove accommodation_type column from home table
    op.drop_column('home', 'accommodation_type') 