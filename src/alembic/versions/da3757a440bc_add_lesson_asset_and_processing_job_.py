"""add lesson asset and processing job tables

Revision ID: da3757a440bc
Revises: a898a00fcca2
Create Date: 2026-08-19 13:36:19.925532

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da3757a440bc"
down_revision: str | Sequence[str] | None = "a898a00fcca2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lesson_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_id", "version", name="uq_lesson_asset_version"),
    )
    op.create_index(op.f("ix_lesson_assets_id"), "lesson_assets", ["id"], unique=False)
    op.create_index(
        op.f("ix_lesson_assets_lesson_id"), "lesson_assets", ["lesson_id"], unique=False
    )
    op.create_index(
        op.f("ix_lesson_assets_upload_id"), "lesson_assets", ["upload_id"], unique=True
    )

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("job_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("result_path", sa.String(), nullable=True),
        sa.Column("transcript_path", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["lesson_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_processing_jobs_id"), "processing_jobs", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_processing_jobs_asset_id"),
        "processing_jobs",
        ["asset_id"],
        unique=False,
    )

    # Backfill: one LessonAsset (version 1) + up to two ProcessingJob rows per
    # existing lesson that already has an uploaded file.
    connection = op.get_bind()
    lessons = connection.execute(
        sa.text(
            """
            SELECT id, file_url, upload_id, upload_status, upload_failure_reason,
                   subtitle_status, subtitles_path, transcript_path, updated_at
            FROM lessons
            WHERE file_url IS NOT NULL
            """
        )
    ).fetchall()

    for lesson in lessons:
        upload_id = lesson.upload_id or lesson.id.__str__().zfill(32)[-32:]
        asset_id = connection.execute(
            sa.text(
                """
                INSERT INTO lesson_assets
                    (lesson_id, upload_id, version, storage_key, checksum,
                     content_type, size, created_at)
                VALUES
                    (:lesson_id, :upload_id, 1, :storage_key, '',
                     'application/octet-stream', 0, :created_at)
                RETURNING id
                """
            ),
            {
                "lesson_id": lesson.id,
                "upload_id": upload_id,
                "storage_key": lesson.file_url,
                "created_at": lesson.updated_at,
            },
        ).scalar_one()

        if lesson.upload_status is not None:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO processing_jobs
                        (asset_id, job_type, status, failure_reason,
                         created_at, updated_at)
                    VALUES
                        (:asset_id, 'finalize', :status, :failure_reason, :ts, :ts)
                    """
                ),
                {
                    "asset_id": asset_id,
                    "status": lesson.upload_status.lower(),
                    "failure_reason": lesson.upload_failure_reason,
                    "ts": lesson.updated_at,
                },
            )

        if lesson.subtitle_status is not None:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO processing_jobs
                        (asset_id, job_type, status, result_path,
                         transcript_path, created_at, updated_at)
                    VALUES
                        (:asset_id, 'subtitle', :status, :result_path,
                         :transcript_path, :ts, :ts)
                    """
                ),
                {
                    "asset_id": asset_id,
                    "status": lesson.subtitle_status.lower(),
                    "result_path": lesson.subtitles_path,
                    "transcript_path": lesson.transcript_path,
                    "ts": lesson.updated_at,
                },
            )

    op.drop_index(op.f("ix_lessons_upload_id"), table_name="lessons")
    op.drop_column("lessons", "file_url")
    op.drop_column("lessons", "subtitle_status")
    op.drop_column("lessons", "subtitles_path")
    op.drop_column("lessons", "transcript_path")
    op.drop_column("lessons", "upload_id")
    op.drop_column("lessons", "upload_status")
    op.drop_column("lessons", "upload_failure_reason")

    subtitle_status_enum = sa.Enum(name="subtitlestatustype")
    upload_status_enum = sa.Enum(name="uploadstatustype")
    subtitle_status_enum.drop(op.get_bind(), checkfirst=True)
    upload_status_enum.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    subtitle_status_enum = sa.dialects.postgresql.ENUM(
        "PENDING", "PROCESSING", "COMPLETED", "FAILED", name="subtitlestatustype"
    )
    upload_status_enum = sa.dialects.postgresql.ENUM(
        "QUEUED", "PROCESSING", "READY", "FAILED", name="uploadstatustype"
    )
    subtitle_status_enum.create(op.get_bind(), checkfirst=True)
    upload_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "lessons", sa.Column("file_url", sa.String(length=512), nullable=True)
    )
    op.add_column(
        "lessons",
        sa.Column(
            "subtitle_status",
            subtitle_status_enum,
            nullable=False,
            server_default="PENDING",
        ),
    )
    op.add_column("lessons", sa.Column("subtitles_path", sa.String(), nullable=True))
    op.add_column("lessons", sa.Column("transcript_path", sa.String(), nullable=True))
    op.add_column(
        "lessons", sa.Column("upload_id", sa.String(length=32), nullable=True)
    )
    op.add_column(
        "lessons", sa.Column("upload_status", upload_status_enum, nullable=True)
    )
    op.add_column(
        "lessons",
        sa.Column("upload_failure_reason", sa.String(length=255), nullable=True),
    )
    op.create_index(op.f("ix_lessons_upload_id"), "lessons", ["upload_id"], unique=True)

    # Data is not restored on downgrade — this is a lossy rollback for the
    # asset/job history; the most recent LessonAsset per lesson could be
    # written back to lessons.file_url here if that's required operationally.

    op.drop_table("processing_jobs")
    op.drop_table("lesson_assets")
