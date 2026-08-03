from dataclasses import dataclass


@dataclass(slots=True)
class SubtitleResult:
    transcript_path: str
    vtt_path: str
    srt_path: str
