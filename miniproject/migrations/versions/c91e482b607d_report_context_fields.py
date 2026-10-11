"""Persist the report fields collected by the safety form.

Revision ID: c91e482b607d
Revises: a82d5c19e341
Create Date: 2026-10-03
"""
from alembic import op
import sqlalchemy as sa


revision = "c91e482b607d"
down_revision = "a82d5c19e341"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("safety_reports") as batch_op:
        batch_op.add_column(sa.Column("incident_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("incident_time", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("people_involved", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("additional_details", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("safety_reports") as batch_op:
        batch_op.drop_column("additional_details")
        batch_op.drop_column("people_involved")
        batch_op.drop_column("incident_time")
        batch_op.drop_column("incident_date")
