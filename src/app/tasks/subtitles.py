from app.core.celery_con import celery_app

from sqlalchemy import select

from app.db.sync_database import SessionLocal

from app.feature.course.models import Lesson

from app.feature.subtitle.service import SubtitleService

from app.core.storage import get_media_root

def delete_if_exists(path: str | None):
    if not path:
        return

    file = get_media_root() / path
    file.unlink(missing_ok=True)


@celery_app.task
def generate_subtitles(lesson_id: int):
    with SessionLocal() as session:
        lesson = session.scalar(
            select(Lesson).where(Lesson.id == lesson_id)
        )

        if lesson is None:
            return

        lesson.subtitle_status = "processing"
        session.commit()

        try:
            service = SubtitleService()

            video_path = get_media_root() / lesson.file_url
            delete_if_exists(lesson.subtitles_path)
            delete_if_exists(lesson.subtitles_path.replace(".vtt", ".srt"))
            delete_if_exists(lesson.transcript_path)

            result = service.generate(
                str(video_path),
                media_root=get_media_root(),
            )

            lesson.subtitle_status = "completed"
            lesson.subtitles_path = result.vtt_path
            lesson.transcript_path = result.transcript_path
            session.commit()

        except Exception:
            lesson.subtitle_status = "failed"
            session.commit()
            raise