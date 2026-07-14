from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)

    course_id: Mapped[int] = mapped_column(ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    rating: Mapped[float] = mapped_column(nullable=False)

    comment: Mapped[str] = mapped_column(default='')

    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now())


    __table_args__ = (UniqueConstraint('course_id', 'user_id', name='uniq_course_student_review'),)