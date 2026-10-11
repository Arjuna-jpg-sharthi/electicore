"""Record and respect consent for AI-assisted safety report drafting.

Revision ID: 31bc682ef504
Revises: c91e482b607d
Create Date: 2026-10-03
"""
from alembic import op
import sqlalchemy as sa


revision = "31bc682ef504"
down_revision = "c91e482b607d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("safety_reports") as batch_op:
        batch_op.add_column(sa.Column("ai_drafting_consent", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("safety_reports") as batch_op:
        batch_op.drop_column("ai_drafting_consent")
