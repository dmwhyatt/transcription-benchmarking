"""The registry of transcription systems, and how each one is run.

One dataclass per system, and nothing else: no imports of the systems
themselves, no logic that knows what any of them do. Adding a system is adding
an entry here plus a directory under ``images/``, and removing one is deleting
both. The driver in ``bench.py`` reads this and is otherwise ignorant.

Every image honours the same contract, which is what makes the comparison a
comparison rather than ten separate experiments:

    /audio   read-only, the corpus, nested directories preserved
    /ckpt    read-only, whatever ``bench.py fetch`` put there
    /cache   writable, scratch that may be reused between runs
    /out     writable, and the image MUST write:
               /out/midi/<same relative path as the audio>.mid
               /out/adapter.json   {"items": [{"item", "status", "seconds"}]}

Mirroring the audio's relative path matters: M4Singer names every segment
0000.wav inside its own folder, and a flat output directory would collide 700
ways. The benchmark pairs on the stem within the same directory first, so a
mirrored tree pairs exactly and a flat one pairs by luck.
"""

from dataclasses import dataclass, field
from typing import List, Optional

READY = "ready"        # image written here; runnable, though see `tested`
PLANNED = "planned"    # registry entry only, no image yet
BLOCKED = "blocked"    # cannot run unattended without solving something first


@dataclass(frozen=True)
class Checkpoint:
    """Where a system's weights come from, and what to do when that fails."""
    kind: str                 # "hf" | "url" | "in-image" | "manual"
    ref: str = ""             # HF repo id, or a URL
    unpack: bool = False      # treat `ref` as an archive to expand
    manual_hint: str = ""     # printed verbatim when a human must intervene


@dataclass(frozen=True)
class System:
    name: str                 # directory name, image tag, results key
    title: str                # for reports
    licence: str
    image: str = ""           # defaults to bench/<name>
    gpu: bool = False                # request --gpus all
    cpu_ok: bool = True              # will still run without a GPU
    checkpoint: Optional[Checkpoint] = None
    status: str = READY
    tested: bool = False             # has anyone actually run this image?
    notes: str = ""
    # Extra docker args a system genuinely needs. Kept explicit so that a
    # system which needs the network, or more shared memory, has to say so.
    docker_args: List[str] = field(default_factory=list)
    needs_network: bool = False
    # Rough built size in GB. Estimates, not measurements -- nothing here has
    # been built -- and only good enough to order the builds and warn before
    # the disk runs out mid-layer.
    approx_gb: float = 2.0

    @property
    def tag(self) -> str:
        return self.image or f"bench/{self.name}"


SYSTEMS: List[System] = [
    # ---------------------------------------------------------------- ready
    System(
        name="basic-pitch",
        approx_gb=1.5,
        title="Basic Pitch (Spotify, ICASSP 2022)",
        licence="Apache-2.0",
        checkpoint=Checkpoint(kind="in-image"),
        tested=False,
        notes="The only system verified end to end outside Docker: pip "
              "install succeeded and it transcribed the synthetic phrase 8/8. "
              "Polyphonic, so expect simultaneous notes a monophonic "
              "reference does not have.",
    ),
    System(
        name="essentia",
        approx_gb=0.6,
        title="Essentia PredominantPitchMelodia + PitchContourSegmentation",
        licence="AGPL-3.0",
        checkpoint=Checkpoint(kind="in-image"),
        notes="Non-neural control. Verified outside Docker: 8/8 on the "
              "synthetic phrase. AGPL, which matters downstream and not here.",
    ),
    System(
        name="aubio",
        approx_gb=0.4,
        title="aubio notes",
        licence="GPL-3.0",
        checkpoint=Checkpoint(kind="in-image"),
        notes="The floor. Verified outside Docker, where it merged a legato "
              "run into one note and returned 3 of 8. If a system cannot beat "
              "this, something is wrong with the system. Ships no wheels for "
              "any platform, so it compiles from source in a builder stage. "
              "Reads the audio formats its own reader handles, which covers "
              "WAV; see the Dockerfile before widening that.",
    ),
    System(
        name="crepe-notes",
        approx_gb=2.5,
        title="CREPE Notes (Riley and Dixon, SMC 2023)",
        licence="GPL-3.0 + madmom non-commercial",
        checkpoint=Checkpoint(kind="in-image"),
        notes="The image pins the four workarounds the plain install needs: "
              "Cython and numpy<2 before madmom, madmom from git, crepe "
              "without build isolation, and matplotlib, which it imports but "
              "does not declare. Model weights are baked at build time so the "
              "run needs no network.",
    ),
    System(
        name="omnizart",
        approx_gb=4.0,
        title="Omnizart vocal (VOCANO, MCT Lab)",
        licence="MIT",
        checkpoint=Checkpoint(kind="in-image"),
        notes="Builds FROM the upstream image, because pip install omnizart "
              "fails on pyaudio/portaudio.h and that image already solves it. "
              "It is still built rather than pulled: an image without this "
              "directory's adapter in it does not honour the contract.",
    ),
    System(
        name="mirst500",
        approx_gb=7.0,
        title="MIR-ST500 baseline (Wang and Jang, ICASSP 2021)",
        licence="none stated",
        gpu=True,
        checkpoint=Checkpoint(kind="in-image"),
        notes="Weights are committed to the upstream repository, so the "
              "image carries them and fetch does nothing. Source separation "
              "(-s, Spleeter) is off by default: vocadito is already solo "
              "voice. Set SEPARATE=1 for mixed audio.",
    ),
    System(
        name="rosvot",
        approx_gb=8.0,
        title="ROSVOT (Li et al., ACL 2024)",
        licence="MIT",
        gpu=True,
        cpu_ok=False,
        checkpoint=Checkpoint(
            kind="manual",
            manual_hint=(
                "ROSVOT's weights are a single Google Drive zip and Drive "
                "rate-limits scripted downloads.\n"
                "  1. open https://drive.google.com/file/d/"
                "1JNtNT37KiLq9uFQqHk7JFs-3trxd3bRh/view\n"
                "  2. download checkpoints.zip\n"
                "  3. unzip it so that <ckpt-dir>/rosvot/model.pt, "
                "<ckpt-dir>/rwbd/model.pt and <ckpt-dir>/rmvpe/ exist"),
        ),
        notes="The adapter passes --apply_rwbd and --verbose. Both are "
              "load-bearing and neither is obvious: without --verbose "
              "failures are silent, and without --apply_rwbd every item "
              "raises on missing word_durs and the output directory comes "
              "out empty. See docs/benchmarking-rosvot.md.",
    ),
    System(
        name="game",
        approx_gb=11.0,
        title="GAME: Generative Adaptive MIDI Extractor (OpenVPI)",
        licence="MIT",
        gpu=True,
        checkpoint=Checkpoint(
            kind="manual",
            manual_hint=(
                "GAME publishes weights on GitHub releases and discussions.\n"
                "  1. see https://github.com/openvpi/GAME/releases\n"
                "  2. put the .pt file at <ckpt-dir>/model.pt"),
        ),
        notes="Batch-transcribes a directory in one process, which makes it "
              "the cheapest of the singing-specific systems to run. Copies "
              "the audio into a writable tree first, because it writes its "
              "MIDI beside each input and /audio is mounted read-only.",
    ),
    System(
        name="phoneme-informed",
        # Standalone cost. It shares mirst500's pytorch 1.13.1-cuda11.6 base,
        # so building the two back to back costs about this once rather than
        # twice -- but the estimate errs high, because guessing low is what
        # runs a tight disk out halfway through a layer.
        approx_gb=7.0,
        title="Phoneme-informed note-level singing transcription (ICASSP 2023)",
        licence="MIT",
        gpu=True,
        checkpoint=Checkpoint(
            kind="url",
            ref="https://github.com/seyong92/"
                "phoneme-informed-note-level-singing-transcription/releases/"
                "download/0.1.0/model.pt",
        ),
        notes="Takes a --bpm and may quantise against it; the adapter passes "
              "BPM=120 by default. Check whether its offsets land on a grid "
              "before reading anything into COnPOff. Shares mirst500's base "
              "image, so build the two in the same wave on a tight disk.",
    ),

    # -------------------------------------------------------------- planned
    System(
        name="stars",
        title="STARS (Findings of ACL 2025)",
        licence="MIT",
        gpu=True,
        cpu_ok=False,
        status=BLOCKED,
        checkpoint=Checkpoint(kind="hf", ref="verstar/STARS"),
        notes="Blocked, and the survey was too optimistic about it. Its "
              "metadata.json wants word and phoneme sequences per item, and "
              "the helper that produces them (scripts/process_ch.py) is for "
              "Chinese. Resolve before writing the image: can inference run "
              "with words omitted, as ROSVOT can via --apply_rwbd? If not, "
              "vocadito needs a phonemiser and that is a decision, not a "
              "detail.",
    ),
    System(name="some", title="SOME (OpenVPI)", licence="MIT", gpu=True,
           status=PLANNED,
           checkpoint=Checkpoint(kind="manual",
                                 manual_hint="Weights: github.com/openvpi/SOME/releases"),
           notes="Superseded by GAME; run it only to measure the difference."),
    System(name="keums", title="Kum et al. teacher-student (ICASSP 2022)",
           licence="none stated", gpu=True, status=PLANNED,
           checkpoint=Checkpoint(kind="in-image"),
           notes="Keras/TF 2.5 pin is the work. Transcribes polyphonic audio "
                 "directly, so it needs no separation step."),
    System(name="yourmt3", title="YourMT3+ (MLSP 2024)", licence="GPL-3.0",
           gpu=True, cpu_ok=False, status=PLANNED,
           checkpoint=Checkpoint(kind="hf", ref="mimbres/YourMT3"),
           notes="Code for YourMT3+ is pre-release behind a link in issue #2; "
                 "pin whatever you use."),
    System(name="vocalparse", title="VocalParse (2026)", licence="Apache-2.0",
           gpu=True, cpu_ok=False, status=PLANNED,
           checkpoint=Checkpoint(kind="hf", ref="pymaster/VocalParse"),
           notes="Needs a converter: it emits lyrics interleaved with pitch "
                 "and note-value tokens against a predicted BPM, not seconds. "
                 "A tempo error becomes proportional timing error, which "
                 "--align cannot rescue."),
    System(name="musicyolo", title="MusicYOLO (ICASSP 2022)", licence="Apache-2.0",
           gpu=True, cpu_ok=False, status=BLOCKED,
           checkpoint=Checkpoint(kind="manual",
                                 manual_hint="Weights are on Baidu Pan only."),
           notes="Blocked on checkpoint availability outside China, and on a "
                 "torch 1.8 / CUDA 10.2 / apex build."),
    System(name="mt3", title="MT3 (ICLR 2022)", licence="Apache-2.0",
           gpu=True, cpu_ok=False, status=PLANNED,
           checkpoint=Checkpoint(kind="manual",
                                 manual_hint="Checkpoints are on GCS; see the repo's colab."),
           notes="Trained on instrumental data only. Run it to quantify how "
                 "an instrumental model handles voice, not as a contender."),
    System(name="sheetsage", title="Sheet Sage (ISMIR 2022)", licence="MIT",
           gpu=True, cpu_ok=False, status=PLANNED,
           checkpoint=Checkpoint(kind="manual",
                                 manual_hint="./prepare.sh -j, ~14 GB, 12 GB VRAM."),
           notes="Melody is beat-quantised, which will read as timing error "
                 "against references annotated from audio."),
    System(name="svt-speechbrain", title="SVT_SpeechBrain (TOMM 2024)",
           licence="Apache-2.0", gpu=True, cpu_ok=False, status=PLANNED,
           checkpoint=Checkpoint(kind="manual", manual_hint="On request from the authors."),
           notes="Audio-only mode is the relevant one; the video path needs "
                 "N20EM."),
    System(name="tony", title="pYIN note track via sonic-annotator",
           licence="GPL-2.0+", status=PLANNED,
           checkpoint=Checkpoint(kind="in-image"),
           notes="Check for circularity on vocadito first: its annotations "
                 "may have been made in Tony, in which case this measures "
                 "agreement with an editing tool."),
]


def by_name(name: str) -> System:
    for system in SYSTEMS:
        if system.name == name:
            return system
    known = ", ".join(s.name for s in SYSTEMS)
    raise KeyError(f"no system named {name!r}; known: {known}")


def runnable() -> List[System]:
    return [s for s in SYSTEMS if s.status == READY]
