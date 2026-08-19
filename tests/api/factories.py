import uuid
from datetime import UTC, datetime
from decimal import Decimal

import factory

from app.feature.course.models import (
    Course,
    Lesson,
    LessonAsset,
    LessonType,
    ProcessingJob,
)
from app.feature.enrollment.models import Enrollment, EnrollmentStatus
from app.feature.user.models import User, UserRole


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    email = factory.LazyAttribute(lambda o: f"{o.name.lower()}@example.com")
    name = "Jane"
    surname = "Doe"
    password = "hashed_password"
    role = UserRole.INSTRUCTOR
    created_at = datetime(2026, 1, 1, tzinfo=UTC)


class CourseFactory(factory.Factory):
    class Meta:
        model = Course

    id = factory.Sequence(lambda n: n + 1)
    instructor = factory.SubFactory(UserFactory)
    instructor_id = factory.LazyAttribute(lambda o: o.instructor.id)
    title = "Python 101"
    description = "Intro to Python"
    price = Decimal("9.99")
    currency = "USD"
    published_at = None
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    updated_at = datetime(2026, 1, 1, tzinfo=UTC)


class LessonFactory(factory.Factory):
    class Meta:
        model = Lesson

    id = factory.Sequence(lambda n: n + 1)
    course = factory.SubFactory(CourseFactory)
    course_id = factory.LazyAttribute(lambda o: o.course.id)
    title = "Lesson 1"
    lesson_type = LessonType.VIDEO
    description = None
    is_published = True
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    updated_at = datetime(2026, 1, 1, tzinfo=UTC)


class LessonAssetFactory(factory.Factory):
    class Meta:
        model = LessonAsset

    id = factory.Sequence(lambda n: n + 1)
    lesson = factory.SubFactory(LessonFactory)
    lesson_id = factory.LazyAttribute(lambda o: o.lesson.id)
    upload_id = factory.LazyFunction(lambda: uuid.uuid4().hex)
    version = 1
    storage_key = "lessons/video/abc123.mp4"
    checksum = "deadbeef"
    content_type = "video/mp4"
    size = 1024
    created_at = datetime(2026, 1, 1, tzinfo=UTC)


class ProcessingJobFactory(factory.Factory):
    class Meta:
        model = ProcessingJob

    id = factory.Sequence(lambda n: n + 1)
    asset = factory.SubFactory(LessonAssetFactory)
    asset_id = factory.LazyAttribute(lambda o: o.asset.id)
    job_type = "subtitle"
    status = "queued"
    failure_reason = None
    result_path = None
    transcript_path = None
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    updated_at = datetime(2026, 1, 1, tzinfo=UTC)


class EnrollmentFactory(factory.Factory):
    class Meta:
        model = Enrollment

    id = factory.Sequence(lambda n: n + 1)
    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda o: o.user.id)
    course = factory.SubFactory(CourseFactory)
    course_id = factory.LazyAttribute(lambda o: o.course.id)
    status = EnrollmentStatus.ACTIVE
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    updated_at = datetime(2026, 1, 1, tzinfo=UTC)
