"""Signals and stand-in transcribers for the tests.

The benchmark has no transcriber of its own, so the tests bring their own: a
tone generator to make audio with known notes, and fake systems whose errors
are chosen rather than measured. That is the right way round -- a test of a
scoring rule should state the error it expects the score to reflect, not
discover it by running a model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

SAMPLE_RATE = 16000
Note = Tuple[float, float, float]


def render(notes: Sequence[Note], sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """A sung-ish signal: a fundamental with a few harmonics, softly enveloped.

    Enough for pitch tracking to have something to track, and for onsets to be
    where the annotation says they are.
    """
    duration = max(end for _, end, _ in notes) + 0.2
    audio = np.zeros(int(duration * sample_rate), dtype=np.float64)
    for start, end, pitch in notes:
        a, b = int(start * sample_rate), int(end * sample_rate)
        if b <= a:
            continue
        t = np.arange(b - a) / sample_rate
        frequency = 440.0 * 2 ** ((pitch - 69) / 12)
        tone = sum(np.sin(2 * np.pi * frequency * h * t) / h for h in (1, 2, 3))
        # A short fade at each end, so an onset detector sees an onset and the
        # boundary is not a click that every detector would find.
        fade = min(int(0.01 * sample_rate), (b - a) // 2)
        if fade:
            tone[:fade] *= np.linspace(0.0, 1.0, fade)
            tone[-fade:] *= np.linspace(1.0, 0.0, fade)
        audio[a:b] += tone
    peak = np.max(np.abs(audio))
    return (audio / peak * 0.7) if peak else audio


def case_scale(start_pitch: int = 60, n: int = 8) -> Tuple[np.ndarray, List[Note]]:
    """Separated notes walking up a scale: the easy case, deliberately."""
    steps = [0, 2, 4, 5, 7, 9, 11, 12]
    notes = [(0.2 + i * 0.5, 0.2 + i * 0.5 + 0.4, float(start_pitch + steps[i % 8]))
             for i in range(n)]
    return render(notes), notes


def case_legato() -> Tuple[np.ndarray, List[Note]]:
    """Notes that touch, so the only cue to a boundary is the pitch change."""
    notes = []
    start = 0.2
    for pitch in (62, 64, 65, 67, 65, 64):
        notes.append((start, start + 0.45, float(pitch)))
        start += 0.45
    return render(notes), notes


def write_case(directory: Path, name: str, notes: Sequence[Note],
               audio: np.ndarray | None = None) -> None:
    """Write one recording and its reference annotation, the way a corpus ships."""
    import soundfile as sf

    directory.mkdir(parents=True, exist_ok=True)
    sf.write(directory / f"{name}.wav", render(notes) if audio is None else audio,
             SAMPLE_RATE)
    rows = ["onset,offset,pitch"]
    rows += [f"{a:.6f},{b:.6f},{p}" for a, b, p in notes]
    (directory / f"{name}.csv").write_text("\n".join(rows) + "\n")


class FakeTranscriber:
    """A transcriber whose errors are stated rather than measured.

    Returns the notes it was told to return for each recording, so an
    end-to-end test can assert an exact score instead of a threshold.
    """

    name = "fake"

    def __init__(self, by_stem: Dict[str, Sequence[Note]], **settings) -> None:
        self._by_stem = {k: list(v) for k, v in by_stem.items()}
        self._settings = settings
        self.calls: List[Path] = []

    def transcribe(self, audio: Path) -> List[Note]:
        self.calls.append(Path(audio))
        return list(self._by_stem.get(Path(audio).stem, []))

    def settings(self) -> Dict[str, object]:
        """What the benchmark records as provenance, and keys its cache on."""
        return dict(self._settings)
