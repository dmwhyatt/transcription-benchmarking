#!/usr/bin/env python3
"""GAME over the whole corpus in one process.

GAME writes its MIDI beside each input, and /audio is read-only, so the tree
is copied into /cache first. Batching the whole corpus through one model load
is the point of this system -- it is the cheapest singing-specific entrant to
run -- so this adapter does not fall back to per-file invocation.
"""
import json
import os
import shutil
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
MODEL = os.environ.get("GAME_MODEL", str(CKPT / "model.pt"))


def main():
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    if not sources:
        print("no audio under /audio", file=sys.stderr)
        return 2
    model = Path(MODEL)
    if not model.exists():
        # GAME's releases include an ONNX bundle, which its own README says is
        # not runnable from this repository: "We don't provide implementation
        # of ONNX model inference pipeline in this repository." infer.py wants
        # a PyTorch checkpoint. Saying that is worth more than "not found".
        found = sorted(list(CKPT.rglob("*.pt")) + list(CKPT.rglob("*.ckpt")))
        if found:
            model = found[0]
            print(f"using checkpoint {model}", flush=True)
        else:
            onnx = sorted(CKPT.rglob("*.onnx"))
            if onnx:
                print(f"Found only ONNX models under {CKPT}:", file=sys.stderr)
                for path in onnx[:8]:
                    print(f"  {path.relative_to(CKPT)}", file=sys.stderr)
                print("\nGAME does not ship an ONNX inference pipeline -- its "
                      "README says so outright -- and infer.py takes a PyTorch "
                      "checkpoint. Download the non-ONNX release asset "
                      "instead.", file=sys.stderr)
            else:
                print(f"No .pt or .ckpt anywhere under {CKPT}; "
                      "see bench.py fetch", file=sys.stderr)
            return 2

    work = CACHE / "work"
    if work.exists():
        shutil.rmtree(work)
    for source in sources:
        target = work / source.relative_to(AUDIO)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    started = time.time()
    extensions = sorted({p.suffix.lower() for p in sources})
    codes = []
    for extension in extensions:
        proc = subprocess.run(
            ["python3", "infer.py", "extract", str(work), "-m", str(model),
             "--glob", f"*{extension}", "--output-formats", "mid"],
            cwd="/app", capture_output=True, text=True)
        codes.append(proc.returncode)
        print(proc.stdout[-2000:])
        if proc.returncode != 0:
            print(proc.stderr[-2000:], file=sys.stderr)
    elapsed = time.time() - started

    rows = []
    for source in sources:
        relative = source.relative_to(AUDIO)
        produced = (work / relative).with_suffix(".mid")
        if produced.exists():
            target = OUT / "midi" / relative.with_suffix(".mid")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(produced.read_bytes())
            rows.append({"item": str(relative), "status": "ok"})
        else:
            rows.append({"item": str(relative), "status": "fail",
                         "error": "no MIDI beside the copied input"})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "game", "model": str(model), "seconds": round(elapsed, 1),
         "exit_codes": codes, "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed in {elapsed:.0f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
