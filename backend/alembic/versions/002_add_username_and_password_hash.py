"""Add username and password_hash columns to users table

迁移 ID: 002
说明: 为密码认证添加 username (唯一) 和 password_hash 字段
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002_add_username_and_password_hash"
down_revision: Union[str, None] = "001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(128), nullable=True, unique=True))
    op.add_column("users", sa.Column("password_hash", sa.String(256), nullable=True))
    op.create_index("idx_users_username", "users", ["username"])


def downgrade() -> None:
    op.drop_index("idx_users_username", table_name="users")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "username")
