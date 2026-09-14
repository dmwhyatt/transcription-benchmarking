#!/usr/bin/env python3
"""Run every transcription system over the same corpus, then score them all.

The point is that the systems differ and the treatment does not. Each one runs
in its own container, from its own pinned image, over the same read-only audio,
and writes MIDI into its own output tree under one filename convention. Only
then does the benchmark see any of it, through ``--estimates``, which is the
same path a hand-run system would take.

Nothing here imports a transcriber, and nothing here is imported by the
benchmark: this directory is not part of the installed package. That is
deliberate. A benchmark that depends on the systems it measures can only ever
measure those.

    ./bench.py doctor                     # is this machine able to do it
    ./bench.py build                      # build the images
    ./bench.py fetch                      # get the checkpoints
    ./bench.py transcribe --audio DIR     # run every system
    ./bench.py score --audio DIR -a ANN   # score every system
    ./bench.py compare                    # every pair, with intervals
    ./bench.py all --audio DIR -a ANN     # the lot

Failure of one system is recorded and the sweep continues, because the
alternative is a half-finished run that looks complete. Every step writes
provenance next to its output.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import systems as registry  # noqa: E402

AUDIO_SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}


# --------------------------------------------------------------------------
# plumbing


def log(message: str) -> None:
    print(f"[{dt.datetime.now():%H:%M:%S}] {message}", flush=True)


def run(argv: Sequence[str], *, capture: bool = False, check: bool = True,
        timeout: Optional[int] = None, dry: bool = False,
        tee: Optional[Path] = None):
    """Run a command, showing it first. The showing is the point."""
    printable = " ".join(str(a) for a in argv)
    if dry:
        print(f"    would run: {printable}")
        return subprocess.CompletedProcess(argv, 0, "", "")
    log(f"$ {printable}")
    # stdout and stderr are merged rather than captured separately: a build
    # log is one stream, and a failure whose cause is in stderr while the
    # step numbers are in stdout is unreadable split in two.
    result = subprocess.run(
        [str(a) for a in argv], check=check, timeout=timeout, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None)
    if tee is not None and result.stdout:
        tee.parent.mkdir(parents=True, exist_ok=True)
        tee.write_text(result.stdout)
    return result


def audio_items(audio_dir: Path) -> List[Path]:
    """Every audio file, as paths relative to the corpus root."""
    found = [p.relative_to(audio_dir)
             for p in sorted(audio_dir.rglob("*"))
             if p.is_file() and p.suffix.lower() in AUDIO_SUFFIXES
             and not p.name.startswith(".")]
    return found


def stage_subset(audio_dir: Path, items: Sequence[Path], staging: Path) -> Path:
    """A corpus of just `items`, for a smoke run, with the tree preserved.

    Hardlinked where the filesystem allows, so a 40-file subset of a large
    corpus costs nothing. Copies only when it must.
    """
    if staging.exists():
        shutil.rmtree(staging)
    for item in items:
        target = staging / item
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(audio_dir / item, target)
        except OSError:
            shutil.copy2(audio_dir / item, target)
    return staging


# --------------------------------------------------------------------------
# layout


class Work:
    """Where everything lands. One directory, so a sweep is one thing to keep."""

    def __init__(self, root: Path) -> None:
        # Absolute, always. Every bind mount below is built from this, and
        # docker rejects a relative source with exit 125 before the container
        # is ever created -- which reads as nine broken images rather than one
        # missing call to resolve().
        self.root = Path(root).resolve()
        for sub in ("ckpt", "out", "cache", "results", "logs", "staging"):
            (root / sub).mkdir(parents=True, exist_ok=True)

    def ckpt(self, name: str) -> Path:
        return self._sub("ckpt", name)

    def out(self, name: str) -> Path:
        return self._sub("out", name)

    def cache(self, name: str) -> Path:
        return self._sub("cache", name)

    def _sub(self, kind: str, name: str) -> Path:
        path = self.root / kind / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def results(self) -> Path:
        return self.root / "results"

    @property
    def logs(self) -> Path:
        return self.root / "logs"


# --------------------------------------------------------------------------
# commands


def base_images() -> List[str]:
    """The FROM lines of every Dockerfile here, so doctor can verify the tags."""
    found = set()
    for dockerfile in sorted((HERE / "images").glob("*/Dockerfile")):
        for line in dockerfile.read_text().splitlines():
            if line.strip().upper().startswith("FROM "):
                found.add(line.split(None, 1)[1].split(" AS ")[0].strip())
    return sorted(found)


def cmd_doctor(args) -> int:
    """Say what this machine can and cannot do, before anything slow starts."""
    ok = True

    def check(label: str, good: bool, detail: str = "") -> None:
        nonlocal ok
        mark = "ok  " if good else "FAIL"
        print(f"  [{mark}] {label}{(' -- ' + detail) if detail else ''}")
        ok = ok and good

    print("\ndocker")
    docker = shutil.which("docker")
    check("docker on PATH", bool(docker), docker or "install docker")
    daemon = False
    if docker:
        probe = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                               capture_output=True, text=True)
        daemon = probe.returncode == 0
        check("docker daemon reachable", daemon,
              probe.stdout.strip() or probe.stderr.strip()[:80])

    print("\ngpu")
    smi = shutil.which("nvidia-smi")
    check("nvidia-smi on PATH", bool(smi), "" if smi else "CPU-only systems will still run")
    if smi:
        probe = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
             "--format=csv,noheader"], capture_output=True, text=True)
        for line in probe.stdout.strip().splitlines():
            print(f"         {line}")
        print("         CUDA images here pin 11.6 to 12.9; the host driver must")
        print("         be new enough for the highest of those you build.")
    if daemon:
        gpu_probe = subprocess.run(
            ["docker", "run", "--rm", "--gpus", "all", "ubuntu:22.04", "true"],
            capture_output=True, text=True)
        check("docker --gpus all works", gpu_probe.returncode == 0,
              gpu_probe.stderr.strip().splitlines()[-1][:90] if gpu_probe.returncode else "")

    print("\nbenchmark")
    bench = shutil.which("transcription-benchmark")
    check("transcription-benchmark on PATH", bool(bench),
          bench or "pip install -e . from the repository root")

    print("\ndisk")
    usage = shutil.disk_usage(args.work if Path(args.work).exists() else ".")
    free_gb = usage.free / 2**30
    ready = registry.runnable()
    needed = sum(s.approx_gb for s in ready)
    # Layer sharing is real but unmeasurable from here, and BuildKit's cache
    # can transiently double a build, so the headroom asked for is the build
    # cache rather than the images.
    check(f"free space {free_gb:.0f} GB for ~{needed:.0f} GB of images",
          free_gb > needed * 1.3,
          "" if free_gb > needed * 1.3 else
          "tight: build in waves and run `docker builder prune -f` between them")
    if free_gb <= needed * 1.3:
        print("\n         suggested waves, cheapest first (prune between):")
        wave, running = [], 0.0
        for system in sorted(ready, key=lambda s: s.approx_gb):
            if running + system.approx_gb > free_gb * 0.45 and wave:
                print(f"           ./bench.py --only {','.join(wave)} build"
                      f"   (~{running:.0f} GB)")
                wave, running = [], 0.0
            wave.append(system.name)
            running += system.approx_gb
        if wave:
            print(f"           ./bench.py --only {','.join(wave)} build"
                  f"   (~{running:.0f} GB)")
        print("           docker builder prune -f   # between each")

    print("\nbase images")
    print("         (these tags were pinned in an environment with no docker;")
    print("          a wrong one costs a long build before it fails, so check first)")
    for base in sorted(base_images()):
        if not daemon:
            print(f"  [skip]  {base} -- no daemon to ask")
            continue
        probe = subprocess.run(["docker", "manifest", "inspect", base],
                               capture_output=True, text=True)
        check(base, probe.returncode == 0,
              "" if probe.returncode == 0
              else "tag not found; pick a nearby one from the same repository")

    print("\nsystems")
    for system in registry.SYSTEMS:
        flag = {registry.READY: "ready  ", registry.PLANNED: "planned",
                registry.BLOCKED: "blocked"}[system.status]
        gpu = "gpu" if system.gpu else "cpu"
        note = ""
        if system.status == registry.READY and not system.tested:
            note = "  image not yet executed anywhere"
        elif system.status != registry.READY:
            note = "  " + system.notes.split(".")[0].lower()
        print(f"  {flag}  {gpu}  {system.name:<18}{note}")

    print("\nNo image here has been built or run: the environment these were")
    print("written in had no docker daemon. Budget the first build as work,")
    print("and run `transcribe --limit 2` before committing to a whole corpus.")
    return 0 if ok else 1


def cmd_build(args) -> int:
    """Build each image, keeping the output, because "build failed: aubio" is
    not a diagnosis. The log is written per system and its tail printed on
    failure, so the next thing to look at is on screen already.
    """
    work = Work(Path(args.work))
    failures = []
    for system in selected(args):
        # Every system builds. Tagging an upstream image directly would skip
        # this directory's Dockerfile, and with it the adapter -- the container
        # would then run whatever the upstream entrypoint is, which for
        # omnizart meant printing its own help and exiting 2.
        context = HERE / "images" / system.name
        if not (context / "Dockerfile").exists():
            log(f"{system.name}: no Dockerfile at {context}, skipping")
            failures.append(system.name)
            continue
        logfile = work.logs / f"build-{system.name}.log"
        try:
            result = run(["docker", "build", "--progress=plain",
                          "-t", system.tag, str(context)],
                         check=False, dry=args.dry_run, capture=True,
                         timeout=getattr(args, "build_timeout", 3600),
                         tee=None if args.dry_run else logfile)
        except subprocess.TimeoutExpired:
            # A build that waits for input does not fail, it waits. The
            # classic is tzdata asking for a geographic area, which every
            # Dockerfile here now suppresses -- but a timeout is what turns
            # the next one anybody meets into a message instead of an
            # afternoon.
            log(f"{system.name}: build exceeded "
                f"{getattr(args, 'build_timeout', 3600)}s and was killed. "
                "If it was sitting at a prompt, that is a bug in the "
                "Dockerfile, not a slow machine.")
            failures.append(system.name)
            continue
        if not args.dry_run and result.returncode != 0:
            failures.append(system.name)
            tail = (result.stdout or "").splitlines()[-15:]
            if tail:
                log(f"{system.name}: last {len(tail)} lines "
                    f"(full log: {work.logs / f'build-{system.name}.log'})")
                for line in tail:
                    print(f"    {line}")
        if getattr(args, "prune", False):
            # BuildKit's cache can transiently double a build's footprint,
            # which is what runs a nearly-full disk out mid-layer.
            run(["docker", "builder", "prune", "-f"], check=False,
                dry=args.dry_run)
    if failures:
        log(f"build failed: {', '.join(failures)}")
    return 1 if failures else 0


def cmd_fetch(args) -> int:
    work = Work(Path(args.work))
    manual: List[str] = []
    for system in selected(args):
        spec = system.checkpoint
        dest = work.ckpt(system.name)
        if spec is None or spec.kind == "in-image":
            log(f"{system.name}: weights are in the image, nothing to fetch")
            continue
        if spec.kind == "manual":
            if any(dest.iterdir()):
                log(f"{system.name}: {dest} is not empty, assuming it is done")
            else:
                manual.append(f"\n{system.name}:\n{spec.manual_hint}\n  -> put it in {dest}")
            continue
        if spec.kind == "url":
            target = dest / Path(spec.ref).name
            if target.exists() or (spec.unpack and any(dest.iterdir())):
                log(f"{system.name}: already here")
                continue
            result = run(["curl", "-fL", "--retry", "3", "-o", str(target),
                          spec.ref], check=False, dry=args.dry_run)
            if spec.unpack and not args.dry_run and result.returncode == 0:
                import zipfile
                log(f"{system.name}: unpacking {target.name}")
                with zipfile.ZipFile(target) as archive:
                    archive.extractall(dest)
                target.unlink()
        elif spec.kind == "hf":
            run([sys.executable, "-c",
                 "import sys;from huggingface_hub import snapshot_download;"
                 "snapshot_download(repo_id=sys.argv[1], local_dir=sys.argv[2])",
                 spec.ref, str(dest)], check=False, dry=args.dry_run)
    if manual:
        print("\n" + "=" * 72)
        print("These need a human. Nothing else will proceed for them.")
        print("=" * 72 + "".join(manual))
        return 1
    return 0


def cmd_transcribe(args) -> int:
    work = Work(Path(args.work))
    audio_dir = Path(args.audio).resolve()
    if not audio_dir.is_dir():
        print(f"error: no such directory: {audio_dir}", file=sys.stderr)
        return 2

    items = audio_items(audio_dir)
    if not items:
        print(f"error: no audio under {audio_dir}", file=sys.stderr)
        return 2
    mounted = audio_dir
    if args.limit:
        items = items[: args.limit]
        mounted = stage_subset(audio_dir, items, work.root / "staging" / "audio")
        log(f"smoke run: {len(items)} of the corpus, staged at {mounted}")
    log(f"{len(items)} items, {len(list(selected(args)))} systems")

    summary = []
    for system in selected(args):
        summary.append(transcribe_one(system, mounted, len(items), work, args))
    print_summary(summary)
    (work.results / "transcribe-summary.json").write_text(
        json.dumps(summary, indent=2))
    return 0 if all(row["status"] == "ok" for row in summary) else 1


def transcribe_one(system, audio_dir: Path, expected: int, work: Work, args) -> Dict:
    out = work.out(system.name)
    if args.fresh and out.exists():
        shutil.rmtree(out)
        out = work.out(system.name)

    argv = ["docker", "run", "--rm",
            "-u", f"{os.getuid()}:{os.getgid()}",
            "-e", "HOME=/cache",
            "-v", f"{audio_dir}:/audio:ro",
            "-v", f"{out}:/out",
            "-v", f"{work.ckpt(system.name)}:/ckpt:ro",
            "-v", f"{work.cache(system.name)}:/cache"]

    # The adapter is COPYed into the image so it can run standalone, and
    # mounted over that copy here so it is never the stale one. Editing an
    # adapter used to mean remembering to rebuild; forgetting produced
    # failures that looked like the bug you had just fixed still happening.
    adapter = HERE / "images" / system.name / "adapter.py"
    if adapter.exists():
        argv += ["-v", f"{adapter}:/adapter.py:ro"]
    if system.gpu and not args.no_gpu:
        argv += ["--gpus", "all"]
    # Docker gives a container 64 MB of /dev/shm, and a PyTorch DataLoader with
    # workers uses shared memory to hand tensors back to the parent. When it
    # runs out the worker dies on SIGBUS and the traceback blames whichever
    # conv layer happened to be running -- so a container setting reads as a
    # model failure. tmpfs allocates lazily, so a bigger size costs nothing
    # until it is used.
    argv += [f"--shm-size={getattr(args, 'shm_size', '2g')}"]
    # Offline by default: a system that quietly downloads a model at run time
    # is not reproducible, and finding that out here is cheaper than finding it
    # out in six months.
    if not (args.allow_network or system.needs_network):
        argv += ["--network", "none"]
    argv += system.docker_args + [system.tag]

    for flag, value in zip(argv, argv[1:]):
        if flag == "-v":
            source = value.split(":", 1)[0]
            assert Path(source).is_absolute(), (
                f"bind mount source {source!r} is not absolute; docker will "
                "refuse it with exit 125")

    started = time.time()
    logfile = work.logs / f"{system.name}.log"
    if args.dry_run:
        run(argv, dry=True)
        return {"system": system.name, "status": "dry-run"}

    log(f"--- {system.name} ---")
    with logfile.open("w") as handle:
        proc = subprocess.run([str(a) for a in argv], stdout=handle,
                              stderr=subprocess.STDOUT, timeout=args.timeout)
    elapsed = time.time() - started

    written = sorted((out / "midi").rglob("*.mid")) if (out / "midi").is_dir() else []
    status = "ok"
    if proc.returncode != 0:
        status = f"exit {proc.returncode}"
    elif len(written) < expected:
        # A short run is worse than a failed one: the items a system skips are
        # its hardest, and dropping them flatters it.
        status = f"short: {len(written)}/{expected}"

    if proc.returncode != 0:
        tail = logfile.read_text().splitlines()[-12:] if logfile.exists() else []
        if tail:
            log(f"{system.name}: last {len(tail)} lines of {logfile}")
            for line in tail:
                print(f"    {line}")

    record = {
        "system": system.name,
        "title": system.title,
        "status": status,
        "exit_code": proc.returncode,
        "seconds": round(elapsed, 1),
        "expected_items": expected,
        "midi_written": len(written),
        "image": system.tag,
        "image_id": image_id(system.tag),
        "command": " ".join(str(a) for a in argv),
        "audio_dir": str(audio_dir),
        "log": str(logfile),
        "finished": dt.datetime.now().isoformat(timespec="seconds"),
    }
    (out / "run.json").write_text(json.dumps(record, indent=2))
    log(f"{system.name}: {status}, {len(written)} midi, {elapsed:.0f}s")
    return record


def image_id(tag: str) -> str:
    probe = subprocess.run(["docker", "image", "inspect", tag, "--format", "{{.Id}}"],
                           capture_output=True, text=True)
    return probe.stdout.strip() if probe.returncode == 0 else "unknown"


def cmd_score(args) -> int:
    work = Work(Path(args.work))
    scored, skipped = [], []
    for system in selected(args):
        midi = work.out(system.name) / "midi"
        if not midi.is_dir() or not any(midi.rglob("*.mid")):
            skipped.append(system.name)
            continue
        target = work.results / f"{system.name}.json"
        argv = ["transcription-benchmark", args.audio, "--estimates", str(midi),
                "-o", str(target)]
        if args.annotations:
            argv += ["--annotations", args.annotations]
        if args.items:
            argv += ["--items", args.items]
        argv += args.passthrough
        result = run(argv, check=False, dry=args.dry_run)
        if args.dry_run or result.returncode == 0:
            scored.append(system.name)
        else:
            skipped.append(system.name)
    log(f"scored: {', '.join(scored) or 'none'}")
    if skipped:
        log(f"not scored: {', '.join(skipped)}")
    return 0 if scored else 1


def cmd_compare(args) -> int:
    """Every pair, because overlapping intervals are not a comparison.

    Reading a league table of separate confidence intervals double-counts the
    difficulty of each recording. --compare bootstraps the paired difference,
    which is the question actually being asked.
    """
    work = Work(Path(args.work))
    results = sorted(work.results.glob("*.json"))
    results = [r for r in results if r.name != "transcribe-summary.json"]
    if len(results) < 2:
        log(f"need two scored systems to compare, found {len(results)}")
        return 1
    print(f"\n{len(results)} systems, {len(results) * (len(results) - 1) // 2} pairs\n")
    for i, before in enumerate(results):
        for after in results[i + 1:]:
            print(f"\n=== {before.stem} vs {after.stem} ===")
            run(["transcription-benchmark", "--compare", str(before), str(after)],
                check=False, dry=args.dry_run)
    return 0


def cmd_table(args) -> int:
    """One table across every scored system, which is the point of the sweep.

    `compare` bootstraps the paired difference between two systems and is the
    honest way to say one beat another. This is the other thing you want: all
    of them side by side, with the intervals visible so that a table of means
    cannot be read as a ranking.
    """
    work = Work(Path(args.work))
    rows = []
    for path in sorted(work.results.glob("*.json")):
        if path.name in ("transcribe-summary.json", "table.json"):
            continue
        try:
            data = json.loads(path.read_text())
            aggregate = data["aggregate"]
        except (ValueError, KeyError):
            log(f"skipping {path.name}: not a benchmark result")
            continue
        macro = aggregate["macro"]
        rows.append({
            "system": path.stem,
            "items": aggregate["n_items"],
            "reference_notes": aggregate["n_reference_notes"],
            "estimated_notes": aggregate["n_estimated_notes"],
            "con": macro["con_f"], "conp": macro["conp_f"],
            "conpoff": macro["conpoff_f"],
            "octave_error_rate": aggregate.get("octave_error_rate", 0.0),
            "median_best_offset_s": aggregate.get("median_best_offset_s", 0.0),
        })
    if not rows:
        log(f"no scored results in {work.results}; run `score` first")
        return 1

    # By COnP, which is the headline metric: onset and pitch, not offset.
    rows.sort(key=lambda r: r["conp"]["mean"], reverse=True)

    timings = {}
    summary = work.results / "transcribe-summary.json"
    if summary.exists():
        for entry in json.loads(summary.read_text()):
            timings[entry.get("system")] = entry.get("seconds")

    def cell(interval):
        return (f"{interval['mean']:.3f} "
                f"[{interval['low']:.3f}-{interval['high']:.3f}]")

    if args.markdown:
        print("| system | items | COn F | COnP F | COnPOff F | octave err | "
              "median offset | transcribe |")
        print("|---|---:|---|---|---|---:|---:|---:|")
        for r in rows:
            seconds = timings.get(r["system"])
            print(f"| {r['system']} | {r['items']} | {cell(r['con'])} | "
                  f"{cell(r['conp'])} | {cell(r['conpoff'])} | "
                  f"{r['octave_error_rate'] * 100:.1f}% | "
                  f"{r['median_best_offset_s']:+.3f}s | "
                  f"{(str(int(seconds)) + 's') if seconds else '--'} |")
    else:
        print(f"\n{'system':<18}{'COn F':>22}{'COnP F':>22}{'COnPOff F':>22}"
              f"{'oct':>7}{'offset':>9}")
        print("-" * 100)
        for r in rows:
            print(f"{r['system']:<18}{cell(r['con']):>22}{cell(r['conp']):>22}"
                  f"{cell(r['conpoff']):>22}"
                  f"{r['octave_error_rate'] * 100:>6.1f}%"
                  f"{r['median_best_offset_s']:>+9.3f}")
        print("-" * 100)
        print(f"{rows[0]['items']} recordings, "
              f"{rows[0]['reference_notes']} reference notes. "
              f"Macro mean over recordings, 95% bootstrap interval.")
        print("\nSorted by COnP, and the order is not a ranking: intervals "
              "this wide\noverlap freely. Use `compare` for any claim that one "
              "system beats another --\nit bootstraps the paired difference, "
              "which is the question being asked.")
        print("\nRead against the ceiling. Two annotators agree at COnP 0.740 "
              "on vocadito,\nso a system there is at the limit of what those "
              "references can show, and one\nfar above it has a scoring fault "
              "rather than a remarkable model.")

    (work.results / "table.json").write_text(json.dumps(rows, indent=2))
    return 0


def cmd_all(args) -> int:
    for step in (cmd_build, cmd_fetch, cmd_transcribe, cmd_score,
                 cmd_table, cmd_compare):
        code = step(args)
        if code != 0 and step in (cmd_build, cmd_fetch):
            log(f"stopping: {step.__name__} did not complete")
            return code
    return 0


# --------------------------------------------------------------------------


def print_summary(rows: List[Dict]) -> None:
    print("\n" + "-" * 66)
    print(f"{'system':<20}{'status':<18}{'midi':>6}{'seconds':>10}")
    print("-" * 66)
    for row in rows:
        print(f"{row['system']:<20}{row.get('status', '?'):<18}"
              f"{row.get('midi_written', 0):>6}{row.get('seconds', 0):>10}")
    print("-" * 66)


def selected(args):
    if args.only:
        return [registry.by_name(name.strip())
                for name in args.only.split(",") if name.strip()]
    if getattr(args, "include_planned", False):
        return registry.SYSTEMS
    return registry.runnable()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", default="bench-work",
                        help="where images' output, checkpoints and results go")
    parser.add_argument("--only", metavar="NAMES",
                        help="comma-separated systems to restrict to, e.g. "
                             "--only basic-pitch,essentia. Comma-separated "
                             "rather than space-separated so it can precede "
                             "the subcommand without swallowing it.")
    parser.add_argument("--dry-run", action="store_true",
                        help="print every command instead of running it")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="check this machine before anything slow")

    build = sub.add_parser("build", help="build or pull the images")
    build.add_argument("--include-planned", action="store_true")
    build.add_argument("--prune", action="store_true",
                       help="docker builder prune between images, for a tight disk")
    build.add_argument("--build-timeout", type=int, default=3600,
                       help="seconds before a build is assumed stuck (default 3600)")

    sub.add_parser("fetch", help="download checkpoints")

    trans = sub.add_parser("transcribe", help="run every system over the audio")
    trans.add_argument("--audio", required=True)
    trans.add_argument("--limit", type=int, default=None,
                       help="smoke run over the first N items")
    trans.add_argument("--timeout", type=int, default=60 * 60 * 6,
                       help="per-system wall clock limit, seconds")
    trans.add_argument("--no-gpu", action="store_true")
    trans.add_argument("--fresh", action="store_true",
                       help="delete a system's previous output first")
    trans.add_argument("--allow-network", action="store_true",
                       help="containers run with --network none by default")
    trans.add_argument("--shm-size", default="2g",
                       help="/dev/shm per container (default 2g); docker's own "
                            "64m default is too small for DataLoader workers")

    score = sub.add_parser("score", help="score every system's output")
    score.add_argument("--audio", required=True)
    score.add_argument("-a", "--annotations", default=None)
    score.add_argument("--items", default=None, help="a test-split file")
    score.add_argument("passthrough", nargs="*", default=[],
                       help="extra flags passed to transcription-benchmark")

    table = sub.add_parser("table", help="one table across every scored system")
    table.add_argument("--markdown", action="store_true",
                       help="emit a markdown table, for pasting into docs/")

    sub.add_parser("compare", help="paired comparison of every pair")

    every = sub.add_parser("all", help="build, fetch, transcribe, score, compare")
    every.add_argument("--audio", required=True)
    every.add_argument("-a", "--annotations", default=None)
    every.add_argument("--items", default=None)
    every.add_argument("--limit", type=int, default=None)
    every.add_argument("--timeout", type=int, default=60 * 60 * 6)
    every.add_argument("--no-gpu", action="store_true")
    every.add_argument("--fresh", action="store_true")
    every.add_argument("--allow-network", action="store_true")
    every.add_argument("--shm-size", default="2g")
    every.set_defaults(markdown=False)
    every.add_argument("--include-planned", action="store_true")
    every.set_defaults(passthrough=[])

    args = parser.parse_args(argv)
    return {
        "doctor": cmd_doctor, "build": cmd_build, "fetch": cmd_fetch,
        "transcribe": cmd_transcribe, "score": cmd_score,
        "compare": cmd_compare, "table": cmd_table, "all": cmd_all,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
