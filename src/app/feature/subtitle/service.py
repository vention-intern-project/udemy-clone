from pathlib import Path

from app.feature.subtitle.formatter import (
    create_output_paths,
    srt_timestamp,
    vtt_timestamp,
)

from app.feature.subtitle.schemas import SubtitleResult
from app.feature.subtitle.whisper import get_model


class SubtitleService:

    def generate(
        self,
        video_path: str,
        media_root,
    ) -> SubtitleResult:

        model = get_model()

        segments, info = model.transcribe(
            video_path,
            beam_size=5,
            vad_filter=True,
        )

        txt_path, vtt_path, srt_path = create_output_paths(video_path)

        transcript = []

        with (
            open(txt_path, "w", encoding="utf8") as txt,
            open(vtt_path, "w", encoding="utf8") as vtt,
            open(srt_path, "w", encoding="utf8") as srt,
        ):

            vtt.write("WEBVTT\n\n")

            for index, segment in enumerate(segments, start=1):

                text = segment.text.strip()

                transcript.append(text)

                txt.write(text + "\n")

                srt.write(f"{index}\n")
                srt.write(
                    f"{srt_timestamp(segment.start)} --> "
                    f"{srt_timestamp(segment.end)}\n"
                )
                srt.write(text)
                srt.write("\n\n")

                vtt.write(
                    f"{vtt_timestamp(segment.start)} --> "
                    f"{vtt_timestamp(segment.end)}\n"
                )
                vtt.write(text)
                vtt.write("\n\n")

        return SubtitleResult(
            transcript_path=str(txt_path.relative_to(media_root)),
            vtt_path=str(vtt_path.relative_to(media_root)),
            srt_path=str(srt_path.relative_to(media_root)),
        )