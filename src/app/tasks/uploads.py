from app.core.celery_con import celery_app
from app.core.storage import get_media_root
from app.db.sync_database import SessionLocal
from app.feature.course.models import ProcessingJob


@celery_app.task
def finalize_lesson_upload(job_id: int):
    with SessionLocal() as session:
        job = session.get(ProcessingJob, job_id)
        if job is None or job.job_type != "finalize":
            return

        asset = job.asset

        job.status = "processing"
        session.commit()

        try:
            path = get_media_root() / asset.storage_key
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError("Uploaded file is missing or empty")
        except Exception as e:
            job.status = "failed"
            job.failure_reason = str(e)
            session.commit()
            return

        job.status = "completed"
        session.commit()
