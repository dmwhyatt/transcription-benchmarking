#!/usr/bin/env python3
"""Run Tony's automatic note transcription over /audio, one file at a time.

That is the pYIN Vamp plugin's "notes" output with Tony's own parameters
(/tony-notes.n3), hosted by Sonic Annotator. pYIN gives each note as onset,
duration and a frequency in Hz: the median of the note's smoothed pitch track,
not rounded to a semitone.

Tony also conditions the audio before pYIN sees it (MainWindow.cpp:
setResampleOnLoad(true), setFixedSampleRate(44100), setNormaliseAudio(true)),
and that matters, because pYIN's low-amplitude suppression compares each
frame's RMS with an absolute threshold. So a file not at 44.1 kHz is resampled
to it here (soxr, very high quality, float, never clipped), and Sonic
Annotator's --normalise applies the same peak normalisation, through the same
svcore reader Tony uses. Channels are left for the host to mix down, as Tony's
does. On vocadito_1 (peak 0.13) normalising moved the share of annotator A1's
onsets that coincide with this output to the millisecond from 0.61 to 0.86.

MIDI gets that pitch rounded to the nearest semitone, as every other adapter
here writes it. The unrounded pitch is kept beside it, in notes/<item>.csv
(onset_s, offset_s, midi_float), for any later measured-pitch comparison.
"""
import csv
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pretty_midi
import soundfile as sf
import soxr

AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CKPT = Path(os.environ.get("BENCH_CKPT", "/ckpt"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))
TRANSFORM = Path(os.environ.get("TONY_TRANSFORM", "/tony-notes.n3"))
RATE = 44100            # Tony's fixed sample rate
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}


def items():
    return [p for p in sorted(AUDIO.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUFFIXES
            and not p.name.startswith(".")]


def notes_from_csv(text):
    """(onset, offset, midi_float) from Sonic Annotator's CSV.

    Each row ends in timestamp, duration, value; a leading filename column
    appears or not depending on the writer's options, so the last three
    fields are read rather than fixed positions.
    """
    notes = []
    for row in csv.reader(io.StringIO(text)):
        fields = [f.strip() for f in row if f.strip()]
        if len(fields) < 3:
            continue
        try:
            onset, duration, hz = (float(f) for f in fields[-3:])
        except ValueError:
            continue
        if duration <= 0 or hz <= 0:
            continue
        notes.append((onset, onset + duration, 69.0 + 12.0 * math.log2(hz / 440.0)))
    return notes


def at_tony_rate(source, scratch):
    """The file itself if it is already at 44.1 kHz, else a resampled copy."""
    info = sf.info(str(source))
    if info.samplerate == RATE:
        return source
    audio, rate = sf.read(str(source), dtype="float32", always_2d=True)
    resampled = soxr.resample(audio, rate, RATE, quality="VHQ")
    copy = Path(scratch) / "input.wav"
    sf.write(str(copy), resampled, RATE, subtype="FLOAT")
    return copy


def write_midi(notes, target):
    score = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=53)  # voice oohs
    for onset, offset, pitch in notes:
        instrument.notes.append(pretty_midi.Note(
            velocity=100, pitch=int(round(pitch)), start=onset, end=offset))
    score.instruments.append(instrument)
    target.parent.mkdir(parents=True, exist_ok=True)
    score.write(str(target))


def main():
    rows = []
    for source in items():
        relative = source.relative_to(AUDIO)
        target = OUT / "midi" / relative.with_suffix(".mid")
        started = time.time()
        trouble, notes = "", None
        try:
            with tempfile.TemporaryDirectory(dir=str(CACHE)) as scratch:
                written = Path(scratch) / "csv"
                written.mkdir()
                proc = subprocess.run(
                    ["sonic-annotator", "--normalise", "-t", str(TRANSFORM),
                     "-w", "csv", "--csv-basedir", str(written), "--csv-force",
                     str(at_tony_rate(source, scratch))],
                    capture_output=True, text=True)
                produced = sorted(written.rglob("*.csv"))
                if proc.returncode == 0 and produced:
                    notes = notes_from_csv(produced[0].read_text())
                else:
                    trouble = (proc.stderr or proc.stdout or
                               f"exit {proc.returncode}, no CSV written")
        except OSError as exc:
            trouble = f"could not start sonic-annotator: {exc}"
        if notes is not None:
            write_midi(notes, target)
            sidecar = OUT / "notes" / relative.with_suffix(".csv")
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            with sidecar.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["onset_s", "offset_s", "midi_float"])
                writer.writerows([f"{a:.6f}", f"{b:.6f}", f"{p:.4f}"] for a, b, p in notes)
        ok = target.exists()
        try:
            audio_s = round(sf.info(str(source)).duration, 3)
        except Exception:                                   # noqa: BLE001
            audio_s = None
        row = {"item": str(relative), "status": "ok" if ok else "fail",
               "notes": len(notes) if notes is not None else 0,
               "audio_seconds": audio_s,
               "seconds": round(time.time() - started, 2),
               "stderr": "" if ok else trouble[-3000:]}
        rows.append(row)
        print(f"{'ok  ' if ok else 'FAIL'} {relative}", flush=True)
        if not ok and row["stderr"]:
            for line in row["stderr"].strip().splitlines()[-8:]:
                print(f"       {line}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    revision = Path("/usr/local/lib/vamp/pyin.REVISION")
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "tony",
         "pyin_revision": revision.read_text().strip() if revision.exists() else "",
         "conditioning": f"resampled to {RATE} Hz where needed; peak-normalised",
         "transform": TRANSFORM.read_text() if TRANSFORM.exists() else "",
         "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
