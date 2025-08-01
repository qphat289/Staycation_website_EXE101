"""initial migration

Revision ID: deb62770d2cb
Revises: 
Create Date: 2025-06-08 20:45:31.337695

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'deb62770d2cb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('renter', schema=None) as batch_op:
        batch_op.add_column(sa.Column('google_id', sa.String(length=100), nullable=True))
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=80),
               nullable=True)
        batch_op.create_unique_constraint('uq_renter_google_id', ['google_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('renter', schema=None) as batch_op:
        batch_op.drop_constraint('uq_renter_google_id', type_='unique')
        batch_op.alter_column('username',
               existing_type=sa.VARCHAR(length=80),
               nullable=False)
        batch_op.drop_column('google_id')
    # ### end Alembic commands ###
