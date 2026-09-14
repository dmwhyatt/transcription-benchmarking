#!/usr/bin/env python3
"""Omnizart `vocal transcribe`, one file at a time.

The CLI's output flag has moved between versions, so rather than depend on
one spelling this runs in a scratch directory and collects whatever MIDI
appeared. That is uglier and survives an upstream rename.
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


def main():
    rows = []
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    for source in sources:
        relative = source.relative_to(AUDIO)
        started = time.time()
        with tempfile.TemporaryDirectory(dir=str(CACHE)) as scratch:
            proc = subprocess.run(
                ["omnizart", "vocal", "transcribe", str(source), "-o", scratch],
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
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "omnizart", "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
