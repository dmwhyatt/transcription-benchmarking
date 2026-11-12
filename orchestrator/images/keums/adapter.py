#!/usr/bin/env python3
"""Run Kum et al.'s singing transcription over /audio, one file at a time.

The upstream CLI takes one audio file and an output *directory*, and names
what it writes after the input stem -- so a flat output directory would
collide the moment two recordings in different subdirectories share a stem.
Each file therefore gets its own scratch directory, and the result is moved to
mirror the input's relative path.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))
APP = Path(os.environ.get("KEUMS_APP", "/app"))
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}


def items():
    return [p for p in sorted(AUDIO.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUFFIXES
            and not p.name.startswith(".")]


def revision():
    marker = APP / "REVISION"
    return marker.read_text().strip() if marker.exists() else ""


def main():
    rows = []
    for source in items():
        relative = source.relative_to(AUDIO)
        target = OUT / "midi" / relative.with_suffix(".mid")
        target.parent.mkdir(parents=True, exist_ok=True)
        started = time.time()
        trouble = ""
        with tempfile.TemporaryDirectory(dir=str(CACHE)) as scratch:
            try:
                proc = subprocess.run(
                    [sys.executable, str(APP / "src" / "singing_transcription.py"),
                     "-i", str(source), "-o", scratch, "-ot", "midi"],
                    cwd=str(APP / "src"), capture_output=True, text=True)
                trouble = (proc.stderr or proc.stdout)
            except OSError as exc:
                # A missing interpreter or working directory raises before the
                # child starts. Letting that propagate would abandon the sweep
                # on item one and write no adapter.json at all, which is the
                # opposite of running these one file at a time.
                trouble = f"could not start the upstream CLI: {exc}"
            produced = sorted(Path(scratch).rglob("*.mid"))
            if produced:
                shutil.copyfile(produced[0], target)
        ok = target.exists()
        row = {"item": str(relative), "status": "ok" if ok else "fail",
               "seconds": round(time.time() - started, 2),
               "stderr": "" if ok else trouble[-3000:]}
        rows.append(row)
        print(f"{'ok  ' if ok else 'FAIL'} {relative}", flush=True)
        if not ok and row["stderr"]:
            for line in row["stderr"].strip().splitlines()[-8:]:
                print(f"       {line}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "keums", "source_revision": revision(), "items": rows},
        indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
