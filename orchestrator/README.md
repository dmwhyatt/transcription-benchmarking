# Running the systems on a common corpus

The orchestrator runs the systems selected in the survey (`docs/vocal-transcription-tools.md`). Each system runs in
its own container, built from a pinned image, on the same read-only audio, and writes MIDI under a common naming
convention. The benchmark then reads each output directory through `--estimates`, exactly as it reads the output of a
system run by hand.

```shell
./bench.py doctor                                  # check the machine
./bench.py build                                   # build the images
./bench.py fetch                                   # download checkpoints; lists those that need a manual download
./bench.py transcribe --audio ~/corpora/vocadito/Audio --limit 2   # trial run on two recordings
./bench.py transcribe --audio ~/corpora/vocadito/Audio
./bench.py score --audio ~/corpora/vocadito/Audio -a ~/corpora/vocadito/Annotations
./bench.py table
./bench.py compare
```

- `./bench.py all --audio ... -a ...` runs every step.
- `--only game,basic-pitch` restricts any step to the named systems.
- `--dry-run` prints the commands without running them.

The orchestrator is not installed with the package, which contains `src/` only. Neither the orchestrator nor the
benchmark imports any transcription system.

## Setup

### 1. Requirements

- **Software:** Docker, the NVIDIA Container Toolkit, and a driver that supports CUDA 12 (`nvidia-smi` reports the
  highest supported version).
- **Disk:** about 35 GB for the images, plus space for the corpus.
- **GPU:** one with 10 GB of memory is sufficient, provided no other process is using it (see
  [GPU access](#gpu-access)).

### 2. Repositories

```shell
git clone https://github.com/dmwhyatt/transcription-benchmarking
git clone https://github.com/dmwhyatt/transcPybe transcpybe
cd transcription-benchmarking
python -m venv .venv && . .venv/bin/activate
pip install -e .                      # provides transcription-benchmark, which `score` uses
```

### 3. Corpus

vocadito is not redistributed here.
1. Download it from [Zenodo](https://zenodo.org/records/5578807) and unpack it. This gives an `Audio/` directory of
   40 WAV files and an `Annotations/` directory beside it.
2. Check how the annotations are read before scoring:

```shell
transcription-benchmark --inspect /path/to/vocadito/Annotations
transcription-benchmark /path/to/vocadito/Audio -a /path/to/vocadito/Annotations --dry-run
```

vocadito provides two annotators' versions of each recording, as well as f0 contours, and the loader selects the
note-level files by their names. The dry run reports which file was paired with each recording.

### 4. Checking the machine

```shell
cd orchestrator
export TRANSCPYBE_SRC=~/transcpybe
./bench.py doctor
```

`doctor` checks:
- Docker and the GPU, and whether a container can reach the GPU, through `--gpus all` and through the CDI device;
- that the benchmark is on the `PATH`;
- free disk space against the images' sizes;
- each Dockerfile's base image against its registry, since an incorrect base image otherwise fails only after a long
  build.

### 5. Building the images

```shell
./bench.py build --prune
```

`--prune` clears BuildKit's cache between images, which prevents a nearly full disk from filling during a build. If
disk space is limited, `doctor` proposes building in stages.

### 6. Checkpoints

```shell
./bench.py fetch
```

`fetch` downloads checkpoints from Hugging Face and direct URLs. Some systems' weights must be downloaded manually,
because Google Drive limits scripted downloads: among the systems evaluated, these are ROSVOT, STARS, SOME and CTC-CE.
For each, `fetch` prints the link and the directory in which to place the files. Adapters find their models at any
depth below that directory.

### 7. A trial run

```shell
./bench.py transcribe --audio /path/to/vocadito/Audio --limit 2
```

Running every system on two recordings first exposes failures before the full run.

### 8. The full run and the scores

```shell
./bench.py transcribe --audio /path/to/vocadito/Audio
./bench.py score --audio /path/to/vocadito/Audio -a /path/to/vocadito/Annotations
./bench.py table
./bench.py compare
```

### GPU access

**If `doctor` reports that `--gpus all` does not work although `nvidia-smi` does,** the host driver is not at fault:
containers reach the GPU through the NVIDIA Container Toolkit. With Docker 29, that route uses CDI, and the error
"failed to discover GPU vendor from CDI" indicates a missing specification:

```shell
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
nvidia-ctk cdi list                  # expect nvidia.com/gpu=all
```

Older versions of Docker require `sudo nvidia-ctk runtime configure --runtime=docker` and a restart of the daemon
instead.

**If `--gpus all` still fails,** the cause may be vendor discovery. Docker 29 resolves that flag by discovering a
vendor, and on some machines it reports the wrong one (for example, "AMD CDI spec not found" on a machine with only an
NVIDIA card). Naming the device avoids discovery:

```shell
docker run --rm --device nvidia.com/gpu=all ubuntu:22.04 true
```

- **`doctor`** tests both forms and reports which one the machine accepts.
- **`transcribe`** falls back to the CDI device automatically, and says when it does.
- **`--gpu-args`** overrides the choice, for example `--gpu-args "--device nvidia.com/gpu=0"` to select one card.

**On a shared machine, check the GPU before a long run.** An out-of-memory error reported by a model is usually caused
by another process holding the memory, which `nvidia-smi` identifies. `transcribe` prints the free and total GPU memory
before each GPU system.

## The container interface

Every image takes the same mounts and writes output of the same form:

| Mount | Mode | Contents |
|---|---|---|
| `/audio` | read-only | the corpus, with its directory structure preserved |
| `/ckpt` | read-only | the checkpoints placed by `fetch` |
| `/cache` | writable | scratch space, and `$HOME` |
| `/out` | writable | `midi/<same relative path>.mid`, and `adapter.json` |

Output paths mirror the input paths because some corpora reuse file names in different directories: M4Singer names
every segment `0000.wav`, `0001.wav` and so on within its own folder, so a flat output directory would produce
collisions. A mirrored tree pairs each output with its recording exactly.

- **Network:** containers run with `--network none` unless a system declares otherwise, so an image that attempts to
  download a model at run time fails immediately.
- **Weights:** included in the image at build time where the licence permits.
- **User:** containers run as the invoking user, so output files are not owned by root.

## Editing an adapter

Each system's `adapter.py` is copied into its image, so that the image can run on its own. At run time, the file on
disk is mounted over that copy, so an edited adapter takes effect on the next `transcribe` without a rebuild. A change
to a Dockerfile, by contrast, requires `build`.

## Systems

`./bench.py doctor` prints the current registry from `systems.py`. It has 21 entries:

- **Ready (16):** transcPybe and the fifteen systems evaluated in the README.
- **Planned (4):** VocalParse, MT3, Sheet Sage and SVT_SpeechBrain.
- **Blocked (1):** MusicYOLO, whose weights are distributed only through Baidu Pan.

Each entry records the system's licence, whether it uses a GPU, how its checkpoints are obtained, and notes on how it
is run. Adding a system requires an entry in `systems.py` and a directory under `images/` containing a Dockerfile and
an adapter. Where a system's results depend on decisions specific to this benchmark, its directory includes a
`NOTES.md`: STARS, Tony and YourMT3+.

## Comparing two versions of a system

Running a system again overwrites its output and its scores. `--as` stores a run under a different name, so that two
versions can be compared:

```shell
./bench.py --only transcpybe --as transcpybe-new --rev <commit> build --prune
./bench.py --only transcpybe --as transcpybe-new transcribe --audio /path/to/vocadito/Audio
./bench.py score --audio /path/to/vocadito/Audio -a /path/to/vocadito/Annotations
./bench.py compare
```

- **`--rev`** takes a branch, tag or commit and builds it in a detached worktree. The build therefore does not depend
  on which branch the checkout happens to be on, and it reports the commit it resolved.
- **`--as`** also renames the image, so the earlier version remains available.
- **Provenance:** each run records the commit of its source (`source_revision` in `run.json`, with `-dirty` if the
  checkout had uncommitted changes).

`compare` estimates the paired difference between the two versions over the same recordings. This removes the
variation in difficulty between recordings that both versions share, so it detects a real difference long before two
separate confidence intervals stop overlapping.

## Systems built from a local checkout

transcPybe's image is built with a local checkout as its build context, rather than by cloning inside the Docker
build:

```shell
export TRANSCPYBE_SRC=~/transcpybe     # or place the checkout at ../transcpybe
./bench.py --only transcpybe build
```

This allows any revision to be measured, including uncommitted work. Other systems can be built the same way: give
the registry entry a `build_context_env`, and use a Dockerfile that copies the build context (`COPY . /src`).

transcPybe was developed alongside this benchmark. Its version 2 settings were selected on vocadito, Molina and the
RWC-P development set, as the README's results notes state, so its scores on those datasets are not estimates of
performance on unseen recordings.

## Reading the results

`table` lists every scored system with the bootstrap interval beside each mean. `--markdown` formats it for
documentation.

```shell
./bench.py table
./bench.py table --markdown
```

- **Sort order:** the table is sorted by COnP by default. `--sort conpoff` sorts by COnPOff, the metric reported in
  the README, and `con`, `octave` and `name` are also available. Every metric sorts from best to worst, including
  octave errors.
- **Pairwise comparisons:** `compare` runs every pair of systems through the benchmark's `--compare`, which estimates
  the paired difference. This is preferable to comparing separate confidence intervals, which count the shared
  difficulty of each recording twice. With many systems there are many pairs, and at 95% about one pair in twenty will
  appear to differ when the two systems perform equally.
- **Relative to annotator agreement:** `table --percent` expresses each score as a proportion of the agreement between
  two annotators of the same corpus. That agreement must first be measured on the corpus being scored:

```shell
./bench.py ceiling -a /path/to/vocadito/Annotations     # writes results/ceiling.json
./bench.py table --percent --markdown
```

The agreement is measured rather than fixed, because vocadito's value (COnPOff 0.642) would be the wrong reference
for any other corpus. Without `results/ceiling.json`, `--percent` explains how to create it. `--tag-a` and `--tag-b`
set the annotators' file-name tags, which default to vocadito's `notesA1` and `notesA2`. The percentages divide by the
point estimate of the agreement, so their intervals reflect each system's uncertainty but not that of the agreement.

## Limitations

- **Shared memory.** Containers receive 2 GB of `/dev/shm`, rather than Docker's default of 64 MB. A PyTorch
  DataLoader with worker processes passes tensors through shared memory, and fails with SIGBUS when it is exhausted.
  `--shm-size` changes the allocation.
- **Timing.** The times recorded by `transcribe` are wall-clock times and do not compare speed fairly. Images differ
  in how much work they do at start-up, and a system that processes a batch loads its model once, whereas a per-file
  adapter loads it for every file. The README's timing columns were measured separately, with model loading included.
- **`--limit N`.** This takes the first N recordings, which on a corpus ordered by song may all come from one song. It
  is intended for trial runs; the benchmark's `--sample` draws across the corpus.
- **Pairing.** Where references are stored in a parallel tree with repeated file names, the benchmark reports the
  affected recordings as unpaired rather than guessing. `--annotations-json` or `--pairs` resolves this.
