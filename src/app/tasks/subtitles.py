import asyncio

import os

from app.core.celery_con import celery_app

from sqlalchemy import select

from app.db.database import SessionLocal

from app.feature.course.models import Lesson

from app.feature.subtitle.service import SubtitleService

from app.core.storage import get_media_root


async def generate_subtitles_async(
    lesson_id: int,
):

    async with SessionLocal() as session:

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

            video_path = get_media_root() / lesson.file_url

            result = service.generate(
                str(video_path)
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
    bind=True
)
def generate_subtitles(self, lesson_id: int):
    print("generating subtitles")
    asyncio.run(
        generate_subtitles_async(lesson_id)
    )
    print("generated subtitles")