"""How a transcription system is supplied to the benchmark.

There are two ways, and the first is the one to reach for.

**A directory of transcriptions.** Run the system however it wants to be run,
and point the benchmark at what it wrote. Any system that emits MIDI or CSV
works, with no adapter, no import, and no agreement about interfaces -- which
is why it was possible to score ROSVOT without ROSVOT knowing this existed.
Basic Pitch, VOCANO and anything else that writes a file are the same.

**An adapter.** A system that can be called in process registers one, and the
benchmark can then run it itself, cache what it produced, and sweep parameters
without re-running the expensive parts. That is worth having for a system you
are developing; it is not worth demanding from a system you are merely
measuring.

Adapters are found through the ``transcription_benchmarking.transcribers``
entry point group, so this package never imports a transcriber and does not
know which exist. A transcriber that is not installed is simply not offered.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Protocol, Sequence, Tuple, runtime_checkable

# (onset seconds, offset seconds, MIDI pitch). Pitch is a float so a system
# that does not quantise is not forced to.
Note = Tuple[float, float, float]

ENTRY_POINT_GROUP = "transcription_benchmarking.transcribers"


@runtime_checkable
class Transcriber(Protocol):
    """Anything that turns an audio file into notes."""

    def transcribe(self, audio: Path) -> Sequence[Note]:
        ...


def available() -> Dict[str, Callable[[], Transcriber]]:
    """Installed adapters, by name, each a factory that builds one.

    Read at call time rather than at import, so installing a transcriber into a
    live environment is enough to make it available. Nothing is imported here:
    the factory does that when it is called, so one broken adapter cannot stop
    the others from being listed.
    """
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover - Python 3.7 and older
        return {}

    found: Dict[str, Callable[[], Transcriber]] = {}
    try:
        points = entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:  # pragma: no cover - the pre-3.10 signature
        points = entry_points().get(ENTRY_POINT_GROUP, [])
    for point in points:
        found[point.name] = _factory(point)
    return found


def _factory(point) -> Callable[[], Transcriber]:
    """Turn an entry point into something that returns a *usable* transcriber.

    An entry point resolves to whatever the adapter package named, and all
    three plausible things are accepted: a class to instantiate, a function
    that builds one, or an object that is already a transcriber. Getting this
    wrong hands the runner a class, whose ``transcribe`` is unbound, and the
    failure then surfaces somewhere it cannot be explained.
    """
    def build() -> Transcriber:
        target = point.load()
        if isinstance(target, type):
            return target()
        if callable(target) and not callable(getattr(target, "transcribe", None)):
            return target()
        return target

    return build


def load(name: str) -> Transcriber:
    """Instantiate one adapter by name, or say what there was instead."""
    adapters = available()
    if name not in adapters:
        offered = ", ".join(sorted(adapters)) or "none installed"
        raise LookupError(
            f"no transcriber named {name!r}; available: {offered}. "
            "A directory of transcriptions needs no adapter -- score it with "
            "--estimates instead.")
    transcriber = adapters[name]()
    if not callable(getattr(transcriber, "transcribe", None)):
        raise TypeError(
            f"the {name!r} adapter resolved to {transcriber!r}, which provides no "
            "transcribe(audio) -> notes")
    return transcriber


class NotesFromFiles:
    """The file-based path, as a transcriber.

    So the runner has one thing to call whether the notes came from a directory
    or from an adapter, rather than a branch at every use.
    """

    name = "external"

    def __init__(self, by_item: Dict[str, Path]) -> None:
        self._by_item = by_item

    def settings(self) -> Dict[str, object]:
        """Nothing to record: the notes were fixed before the benchmark saw them."""
        return {}

    def for_item(self, item_id: str) -> List[Note]:
        from .annotations import load_annotation

        path = self._by_item.get(item_id)
        if path is None:
            return []
        return [(start, end, pitch)
                for start, end, pitch in load_annotation(path).notes]
