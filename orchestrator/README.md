# Running every system over the same corpus

The survey in `docs/vocal-transcription-tools.md` ends by saying which systems
are worth scoring. This runs them.

One container per system, each from its own pinned image, all over the same
read-only audio, all writing MIDI under one filename convention. Then the
benchmark reads each output directory through `--estimates` -- the same path a
hand-run system takes, with no special case for anything run from here.

```shell
./bench.py doctor                                  # before anything slow
./bench.py build
./bench.py fetch                                   # prints what needs a human
./bench.py transcribe --audio ~/corpora/vocadito/audio --limit 2   # smoke run
./bench.py transcribe --audio ~/corpora/vocadito/audio
./bench.py score --audio ~/corpora/vocadito/audio -a ~/corpora/vocadito/annotations
./bench.py compare
```

`./bench.py all --audio ... -a ...` does the lot. `--only game,basic-pitch`
restricts any step to named systems; `--dry-run` prints every command instead
of running it.

Nothing here is installed with the package: `pyproject.toml` packages `src/`
only. The benchmark does not import this, this does not import the benchmark,
and neither imports a transcriber.

## Starting from nothing

On a machine that has none of this. About two hours, most of it unattended.

**1. The machine.** Docker, the NVIDIA Container Toolkit, and a driver new
enough for CUDA 12 (`nvidia-smi` prints its maximum top right; 12.x covers
every image here). About 35 GB of disk for the images, plus room for the
corpus. A GPU with 10 GB is enough -- but see the note on contention below,
because a shared card is the one failure that looks like a bug in a model.

**2. The repositories.**

```shell
git clone https://github.com/dmwhyatt/transcription-benchmarking
git clone https://github.com/dmwhyatt/transcpybe          # private; needs your access
cd transcription-benchmarking
python -m venv .venv && . .venv/bin/activate
pip install -e .                      # provides transcription-benchmark, used by `score`
```

**3. The corpus.** vocadito is not redistributed here. Download it from
[Zenodo](https://zenodo.org/records/5578807) and unpack it, giving an `Audio/`
directory of 40 wav files and an `Annotations/` directory beside it. Then look
before trusting it:

```shell
transcription-benchmark --inspect /path/to/vocadito/Annotations
transcription-benchmark /path/to/vocadito/Audio -a /path/to/vocadito/Annotations --dry-run
```

vocadito ships two annotator versions per recording plus f0 contours, and the
loader picks the note-level one by filename hints. The dry run says which file
it paired with each recording; read that line rather than skipping it.

**4. Check the machine before anything slow.**

```shell
cd orchestrator
export TRANSCPYBE_SRC=~/transcpybe
./bench.py doctor
```

It verifies docker, the GPU, whether a container can reach it (trying both
`--gpus all` and the CDI device), the benchmark on PATH, free disk against the
images' sizes, and every Dockerfile's base image tag against the registry. A wrong base tag otherwise costs a long build before
it fails.

**5. Build.** If disk is tight, `doctor` prints a wave plan; otherwise:

```shell
./bench.py build --prune
```

Roughly 35 GB and half an hour. `--prune` clears BuildKit's cache between
images, which is what runs a nearly-full disk out mid-layer.

**6. Checkpoints.**

```shell
./bench.py fetch
```

Everything downloads itself except ROSVOT, whose weights are a Google Drive zip
that Drive rate-limits. `fetch` prints the link and the directory; unzip it
anywhere under that directory and the adapter will find the models at any
depth.

**7. A smoke run before the corpus.**

```shell
./bench.py transcribe --audio /path/to/vocadito/ --limit 2
```

Two recordings through all ten systems, about four minutes. Every system that
is going to fail fails here for the price of a coffee rather than an hour.

**8. The real run, and the scores.**

```shell
./bench.py transcribe --audio /path/to/vocadito/
./bench.py score --audio /path/to/vocadito/Audio -a /path/to/vocadito/Annotations
./bench.py table
./bench.py compare
```

About 70 minutes, of which omnizart is 39.

**9. The transcPybe versions.** Pin them by commit, not by branch: branches
move, and `docs/transcpybe-v1.md` reports a specific commit.

```shell
for v in v1:6fe3e12 v2:fc9a9df v3:70b4df2; do
  label=transcpybe-${v%%:*}; rev=${v##*:}
  ./bench.py --only transcpybe --as "$label" --rev "$rev" build --prune
  ./bench.py --only transcpybe --as "$label" transcribe --audio /path/to/vocadito/
done
./bench.py score --audio /path/to/vocadito/Audio -a /path/to/vocadito/Annotations
./bench.py table
./bench.py compare
```

`--rev` builds each in a detached worktree, so the checkout never has to be
switched and the build cannot quietly measure whichever branch it was left on.
Each build prints the commit it resolved; check it.

**If `doctor` says `--gpus all` does not work** while `nvidia-smi` is fine,
the host driver is not the problem -- containers reach the GPU through the
NVIDIA Container Toolkit, which is separate. On docker 29 that path goes
through CDI, and the giveaway is "failed to discover GPU vendor from CDI":

```shell
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
nvidia-ctk cdi list                  # expect nvidia.com/gpu=all
```

Older docker wants `sudo nvidia-ctk runtime configure --runtime=docker` and a
daemon restart instead.

Generating the spec does not always make `--gpus all` work. Docker 29 resolves
that flag by *discovering* a vendor, and on a machine where discovery misfires
it reports the wrong vendor entirely -- "AMD CDI spec not found" on a box whose
only card is NVIDIA. Naming the device skips discovery:

```shell
docker run --rm --device nvidia.com/gpu=all ubuntu:22.04 true
```

If that works and `--gpus all` does not, nothing is wrong with the toolkit.
`doctor` probes both spellings and tells you which one this machine takes, and
`transcribe` falls back to the CDI device on its own -- it prints a line when
it does -- so no flag is needed. `--gpu-args` overrides the choice if you want
a different one (`--gpu-args "--device nvidia.com/gpu=0"` to pin one card).

**Before a long run on a shared machine, look at the card.** A CUDA OOM
reported by a model is usually somebody else's job holding the memory --
`nvidia-smi` names the process. `transcribe` now prints free and total GPU
memory before each GPU system for this reason.

## What has been run

**The full sweep, on vocadito, 14 September 2026.** Ten systems over forty
recordings. `docs/transcpybe-v1.md` has the result and what it does and does
not support. Two figures reproduced numbers obtained by hand through a
different path -- transcPybe 0.591 against 0.589, ROSVOT 0.262 against 0.262 --
which is the evidence that the orchestration is not moving the measurement.

**Every image here has been built and run at least once**, which was not true
when they were written: all nine of the original Dockerfiles were written in an
environment with no Docker daemon. Getting them green took roughly a dozen
rounds, and the failures are worth knowing because most were environmental
rather than the systems' fault: tzdata prompting for a geographic area and
hanging a build, a 64 MB `/dev/shm` killing a PyTorch DataLoader, images
reaching for the network at run time under `--network none`, checkpoints in
layouts the adapters did not expect, and GPU contention reported as a model
error. Each is now either fixed in the Dockerfile or reported clearly enough to
act on.

**What is still unproven:** the systems marked `planned` in `systems.py` have
no image, and the two marked `blocked` name what stops them.

## The contract

Every image takes the same mounts and writes the same shape. This is what makes
ten systems one comparison.

| Mount | Mode | Meaning |
|---|---|---|
| `/audio` | read-only | the corpus, nested directories preserved |
| `/ckpt` | read-only | whatever `fetch` put there |
| `/cache` | writable | scratch, and `$HOME` |
| `/out` | writable | `midi/<same relative path>.mid`, plus `adapter.json` |

**Mirroring the relative path is load-bearing.** M4Singer calls every segment
`0000.wav` inside its own folder, and a flat output directory collides 700
ways. A mirrored tree pairs on the item id exactly.

Containers run with `--network none` unless a system declares otherwise, so an
image that quietly downloads a model at run time fails here rather than in six
months. Weights are baked at build time where the licence allows.
They also run as the invoking user, so the output is not left owned by root.

## Editing an adapter

`adapter.py` is copied into the image so it can run standalone, and mounted
over that copy at run time so the file on disk is always the one that runs.
Edit an adapter and re-run `transcribe`; no rebuild.

A Dockerfile change is different and does need `build`. The distinction
matters because a stale adapter does not announce itself -- it reproduces the
bug you just fixed, which is indistinguishable from not having fixed it.

## Systems

`./bench.py doctor` prints this live. Nine are ready to build:

| System | GPU | Checkpoints | Note |
|---|---|---|---|
| `transcpybe` | yes | in image | The incumbent. Built from a local checkout, not a clone -- see below. |
| `basic-pitch` | no | in image | The one whose install was verified from scratch. |
| `essentia` | no | none | Non-neural control. AGPL. |
| `aubio` | no | none | The floor. Merges legato runs. |
| `crepe-notes` | no | in image | Five install blockers encoded; see the Dockerfile. |
| `omnizart` | no | `download-checkpoints` | Uses the upstream image; pip install fails on portaudio. |
| `mirst500` | yes | **in image** | Weights are committed upstream. Trained on MIR-ST500 1-400. |
| `rosvot` | yes | manual (Drive) | `--apply_rwbd` and `--verbose` are both load-bearing. |
| `game` | no | automatic | Runs the published ONNX models; upstream ships no ONNX pipeline, so the adapter is one. ~1 GB, not ~11. |
| `phoneme-informed` | yes | release asset | Takes a `--bpm`; check whether it quantises. |

`stars` and `musicyolo` are registered as **blocked**, with the reason in
`systems.py`: STARS wants word and phoneme sequences its Chinese-only helper
produces, and MusicYOLO's weights are on Baidu Pan. Eight more are registered
as planned. Adding one is an entry in `systems.py` plus a directory here.

## Measuring a new version against the old one

Re-running a system overwrites its output and its score, which destroys the
record you want to compare against. `--as` files a run under a different name:

```shell
# the record of v1 already exists; keep it
docker tag bench/transcpybe bench/transcpybe-v1
mv bench-work/out/transcpybe          bench-work/out/transcpybe-v1
mv bench-work/results/transcpybe.json bench-work/results/transcpybe-v1.json

./bench.py --only transcpybe --as transcpybe-v2 --rev origin/some-branch build --prune
./bench.py --only transcpybe --as transcpybe-v2 transcribe --audio ~/vocadito/
./bench.py score --audio ~/vocadito/Audio -a ~/vocadito/Annotations
./bench.py table
./bench.py compare
```

`--rev` takes a branch, tag or commit and builds it in a detached worktree, so
the build does not depend on which branch the checkout happens to be sitting
on. That distinction matters more than it sounds: `git pull` fetches a branch
without switching to it, so a build from the working tree can quietly measure
the previous version under the new name -- succeeding, and being wrong. If the
revision is not local yet, it fetches once and retries.

The label renames the image tag as well, so `bench/transcpybe-v1` survives and
v1 stays re-runnable. Each run records the commit its source was on --
`source_revision` in `run.json`, with `-dirty` if the checkout had uncommitted
changes -- so a row can always be traced back to a version.

`compare` is the point of doing it this way. Two versions of one transcriber
over the same recordings is a paired measurement, and the paired difference is
far tighter than two overlapping intervals: it removes the per-recording
difficulty that both versions share. A change worth keeping shows up there, in
an interval that excludes zero, long before it separates two error bars in the
table.

## A system whose source is private

transcPybe cannot be cloned inside a Docker build, because it is private and a
Dockerfile has no credentials. Its image is built with a local checkout as the
build context instead:

```shell
export TRANSCPYBE_SRC=~/transcpybe     # or keep it at ../transcpybe
./bench.py --only transcpybe build
```

Any other closed system can be added the same way -- a `build_context_env` on
its registry entry and a Dockerfile that `COPY . /src`.

One thing to keep in view while reading its column. transcPybe is the system
this benchmark was built alongside, which makes it the one most at risk of
having been tuned until this number improved. That is not an accusation, it is
the failure mode the repository's own README warns about: a score tuned against
a benchmark measures the tuning. If its parameters have been swept on vocadito,
say so beside the number, or report it on a corpus it was not swept on.

## Checkpoints

`fetch` handles HuggingFace and plain URLs. Two systems need a human, and it
prints exactly what to do and where to put the result. That is not laziness:
Google Drive rate-limits scripted downloads and Baidu Pan is effectively
unavailable outside China, which is a fact about those systems' availability
and is recorded as one in the survey.

## Reading the result

`table` is the one you want first: every scored system side by side, sorted by
COnP, with the bootstrap interval beside each mean so a column of numbers
cannot be misread as a ranking. `--markdown` emits it for pasting into `docs/`.

```shell
./bench.py table
./bench.py table --markdown
```

`compare` runs every pair through `--compare`, which bootstraps the *paired*
difference. Do not read a league table of separate confidence intervals
instead: the difficulty of a recording is shared between two systems, and
comparing separate intervals counts it twice. Nine systems is thirty-six pairs,
and at 95% intervals about one pair in twenty will separate two systems that
are level.

Read every number against the ceiling. On vocadito two annotators agree at
COnP 0.740, so a system at 0.59 is at 80% of what those annotations can
support, and anything reported far above 0.74 is a scoring fault rather than a
remarkable model.

## Known limits

- **No image has been built.** Stated twice on purpose.
- **Containers get 2 GB of /dev/shm**, not docker's 64 MB. A PyTorch
  DataLoader with workers passes tensors through shared memory, and when it
  runs out the worker dies on SIGBUS with a traceback pointing at whichever
  layer was running. `--shm-size` changes it.
- **Timing is wall clock, not a fair speed comparison.** Containers run
  sequentially, but the images differ in how much they do at startup, and a
  batching system like GAME loads its model once where the per-file adapters
  load it every time.
- **`--limit N` takes the first N items**, which on a corpus ordered by song is
  one song. It is for smoke runs. Use the benchmark's own `--sample` for
  anything you intend to quote.
- **Annotation pairing is the corpus's problem, not this tool's.** Where
  references live in a parallel tree with colliding stems, the benchmark
  refuses to guess and reports the items as unpaired; use `--annotations-json`
  or `--pairs`, as `docs/benchmarking-rosvot.md` does.
