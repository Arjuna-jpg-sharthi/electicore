"""Store an optional AI safety report urgency estimate.

Revision ID: 7ea2c0d91b45
Revises: 31bc682ef504
Create Date: 2026-10-11
"""
from alembic import op
import sqlalchemy as sa


revision = "7ea2c0d91b45"
down_revision = "31bc682ef504"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("safety_reports") as batch_op:
        batch_op.add_column(sa.Column("ai_severity", sa.String(length=20), nullable=False,
                                      server_default="unassessed"))
        batch_op.add_column(sa.Column("ai_assessment_note", sa.String(length=500), nullable=True))


def downgrade():
    with op.batch_alter_table("safety_reports") as batch_op:
        batch_op.drop_column("ai_assessment_note")
        batch_op.drop_column("ai_severity")
