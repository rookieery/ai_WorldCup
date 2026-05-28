"""Add Chinese translation columns to venues table

Revision ID: 002
Revises: 001
Create Date: 2026-05-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("venues", sa.Column("name_zh", sa.String(length=150), nullable=False, server_default=""))
    op.add_column("venues", sa.Column("city_zh", sa.String(length=100), nullable=False, server_default=""))
    op.add_column("venues", sa.Column("country_zh", sa.String(length=100), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("venues", "country_zh")
    op.drop_column("venues", "city_zh")
    op.drop_column("venues", "name_zh")
