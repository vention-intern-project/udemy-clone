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
    file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
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

    @property
    def download_url(self) -> str | None:
        if not self.file_url:
            return None
        return f"/media/lessons/{Path(self.file_url).name}"
