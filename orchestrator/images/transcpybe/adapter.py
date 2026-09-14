#!/usr/bin/env python3
"""transcPybe over /audio.

transcPybe already batches a directory, and batching matters here: it loads
torch and torchcrepe once instead of once per recording. But it writes a flat
output directory with names disambiguated only as far as it needs, while this
contract wants the audio's relative path mirrored. Those agree exactly when
every stem in the corpus is unique, which is the vocadito case and most cases.

So: batch when the stems are unique, and fall back to one process per
recording when they are not, rather than guessing how its names map back.
M4Singer, where every segment is 0000.wav, is the corpus that takes the slow
path -- and the slow path is the correct one there.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))

SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}
DEVICE = os.environ.get("TRANSCPYBE_DEVICE", "auto")
BACKEND = os.environ.get("TRANSCPYBE_F0_BACKEND", "crepe")
EXTRA = os.environ.get("TRANSCPYBE_ARGS", "").split()


def sources():
    return [p for p in sorted(AUDIO.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUFFIXES
            and not p.name.startswith(".")]


def base_argv():
    return ["transcpybe", "--f0-backend", BACKEND, "--device", DEVICE,
            "--no-json", "--no-csv", "--no-progress", *EXTRA]


def run_batch(paths):
    """One process for the whole corpus, then map each MIDI back by stem."""
    scratch = CACHE / "batch"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    started = time.time()
    proc = subprocess.run(base_argv() + [str(AUDIO), "-o", str(scratch), "--overwrite"],
                          capture_output=True, text=True)
    print(proc.stdout[-2000:])
    if proc.returncode != 0:
        print(proc.stderr[-2000:], file=sys.stderr)
    produced = {p.stem: p for p in scratch.rglob("*.mid")}

    rows = []
    for source in paths:
        relative = source.relative_to(AUDIO)
        made = produced.get(relative.stem)
        if made is not None:
            target = OUT / "midi" / relative.with_suffix(".mid")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(made.read_bytes())
            rows.append({"item": str(relative), "status": "ok"})
        else:
            rows.append({"item": str(relative), "status": "fail",
                         "error": "no MIDI with this stem in the batch output"})
        print(f"{'ok  ' if rows[-1]['status'] == 'ok' else 'FAIL'} {relative}",
              flush=True)
    return rows, time.time() - started, "batch"


def run_one_at_a_time(paths):
    rows = []
    for source in paths:
        relative = source.relative_to(AUDIO)
        scratch = CACHE / "single"
        if scratch.exists():
            shutil.rmtree(scratch)
        scratch.mkdir(parents=True)
        started = time.time()
        proc = subprocess.run(
            base_argv() + [str(source), "-o", str(scratch), "--overwrite"],
            capture_output=True, text=True)
        produced = sorted(scratch.rglob("*.mid"))
        if produced:
            target = OUT / "midi" / relative.with_suffix(".mid")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(produced[0].read_bytes())
            row = {"item": str(relative), "status": "ok"}
        else:
            row = {"item": str(relative), "status": "fail",
                   "error": (proc.stderr or proc.stdout)[-3000:]}
        row["seconds"] = round(time.time() - started, 2)
        rows.append(row)
        print(f"{'ok  ' if row['status'] == 'ok' else 'FAIL'} {relative}", flush=True)
        if row["status"] != "ok" and row.get("error"):
            for line in str(row["error"]).strip().splitlines()[-8:]:
                print(f"       {line}", flush=True)
    return rows, None, "per-file"


def main():
    paths = sources()
    if not paths:
        print("no audio under /audio", file=sys.stderr)
        return 2
    stems = [p.relative_to(AUDIO).stem for p in paths]
    unique = len(set(stems)) == len(stems)
    print(f"{len(paths)} recordings; stems {'unique' if unique else 'collide'}, "
          f"so running {'one batch' if unique else 'one process per recording'}",
          flush=True)

    rows, elapsed, mode = (run_batch(paths) if unique
                           else run_one_at_a_time(paths))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "transcpybe", "mode": mode, "f0_backend": BACKEND,
         "device": DEVICE, "extra_args": EXTRA,
         "seconds": round(elapsed, 1) if elapsed else None,
         "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
