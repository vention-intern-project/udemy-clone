import asyncio

from app.core.celery_con import celery_app

from sqlalchemy import select

from app.db.database import get_db

from app.feature.course.models import Lesson

from app.feature.subtitle.service import SubtitleService


async def generate_subtitles_async(
    lesson_id: str,
):

    async with get_db() as session:

        lesson = await session.scalar(
            select(Lesson).where(
                Lesson.id == lesson_id
            )
        )

        if lesson is None:
            return

        lesson.subtitle_status = "processing"

        await session.commit()

        try:

            service = SubtitleService()

            result = service.generate(
                lesson.video_path
            )

            lesson.subtitle_status = "completed"

            lesson.subtitle_path = result.vtt_path

            lesson.transcript_path = result.transcript_path

            await session.commit()

        except Exception:

            lesson.subtitle_status = "failed"

            await session.commit()

            raise


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_subtitles(lesson_id: str):

    asyncio.run(
        generate_subtitles_async(lesson_id)
    )