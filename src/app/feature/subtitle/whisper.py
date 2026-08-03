from functools import lru_cache

from faster_whisper import WhisperModel


@lru_cache(maxsize=1)
def get_model() -> WhisperModel:
    return WhisperModel(
        "base",
        device="cpu",
        compute_type="int8",
    )
