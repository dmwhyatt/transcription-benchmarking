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

## What has actually been run, and what has not

Being direct about this, because the distinction is the difference between a
tool and a plan.

**Verified end to end, outside Docker.** The `basic-pitch`, `essentia` and
`aubio` adapters were run against a nested corpus that reproduces the
stem-collision case, and their output was scored through the real
`transcription-benchmark` CLI. Basic Pitch and Essentia scored 1.000 on a
synthetic phrase; aubio scored COnP 0.182, having merged a legato run into one
note. That is the whole chain -- adapter, naming, pairing, metrics -- working.

**Not run at all: every Docker image in this directory.** The environment they
were written in had no Docker daemon, so not one has been built. The Python
inside them is exercised; the layers around it are not. Expect the first build
of each to need work, and run `transcribe --limit 2` before committing a whole
corpus to any of them.

The install recipes are not guesses, though. Each was derived by hitting the
failures in a clean venv and recording what got past them -- the `crepe-notes`
Dockerfile in particular encodes five separate blockers, the last of which
(`numpy>=2.0` breaking madmom's compiled extensions) was confirmed and its fix
verified by import.

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

## Checkpoints

`fetch` handles HuggingFace and plain URLs. Two systems need a human, and it
prints exactly what to do and where to put the result. That is not laziness:
Google Drive rate-limits scripted downloads and Baidu Pan is effectively
unavailable outside China, which is a fact about those systems' availability
and is recorded as one in the survey.

## Reading the result

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
