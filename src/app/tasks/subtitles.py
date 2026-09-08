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
    ingest_args = None

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

            # eagerly read everything the ingest needs while the session is
            # still live; the ingest itself must run after the session closes
            # (see below) so the pooled connection isn't held across the LLM call
            lesson = asset.lesson
            ingest_args = (
                lesson.course_id,
                lesson.id,
                lesson.title,
                lesson.course.title,
                result.transcript_path,
            )

        except Exception as e:
            job.status = "failed"
            job.failure_reason = str(e)
            session.commit()
            raise

    # ponytail: last-writer-wins; whisper's minutes make placeholder-first the
    # normal order. Add a timestamp guard in _persist_lesson if a short video
    # ever loses its transcript.
    if ingest_args is not None:
        course_id, lesson_id, lesson_title, course_title, transcript_path = ingest_args
        try:
            transcript = (get_media_root() / transcript_path).read_text(
                encoding="utf-8"
            )
            asyncio.run(
                ingest_lesson_text(
                    course_id,
                    lesson_id,
                    lesson_title,
                    course_title,
                    transcript,
                )
            )
            logger.info(
                "knowledge ingest succeeded for job %s lesson %s",
                job_id,
                lesson_id,
            )
        except Exception:
            logger.exception(
                "knowledge ingest failed for job %s lesson %s transcript %s",
                job_id,
                lesson_id,
                transcript_path,
            )
