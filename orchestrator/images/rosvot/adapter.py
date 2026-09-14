#!/usr/bin/env python3
"""ROSVOT over /audio, via the metadata.json it expects.

Two flags are load-bearing and neither is discoverable from --help:

  --verbose    without it, failures are silent. save_result's word-boundary
               branch ends its except with a bare return, so an item that
               raises is skipped with no MIDI and no message.
  --apply_rwbd without it (or word boundaries, or
               infer_regulate_real_note_itv=False) the note-interval
               regulation step needs word_durs, which a corpus annotated from
               pitch does not have. Every item raises and the output directory
               comes out empty.

Item names must be unique across the corpus, so they are built from the
relative path rather than the stem: M4Singer names every segment 0000.wav
inside its own folder.
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


def item_name(relative: Path) -> str:
    return str(relative.with_suffix("")).replace("/", "__")


def main():
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    if not sources:
        print("no audio under /audio", file=sys.stderr)
        return 2

    by_item = {item_name(p.relative_to(AUDIO)): p.relative_to(AUDIO)
               for p in sources}
    metadata = [{"item_name": item_name(p.relative_to(AUDIO)),
                 "wav_fn": str(p)} for p in sources]
    work = CACHE / "rosvot"
    work.mkdir(parents=True, exist_ok=True)
    meta_path = work / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    produced_dir = work / "midi"

    argv = ["python3", "inference/rosvot.py",
            "--metadata", str(meta_path), "-o", str(produced_dir),
            "--ckpt", str(CKPT / "rosvot" / "model.pt"), "--verbose"]
    wbd = CKPT / "rwbd" / "model.pt"
    if wbd.exists():
        argv += ["--apply_rwbd", "--wbd_ckpt", str(wbd)]
    else:
        print("WARNING: no rwbd checkpoint at /ckpt/rwbd/model.pt. Without it "
              "you must set infer_regulate_real_note_itv=False in the hparams "
              "or every item will be skipped silently.", file=sys.stderr)

    started = time.time()
    proc = subprocess.run(argv, cwd="/app", capture_output=True, text=True)
    elapsed = time.time() - started
    print(proc.stdout[-4000:])
    if proc.returncode != 0:
        print(proc.stderr[-4000:], file=sys.stderr)

    rows = []
    for name, relative in by_item.items():
        candidates = list(produced_dir.rglob(f"{name}.mid"))
        if candidates:
            target = OUT / "midi" / relative.with_suffix(".mid")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(candidates[0].read_bytes())
            rows.append({"item": str(relative), "status": "ok"})
        else:
            rows.append({"item": str(relative), "status": "fail",
                         "error": "no MIDI written; check --verbose output"})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "rosvot", "seconds": round(elapsed, 1),
         "exit_code": proc.returncode, "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
