from sqlalchemy import select

from app.core.celery_con import celery_app
from app.core.storage import get_media_root
from app.db.sync_database import SessionLocal
from app.feature.course.models import Lesson, UploadStatusType


def _load_current(session, lesson_id: int, upload_id: str) -> Lesson | None:
    lesson = session.scalar(select(Lesson).where(Lesson.id == lesson_id))
    if lesson is None or lesson.upload_id != upload_id:
        return None
    return lesson


@celery_app.task
def finalize_lesson_upload(lesson_id: int, upload_id: str):
    with SessionLocal() as session:
        lesson = _load_current(session, lesson_id, upload_id)
        if lesson is None:
            return

        lesson.upload_status = UploadStatusType.PROCESSING
        session.commit()

        try:
            path = get_media_root() / lesson.file_url
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError("Uploaded file is missing or empty")
        except Exception as e:
            lesson = _load_current(session, lesson_id, upload_id)
            if lesson is None:
                return
            lesson.upload_status = UploadStatusType.FAILED
            lesson.upload_failure_reason = str(e)
            session.commit()
            return

        lesson = _load_current(session, lesson_id, upload_id)
        if lesson is None:
            return
        lesson.upload_status = UploadStatusType.READY
        session.commit()
