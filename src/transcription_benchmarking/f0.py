"""A pitch contour for aligning references, owned by the benchmark.

Alignment needs to know roughly where the melody goes in the recording. Asking
the system under test for that would be a mistake: a reference warped onto one
system's pitch track is a reference shaped by that system, and every other
system would then be scored against its competitor's idea of the tune.

So the benchmark estimates its own, with pYIN, and uses the same one for
everybody. It is slower than a neural tracker and it does not need to be
better -- it only has to be neutral, and the same for all.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

SAMPLE_RATE = 16000
HOP_LENGTH = 160          # 10 ms
FMIN_HZ = 55.0
FMAX_HZ = 1600.0


def estimate(audio_path: Path, cache_dir: Optional[Path] = None
             ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (f0 in Hz, voicing probability, frame times) for one recording."""
    if cache_dir is not None:
        cached = _cache_path(cache_dir, audio_path)
        if cached.exists():
            with np.load(cached) as data:
                return data["f0"], data["voicing"], data["times"]

    import librosa

    audio, _ = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
    f0, _voiced, voicing = librosa.pyin(
        audio, fmin=FMIN_HZ, fmax=FMAX_HZ, sr=SAMPLE_RATE,
        hop_length=HOP_LENGTH, fill_na=np.nan)
    f0 = np.nan_to_num(f0, nan=0.0)
    voicing = np.nan_to_num(voicing, nan=0.0)
    times = librosa.frames_to_time(np.arange(f0.shape[0]), sr=SAMPLE_RATE,
                                   hop_length=HOP_LENGTH)

    if cache_dir is not None:
        cached = _cache_path(cache_dir, audio_path)
        cached.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cached, f0=f0, voicing=voicing, times=times)
    return f0, voicing, times


def _cache_path(cache_dir: Path, audio_path: Path) -> Path:
    """Named after the recording, not after whatever produced its notes."""
    digest = hashlib.sha1(str(audio_path.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(cache_dir) / f"{audio_path.stem[:60]}_{digest}.npz"
