#!/usr/bin/env python3
"""The MIR-ST500 baseline, per file, straight to MIDI.

Run per file rather than handing it the folder: do_everything.py accepts a
directory, but then one unreadable recording takes the whole run with it, and
there is no per-item timing.

SEPARATE=1 turns on its Spleeter stage, for corpora that are not already
solo voice. The image does not install Spleeter unless built for it.
"""
import json
import os
import subprocess
import sys
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
MODEL = os.environ.get("MIRST500_MODEL", "models/1005_e_4")
ONSET = os.environ.get("MIRST500_ONSET", "0.4")
OFFSET = os.environ.get("MIRST500_OFFSET", "0.5")
DEVICE = os.environ.get("MIRST500_DEVICE", "cuda:0")


def main():
    rows = []
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    for source in sources:
        relative = source.relative_to(AUDIO)
        target = OUT / "midi" / relative.with_suffix(".mid")
        target.parent.mkdir(parents=True, exist_ok=True)
        argv = ["python3", "do_everything.py", str(source), str(target),
                "-p", MODEL, "-on", ONSET, "-off", OFFSET, "-d", DEVICE]
        if os.environ.get("SEPARATE") == "1":
            argv.append("-s")
        started = time.time()
        proc = subprocess.run(argv, cwd="/app/AST", capture_output=True, text=True)
        ok = target.exists() and target.stat().st_size > 0
        row = {"item": str(relative), "status": "ok" if ok else "fail",
               "seconds": round(time.time() - started, 2)}
        if not ok:
            row["error"] = (proc.stderr or proc.stdout)[-400:]
        rows.append(row)
        print(f"{'ok  ' if ok else 'FAIL'} {relative}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "mirst500", "model": MODEL, "onset_thres": ONSET,
         "offset_thres": OFFSET, "separated": os.environ.get("SEPARATE") == "1",
         "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
