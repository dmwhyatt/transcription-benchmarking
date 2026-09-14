#!/usr/bin/env python3
"""The phoneme-informed model, per file.

It takes a --bpm and may quantise against it. BPM is fixed at 120 for every
item unless PHN_BPM says otherwise, which is a choice worth knowing about:
if its output lands on a grid, its offsets will disagree with a reference
annotated from audio in a way that looks like error and is convention. Check
one output before reading anything into its COnPOff.
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
MODEL = os.environ.get("PHN_MODEL", str(CKPT / "model.pt"))
BPM = os.environ.get("PHN_BPM", "120")
DEVICE = os.environ.get("PHN_DEVICE", "cuda:0")


def main():
    if not Path(MODEL).exists():
        print(f"no checkpoint at {MODEL}; see bench.py fetch", file=sys.stderr)
        return 2
    rows = []
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    for source in sources:
        relative = source.relative_to(AUDIO)
        target = OUT / "midi" / relative.with_suffix(".mid")
        target.parent.mkdir(parents=True, exist_ok=True)
        started = time.time()
        proc = subprocess.run(
            ["python3", "infer.py", MODEL, str(source), str(target),
             "--bpm", BPM, "--device", DEVICE],
            cwd="/app", capture_output=True, text=True)
        ok = target.exists() and target.stat().st_size > 0
        row = {"item": str(relative), "status": "ok" if ok else "fail",
               "seconds": round(time.time() - started, 2)}
        if not ok:
            row["error"] = (proc.stderr or proc.stdout)[-400:]
        rows.append(row)
        print(f"{'ok  ' if ok else 'FAIL'} {relative}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "phoneme-informed", "bpm": BPM, "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
