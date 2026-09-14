#!/usr/bin/env python3
"""aubio's note tracker, parsed into MIDI.

`aubio notes` prints one line per event. Lines with three fields are a
complete note -- pitch, start, end -- and lines with one field are the
bare timestamps it emits around them. Only the three-field lines are notes;
this was established by running it rather than by reading the manual.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pretty_midi

# Paths are the container's by default and overridable by environment, so an
# adapter can be exercised outside Docker -- which is how the three that could
# be run at all were checked before anyone built an image.
AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CKPT = Path(os.environ.get("BENCH_CKPT", "/ckpt"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}


def parse(text: str):
    notes = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        try:
            pitch, start, end = (float(f) for f in fields)
        except ValueError:
            continue
        if end > start and 0 < pitch < 128:
            notes.append((start, end, pitch))
    return notes


def main():
    rows = []
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    for source in sources:
        relative = source.relative_to(AUDIO)
        started = time.time()
        proc = subprocess.run(["aubio", "notes", str(source)],
                              capture_output=True, text=True)
        notes = parse(proc.stdout)
        if proc.returncode == 0:
            score = pretty_midi.PrettyMIDI()
            instrument = pretty_midi.Instrument(program=53)
            for start, end, pitch in notes:
                instrument.notes.append(pretty_midi.Note(
                    velocity=100, pitch=int(round(pitch)), start=start, end=end))
            score.instruments.append(instrument)
            target = OUT / "midi" / relative.with_suffix(".mid")
            target.parent.mkdir(parents=True, exist_ok=True)
            score.write(str(target))
            row = {"item": str(relative), "status": "ok", "notes": len(notes)}
        else:
            row = {"item": str(relative), "status": "fail",
                   "error": proc.stderr[-400:]}
        row["seconds"] = round(time.time() - started, 2)
        rows.append(row)
        print(f"{'ok  ' if row['status'] == 'ok' else 'FAIL'} {relative}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "aubio", "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
