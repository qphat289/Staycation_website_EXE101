"""Add is_active column to homestay table

Revision ID: add_is_active_to_homestay
Revises: 
Create Date: 2023-03-27 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_active_to_homestay'
down_revision = None  # Thay đổi giá trị này theo phiên bản migration cuối cùng của bạn
branch_labels = None
depends_on = None


def upgrade():
    # Thêm cột is_active vào bảng homestay với giá trị mặc định là True
    op.add_column('homestay', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='TRUE'))


def downgrade():
    # Xóa cột is_active khỏi bảng homestay khi cần downgrade
    op.drop_column('homestay', 'is_active') 