from tests.api.factories import LessonAssetFactory, LessonFactory, ProcessingJobFactory


def test_download_url_none_when_no_assets():
    lesson = LessonFactory()

    assert lesson.download_url is None


def test_subtitle_status_false_when_no_assets():
    lesson = LessonFactory()

    assert lesson.subtitle_status is False
    assert lesson.subtitles_path is None
    assert lesson.transcript_path is None


def test_subtitle_status_true_when_latest_subtitle_job_completed():
    lesson = LessonFactory()
    asset = LessonAssetFactory(
        lesson=lesson, version=1, storage_key="lessons/video/abc123.mp4"
    )
    ProcessingJobFactory(
        asset=asset,
        job_type="subtitle",
        status="completed",
        result_path="lessons/video/abc123.vtt",
        transcript_path="lessons/video/abc123.txt",
    )

    assert lesson.subtitle_status is True
    assert lesson.subtitles_path == "lessons/video/abc123.vtt"
    assert lesson.transcript_path == "lessons/video/abc123.txt"
    assert lesson.download_url == "/media/lessons/abc123.mp4"


def test_subtitle_status_false_when_job_not_completed():
    lesson = LessonFactory()
    asset = LessonAssetFactory(lesson=lesson, version=1)
    ProcessingJobFactory(asset=asset, job_type="subtitle", status="processing")

    assert lesson.subtitle_status is False


def test_resolver_properties_use_latest_version_asset():
    lesson = LessonFactory()
    LessonAssetFactory(lesson=lesson, version=1, storage_key="lessons/video/old.mp4")
    newest = LessonAssetFactory(
        lesson=lesson, version=2, storage_key="lessons/video/new.mp4"
    )
    ProcessingJobFactory(
        asset=newest, job_type="subtitle", status="completed", result_path="new.vtt"
    )

    assert lesson.download_url == "/media/lessons/new.mp4"
    assert lesson.subtitles_path == "new.vtt"
