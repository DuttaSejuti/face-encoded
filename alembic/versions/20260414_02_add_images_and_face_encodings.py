"""add images and face encodings

Revision ID: 20260414_02
Revises: 20260414_01
Create Date: 2026-04-14 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260414_02"
down_revision: Union[str, None] = "20260414_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_images_session_id", "images", ["session_id"])

    op.create_table(
        "face_encodings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vector", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["image_id"], ["images.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_face_encodings_image_id", "face_encodings", ["image_id"])


def downgrade() -> None:
    op.drop_index("ix_face_encodings_image_id", table_name="face_encodings")
    op.drop_table("face_encodings")
    op.drop_index("ix_images_session_id", table_name="images")
    op.drop_table("images")
