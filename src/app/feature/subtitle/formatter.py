from pathlib import Path


def srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60

    return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")


def vtt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60

    return f"{h:02}:{m:02}:{s:06.3f}"


def create_output_paths(video_path: str):

    video = Path(video_path)

    return (
        video.with_suffix(".txt"),
        video.with_suffix(".vtt"),
        video.with_suffix(".srt"),
    )