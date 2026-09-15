#!/usr/bin/env python3
"""Run Basic Pitch over /audio, one file at a time.

Per file rather than in one batch call so a single unreadable recording is a
recorded failure rather than an aborted sweep, and so the output tree can
mirror the input's relative paths.
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


def items():
    return [p for p in sorted(AUDIO.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUFFIXES
            and not p.name.startswith(".")]


def main():
    rows = []
    for source in items():
        relative = source.relative_to(AUDIO)
        target = OUT / "midi" / relative.with_suffix(".mid")
        target.parent.mkdir(parents=True, exist_ok=True)
        started = time.time()
        with tempfile.TemporaryDirectory(dir=str(CACHE)) as scratch:
            proc = subprocess.run(
                ["basic-pitch", scratch, str(source), "--save-midi"],
                capture_output=True, text=True)
            # Basic Pitch names its output <stem>_basic_pitch.mid. The
            # benchmark would pair that through its prefix rule, but renaming
            # here makes every system's pairing exact, which is one fewer
            # thing that can silently differ between them.
            produced = sorted(Path(scratch).rglob("*.mid"))
            if produced:
                target.write_bytes(produced[0].read_bytes())
        ok = target.exists()
        row = {"item": str(relative), "status": "ok" if ok else "fail",
               "seconds": round(time.time() - started, 2),
               "stderr": "" if ok else proc.stderr[-3000:]}
        rows.append(row)
        print(f"{'ok  ' if ok else 'FAIL'} {relative}", flush=True)
        if not ok and row["stderr"]:
            for line in row["stderr"].strip().splitlines()[-8:]:
                print(f"       {line}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "basic-pitch", "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
