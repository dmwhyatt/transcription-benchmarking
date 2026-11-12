#!/usr/bin/env python3
"""Run SOME over /audio, one file at a time.

infer.py takes one wav and writes one MIDI, and takes an explicit --midi path,
so unlike most systems here nothing needs renaming afterwards.

The checkpoint is found rather than configured: a release zip can extract to
its own subdirectory or straight into /ckpt/some depending on how it was
unpacked, and both are common enough that failing on one of them would be a
support question rather than a finding.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CKPT = Path(os.environ.get("BENCH_CKPT", "/ckpt"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))
APP = Path(os.environ.get("SOME_APP", "/app"))
TEMPO = os.environ.get("SOME_TEMPO", "120")
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}


def items():
    return [p for p in sorted(AUDIO.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUFFIXES
            and not p.name.startswith(".")]


def find_checkpoint():
    """The .ckpt that has a config.yaml beside it.

    infer.py reads model_path.with_name('config.yaml'), so a checkpoint
    without one is not usable and picking it would fail forty times with a
    FileNotFoundError about a file the user never named.
    """
    root = CKPT / "some"
    if not root.is_dir():
        root = CKPT
    usable, bare = [], []
    for path in sorted(root.rglob("*.ckpt")):
        (usable if path.with_name("config.yaml").exists() else bare).append(path)
    if usable:
        return usable[0], ""
    if bare:
        return None, (f"found {bare[0]} but no config.yaml beside it; extract "
                      "the release zip whole rather than the checkpoint alone")
    return None, f"no .ckpt under {root}"


def link_pretrained():
    """SOME reads RMVPE from its own pretrained/ directory, not from a flag.

    Optional upstream -- without it SOME falls back to parselmouth -- so a
    missing one is not an error, but which of the two ran changes the result
    and so is recorded.
    """
    supplied = CKPT / "some" / "pretrained"
    target = APP / "pretrained"
    if supplied.is_dir() and not target.exists():
        target.symlink_to(supplied)
    return target.exists()


def main():
    checkpoint, problem = find_checkpoint()
    OUT.mkdir(parents=True, exist_ok=True)
    if checkpoint is None:
        print(f"FAIL no usable checkpoint: {problem}", flush=True)
        (OUT / "adapter.json").write_text(json.dumps(
            {"system": "some", "error": problem, "items": []}, indent=2))
        return 1

    pretrained = link_pretrained()
    print(f"checkpoint: {checkpoint}", flush=True)
    print(f"pitch extractor: {'RMVPE' if pretrained else 'parselmouth (no RMVPE supplied)'}",
          flush=True)

    rows = []
    for source in items():
        relative = source.relative_to(AUDIO)
        target = OUT / "midi" / relative.with_suffix(".mid")
        target.parent.mkdir(parents=True, exist_ok=True)
        started = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(APP / "infer.py"),
                 "--model", str(checkpoint), "--wav", str(source),
                 "--midi", str(target), "--tempo", TEMPO],
                cwd=str(APP), capture_output=True, text=True)
            trouble = (proc.stderr or proc.stdout)
        except OSError as exc:
            # As in every adapter here: a child that cannot start is one
            # recorded failure, not an abandoned sweep.
            trouble = f"could not start infer.py: {exc}"
        ok = target.exists()
        row = {"item": str(relative), "status": "ok" if ok else "fail",
               "seconds": round(time.time() - started, 2),
               "stderr": "" if ok else trouble[-3000:]}
        rows.append(row)
        print(f"{'ok  ' if ok else 'FAIL'} {relative}", flush=True)
        if not ok and row["stderr"]:
            for line in row["stderr"].strip().splitlines()[-8:]:
                print(f"       {line}", flush=True)

    revision = (APP / "REVISION")
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "some",
         "source_revision": revision.read_text().strip() if revision.exists() else "",
         "checkpoint": str(checkpoint),
         "pitch_extractor": "rmvpe" if pretrained else "parselmouth",
         "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
