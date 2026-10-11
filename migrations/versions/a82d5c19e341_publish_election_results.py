"""Add explicit election result publication state.

Revision ID: a82d5c19e341
Revises: f97cd17f0a4c
Create Date: 2026-10-03
"""
from alembic import op
import sqlalchemy as sa


revision = "a82d5c19e341"
down_revision = "f97cd17f0a4c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("elections") as batch_op:
        batch_op.add_column(sa.Column("results_published", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.alter_column("results_published", server_default=None)


def downgrade():
    with op.batch_alter_table("elections") as batch_op:
        batch_op.drop_column("results_published")
