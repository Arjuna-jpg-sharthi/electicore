"""Add student doubt discussions and optional voice recordings."""

from alembic import op
import sqlalchemy as sa


revision = "e20c49ad1251"
down_revision = "7ea2c0d91b45"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "doubt_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("audio_filename", sa.String(length=100), nullable=True),
        sa.Column("audio_mime_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["doubt_posts.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("doubt_posts") as batch_op:
        batch_op.create_index(batch_op.f("ix_doubt_posts_parent_id"), ["parent_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_doubt_posts_student_id"), ["student_id"], unique=False)


def downgrade():
    with op.batch_alter_table("doubt_posts") as batch_op:
        batch_op.drop_index(batch_op.f("ix_doubt_posts_student_id"))
        batch_op.drop_index(batch_op.f("ix_doubt_posts_parent_id"))
    op.drop_table("doubt_posts")
