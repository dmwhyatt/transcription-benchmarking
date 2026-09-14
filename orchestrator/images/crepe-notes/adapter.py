#!/usr/bin/env python3
"""CREPE Notes over /audio.

It writes <stem>.<tracker>.transcription.mid into the working directory, so
each file is run in its own scratch directory and the result is moved to the
mirrored path.

CREPE_NOTES_BACKEND selects the pitch tracker. `crepe` is the default and the
only one the published results were measured with; the author marks pesto,
penn and torchcrepe experimental, so a number produced with one of those is
not a number for the paper's method.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Paths are the container's by default and overridable by environment, so an
# adapter can be exercised outside Docker -- which is how the three that could
# be run at all were checked before anyone built an image.
AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CKPT = Path(os.environ.get("BENCH_CKPT", "/ckpt"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}
BACKEND = os.environ.get("CREPE_NOTES_BACKEND", "crepe")
MIN_DURATION = os.environ.get("CREPE_NOTES_MIN_DURATION", "0.05")


def main():
    # The README advises a longer minimum note for voice than its 30 ms
    # default; 50 ms is its own suggestion for "things like vocals".
    rows = []
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    for source in sources:
        relative = source.relative_to(AUDIO)
        started = time.time()
        with tempfile.TemporaryDirectory(dir=str(CACHE)) as scratch:
            proc = subprocess.run(
                ["crepe_notes", "--pitch-tracker", BACKEND,
                 "--min-duration", MIN_DURATION, str(source)],
                cwd=scratch, capture_output=True, text=True)
            produced = sorted(Path(scratch).rglob("*.mid"))
            if produced:
                target = OUT / "midi" / relative.with_suffix(".mid")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(produced[0].read_bytes())
                row = {"item": str(relative), "status": "ok"}
            else:
                row = {"item": str(relative), "status": "fail",
                       "error": (proc.stderr or proc.stdout)[-400:]}
        row["seconds"] = round(time.time() - started, 2)
        rows.append(row)
        print(f"{'ok  ' if row['status'] == 'ok' else 'FAIL'} {relative}", flush=True)
        if row["status"] != "ok" and row.get("error"):
            # The reason belongs on screen. Burying it in adapter.json means
            # the orchestrator reports "0/2 transcribed" and nothing else.
            for line in str(row["error"]).strip().splitlines()[-8:]:
                print(f"       {line}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "crepe-notes", "backend": BACKEND,
         "min_duration": MIN_DURATION, "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed with backend {BACKEND}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
