import asyncio
import logging

from app.core.celery_con import celery_app
from app.core.storage import get_media_root
from app.db.sync_database import SessionLocal
from app.feature.course.models import ProcessingJob
from app.feature.knowledge.service import ingest_lesson_text
from app.feature.subtitle.service import SubtitleService

logger = logging.getLogger(__name__)


@celery_app.task
def generate_subtitles(job_id: int):
    with SessionLocal() as session:
        job = session.get(ProcessingJob, job_id)

        if job is None or job.job_type != "subtitle":
            return

        asset = job.asset

        job.status = "processing"
        session.commit()

        try:
            service = SubtitleService()
            video_path = get_media_root() / asset.storage_key

            result = service.generate(
                str(video_path),
                media_root=get_media_root(),
            )

            job.status = "completed"
            job.result_path = result.vtt_path
            job.transcript_path = result.transcript_path
            session.commit()

            try:
                lesson = asset.lesson
                transcript = (get_media_root() / result.transcript_path).read_text(
                    encoding="utf-8"
                )
                asyncio.run(
                    ingest_lesson_text(
                        lesson.course_id,
                        lesson.id,
                        lesson.title,
                        lesson.course.title,
                        transcript,
                    )
                )
            except Exception:
                logger.exception(
                    "knowledge ingest failed for lesson %s", asset.lesson_id
                )

        except Exception as e:
            job.status = "failed"
            job.failure_reason = str(e)
            session.commit()
            raise
