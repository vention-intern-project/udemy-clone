import enum
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.feature.user.models import User


class LessonType(enum.StrEnum):
    VIDEO = "video"
    TEXT = "text"
    PDF = "pdf"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    instructor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0,
        server_default=text("0"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="UZS",
        server_default=text("'UZS'"),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    instructor: Mapped["User"] = relationship()

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    lesson_type: Mapped[LessonType] = mapped_column(
        Enum(LessonType, name="lessontype"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    course: Mapped["Course"] = relationship(back_populates="lessons")
    assets: Mapped[list["LessonAsset"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LessonAsset.version",
    )

    @property
    def latest_asset(self) -> "LessonAsset | None":
        return self.assets[-1] if self.assets else None

    @property
    def _latest_subtitle_job(self) -> "ProcessingJob | None":
        asset = self.latest_asset
        if asset is None:
            return None
        return next((job for job in asset.jobs if job.job_type == "subtitle"), None)

    @property
    def download_url(self) -> str | None:
        asset = self.latest_asset
        if asset is None:
            return None
        return f"/media/lessons/{Path(asset.storage_key).name}"

    @property
    def subtitle_status(self) -> bool:
        job = self._latest_subtitle_job
        return job is not None and job.status == "completed"

    @property
    def subtitles_path(self) -> str | None:
        job = self._latest_subtitle_job
        return job.result_path if job else None

    @property
    def transcript_path(self) -> str | None:
        job = self._latest_subtitle_job
        return job.transcript_path if job else None


class LessonAsset(Base):
    __tablename__ = "lesson_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    upload_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    lesson: Mapped["Lesson"] = relationship(back_populates="assets")
    jobs: Mapped[list["ProcessingJob"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("lesson_id", "version", name="uq_lesson_asset_version"),
    )


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("lesson_assets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_path: Mapped[str | None] = mapped_column(nullable=True)
    transcript_path: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    asset: Mapped["LessonAsset"] = relationship(back_populates="jobs")
