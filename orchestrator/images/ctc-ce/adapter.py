#!/usr/bin/env python3
"""Run CTC_CE_for_AST over /audio, one file at a time.

do_everything.py takes five positional arguments and writes one MIDI to a path
it is given, so nothing needs renaming afterwards.

Two keys in the config are overridden, and both are recorded rather than
assumed:

  do_svs   Upstream runs Spleeter to separate vocals from a mixture. This
           corpus is isolated vocal already, so separating it would degrade
           the input rather than help -- and the authors did exactly this
           themselves for ISMIR2014, which is likewise monophonic vocal. The
           image does not install Spleeter, so leaving this on would fail.
  tomidi   do_everything.py writes MIDI only when this is true. A config with
           it off produces no output and no error, which would read as forty
           silent failures.

The thresholds are NOT touched. onset_thres and offset_thres are tuned per
checkpoint upstream, so overriding them would be re-tuning the model rather
than running it.
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
APP = Path(os.environ.get("CTC_CE_APP", "/app"))
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}
# Torch checkpoints have no settled extension upstream, so the search is by
# elimination: anything that is not the config and not an obvious document.
NOT_CHECKPOINTS = {".yaml", ".yml", ".md", ".txt", ".json", ".pdf", ".png"}


def items():
    return [p for p in sorted(AUDIO.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUFFIXES
            and not p.name.startswith(".")]


def find_pair():
    """The checkpoint and the config yaml that belongs to it.

    Never guesses. The Drive folder holds several checkpoints, each with its
    own tuned onset and offset thresholds in its own config, and a mismatched
    pair does not fail -- it transcribes at the wrong operating point and
    looks like a result. So anything ambiguous is an error naming the fix,
    and CTC_CE_CHECKPOINT / CTC_CE_CONFIG override when several are wanted.
    """
    chosen = os.environ.get("CTC_CE_CHECKPOINT")
    config = os.environ.get("CTC_CE_CONFIG")
    if chosen and config:
        return Path(chosen), Path(config), ""
    if chosen or config:
        return None, None, ("set both CTC_CE_CHECKPOINT and CTC_CE_CONFIG or "
                            "neither -- a checkpoint without its own config "
                            "is the mismatch this refuses to make")

    root = CKPT / "ctc-ce"
    if not root.is_dir():
        root = CKPT
    checkpoints = [p for p in sorted(root.rglob("*"))
                   if p.is_file() and p.suffix.lower() not in NOT_CHECKPOINTS
                   and not p.name.startswith(".")]
    if not checkpoints:
        return None, None, f"no checkpoint file under {root}"

    pairs = []
    for checkpoint in checkpoints:
        beside = sorted(checkpoint.parent.glob("*.yaml")) + \
                 sorted(checkpoint.parent.glob("*.yml"))
        if len(beside) == 1:
            pairs.append((checkpoint, beside[0]))
        elif len(beside) > 1:
            return None, None, (
                f"{len(beside)} config yamls beside {checkpoint.name} in "
                f"{checkpoint.parent}, so which one tuned it is a guess. Put "
                "one checkpoint and its own config in each directory, or name "
                "them with CTC_CE_CHECKPOINT and CTC_CE_CONFIG.")
    if len(pairs) == 1:
        return pairs[0][0], pairs[0][1], ""
    if len(pairs) > 1:
        listed = ", ".join(sorted(c.parent.name for c, _ in pairs))
        return None, None, (
            f"{len(pairs)} checkpoint/config pairs under {root} ({listed}); "
            "pick one. Either leave a single pair there, or name it with "
            "CTC_CE_CHECKPOINT and CTC_CE_CONFIG. Running several means "
            "several runs, each with its own --as label.")
    return None, None, (
        f"found {checkpoints[0].name} but no config yaml beside it. Take the "
        "config that belongs to the checkpoint from the same Drive folder -- "
        "the onset and offset thresholds live in it, so without it there is "
        "no operating point to run at.")


def prepared_config(config_path):
    """A copy of the config with separation off and MIDI output on."""
    import yaml

    with open(config_path) as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        # An empty or malformed yaml would otherwise surface as an
        # AttributeError on None, forty times, naming neither file.
        raise ValueError(f"{config_path} is not a config mapping "
                         f"(read as {type(config).__name__})")
    before = {"do_svs": config.get("do_svs"), "tomidi": config.get("tomidi")}
    config["do_svs"] = False
    config["tomidi"] = True
    # The feature extractor is loaded by a path relative to the repository, so
    # the config has to keep working from /app as the working directory.
    target = CACHE / "inference.yaml"
    with open(target, "w") as handle:
        yaml.safe_dump(config, handle)
    return target, before, config


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    checkpoint, config_path, problem = find_pair()
    if checkpoint is None:
        print(f"FAIL {problem}", flush=True)
        (OUT / "adapter.json").write_text(json.dumps(
            {"system": "ctc-ce", "error": problem, "items": []}, indent=2))
        return 1

    try:
        config_file, before, config = prepared_config(config_path)
    except (OSError, ValueError) as exc:
        print(f"FAIL {exc}", flush=True)
        (OUT / "adapter.json").write_text(json.dumps(
            {"system": "ctc-ce", "error": str(exc), "items": []}, indent=2))
        return 1
    device = os.environ.get("CTC_CE_DEVICE", "cuda:0")
    print(f"checkpoint: {checkpoint}", flush=True)
    print(f"config:     {config_path}", flush=True)
    print(f"thresholds: onset {config.get('onset_thres')} "
          f"offset {config.get('offset_thres')} (as shipped, untouched)", flush=True)
    print(f"overrides:  do_svs {before['do_svs']} -> False, "
          f"tomidi {before['tomidi']} -> True", flush=True)

    rows = []
    for source in items():
        relative = source.relative_to(AUDIO)
        target = OUT / "midi" / relative.with_suffix(".mid")
        target.parent.mkdir(parents=True, exist_ok=True)
        started = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(APP / "do_everything.py"),
                 str(source), str(target), str(checkpoint),
                 str(config_file), device],
                cwd=str(APP), capture_output=True, text=True)
            trouble = (proc.stderr or proc.stdout)
        except OSError as exc:
            trouble = f"could not start do_everything.py: {exc}"
        ok = target.exists()
        row = {"item": str(relative), "status": "ok" if ok else "fail",
               "seconds": round(time.time() - started, 2),
               "stderr": "" if ok else trouble[-3000:]}
        rows.append(row)
        print(f"{'ok  ' if ok else 'FAIL'} {relative}", flush=True)
        if not ok and row["stderr"]:
            for line in row["stderr"].strip().splitlines()[-8:]:
                print(f"       {line}", flush=True)

    revision = APP / "REVISION"
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "ctc-ce",
         "source_revision": revision.read_text().strip() if revision.exists() else "",
         "checkpoint": str(checkpoint), "config": str(config_path),
         "onset_thres": config.get("onset_thres"),
         "offset_thres": config.get("offset_thres"),
         "overrides": {"do_svs": False, "tomidi": True},
         "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
