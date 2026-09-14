#!/usr/bin/env python3
"""Essentia's classical melody pipeline, as a note transcriber."""
import json
import os
import sys
import time
from pathlib import Path

import essentia.standard as es
import pretty_midi

# Paths are the container's by default and overridable by environment, so an
# adapter can be exercised outside Docker -- which is how the three that could
# be run at all were checked before anyone built an image.
AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CKPT = Path(os.environ.get("BENCH_CKPT", "/ckpt"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}
SAMPLE_RATE, HOP = 44100, 128


def transcribe(path: Path):
    audio = es.MonoLoader(filename=str(path), sampleRate=SAMPLE_RATE)()
    pitch, _ = es.PredominantPitchMelodia(frameSize=2048, hopSize=HOP)(audio)
    onset, duration, midi = es.PitchContourSegmentation(hopSize=HOP)(pitch, audio)
    return list(zip(onset, duration, midi))


def write_midi(notes, target: Path):
    score = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=53)  # voice oohs
    for onset, duration, pitch in notes:
        instrument.notes.append(pretty_midi.Note(
            velocity=100, pitch=int(round(float(pitch))),
            start=float(onset), end=float(onset) + float(duration)))
    score.instruments.append(instrument)
    target.parent.mkdir(parents=True, exist_ok=True)
    score.write(str(target))


def main():
    rows = []
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    for source in sources:
        relative = source.relative_to(AUDIO)
        started = time.time()
        try:
            notes = transcribe(source)
            write_midi(notes, OUT / "midi" / relative.with_suffix(".mid"))
            row = {"item": str(relative), "status": "ok", "notes": len(notes)}
        except Exception as exc:                       # noqa: BLE001
            row = {"item": str(relative), "status": "fail", "error": str(exc)[:400]}
        row["seconds"] = round(time.time() - started, 2)
        rows.append(row)
        print(f"{'ok  ' if row['status'] == 'ok' else 'FAIL'} {relative}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "essentia", "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
