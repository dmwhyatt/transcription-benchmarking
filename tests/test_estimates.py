"""Pairing a system's transcriptions back to the recordings they came from.

The failure this guards against does not look like a failure. Where a corpus
numbers its segments inside a folder per song -- M4Singer names 20,896 of them
0000.wav, 0001.wav and so on -- pairing on the bare stem hands every song the
first song's transcription. Every item pairs, nothing errors, and the score
describes one recording copied 700 times.
"""

from pathlib import Path

import pretty_midi

from transcription_benchmarking.dataset import Item, pair_estimates


def write_midi(path: Path, pitch: int) -> Path:
    """A one-note MIDI file, its pitch identifying which file it is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    score = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=53)
    instrument.notes.append(
        pretty_midi.Note(velocity=100, pitch=pitch, start=0.0, end=0.5))
    score.instruments.append(instrument)
    score.write(str(path))
    return path


def item(item_id: str, audio: Path) -> Item:
    return Item(item_id=item_id, audio=audio, annotation=None)


def test_mirrored_tree_pairs_each_song_with_its_own(tmp_path):
    """Colliding stems in different folders must not collapse onto one file."""
    audio = tmp_path / "audio"
    for song in ("songA", "songB"):
        (audio / song).mkdir(parents=True)
        (audio / song / "0000.wav").touch()

    estimates = tmp_path / "est"
    write_midi(estimates / "songA" / "0000.mid", pitch=60)
    write_midi(estimates / "songB" / "0000.mid", pitch=72)

    items = [item("songA/0000", audio / "songA" / "0000.wav"),
             item("songB/0000", audio / "songB" / "0000.wav")]
    found = pair_estimates(items, estimates)

    assert found["songA/0000"].parent.name == "songA"
    assert found["songB/0000"].parent.name == "songB"


def test_ambiguous_stems_are_refused_rather_than_guessed(tmp_path):
    """A flat output directory cannot say which song a 0000.mid belongs to."""
    audio = tmp_path / "audio"
    for song in ("songA", "songB"):
        (audio / song).mkdir(parents=True)
        (audio / song / "0000.wav").touch()

    # Both songs' transcriptions flattened into one directory, under names
    # that no longer say which is which.
    estimates = tmp_path / "est"
    write_midi(estimates / "run1" / "0000.mid", pitch=60)
    write_midi(estimates / "run2" / "0000.mid", pitch=72)

    items = [item("songA/0000", audio / "songA" / "0000.wav"),
             item("songB/0000", audio / "songB" / "0000.wav")]
    found = pair_estimates(items, estimates)

    # Refused, not guessed. The caller reports these as missing, which is a
    # visible question rather than a confident wrong number.
    assert found == {}


def test_flat_corpus_with_unique_stems_still_pairs(tmp_path):
    audio = tmp_path / "audio"
    audio.mkdir()
    for name in ("one", "two"):
        (audio / f"{name}.wav").touch()

    estimates = tmp_path / "est"
    write_midi(estimates / "one.mid", pitch=60)
    write_midi(estimates / "two.mid", pitch=72)

    items = [item("one", audio / "one.wav"), item("two", audio / "two.wav")]
    found = pair_estimates(items, estimates)

    assert found["one"].stem == "one"
    assert found["two"].stem == "two"


def test_suffixed_names_still_pair(tmp_path):
    """Basic Pitch appends _basic_pitch; CREPE Notes appends .crepe.transcription."""
    audio = tmp_path / "audio"
    audio.mkdir()
    (audio / "song.wav").touch()

    estimates = tmp_path / "est"
    write_midi(estimates / "song_basic_pitch.mid", pitch=60)

    found = pair_estimates([item("song", audio / "song.wav")], estimates)
    assert found["song"].name == "song_basic_pitch.mid"
