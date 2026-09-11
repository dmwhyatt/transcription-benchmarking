# transcription-benchmarking

Note-level benchmarking for music transcription systems. Point it at a corpus
and a system's output and it reports COn, COnP and COnPOff with confidence
intervals, a paired test for comparing two runs, and enough provenance that the
number can be reproduced a year later.

It knows nothing about any particular transcriber, and that is the point. A
benchmark that imports the system it measures can only ever measure that one.

```shell
transcription-benchmark vocadito/audio \
    --annotations vocadito/annotations \
    --estimates some-system/output/ \
    -o results/some-system.json
```

```text
40 recordings, 3211 reference notes, 3106 transcribed

metric                            P      R      F   95% CI on F
--------------------------------------------------------------------
COn      (onset)              0.871  0.842  0.856   [0.821-0.889]
COnP     (onset+pitch)        0.804  0.777  0.790   [0.749-0.828]
COnPOff  (+offset)            0.612  0.591  0.601   [0.558-0.643]

Macro average over recordings; 95% CI from 2000 bootstrap resamples.
Micro (pooled over all notes): COnP F = 0.798

Octave errors: 1.4% of notes whose onset was found
Median best time offset: +0.004s
```

*(the shape of the report, with made-up numbers -- run it to get real ones)*

## Scoring a system

**The usual way is a directory of files.** Run the system however it wants to
be run, then point `--estimates` at what it wrote — MIDI or CSV, matched to the
audio by name. There is no adapter, no import, and no agreement about
interfaces to negotiate. This is how ROSVOT was scored here without ROSVOT
knowing this package exists, and it is how Basic Pitch, VOCANO or anything else
that writes a file is scored.

```shell
transcription-benchmark AUDIO_DIR --annotations ANNOT_DIR --estimates OUT_DIR
```

**An adapter is for a system you are developing**, where it is worth having the
benchmark call it directly so results can be cached and parameters swept without
re-running the expensive parts. A package registers one through the
`transcription_benchmarking.transcribers` entry point group:

```toml
[project.entry-points."transcription_benchmarking.transcribers"]
mysystem = "mypackage.adapter:MySystem"
```

The object needs one method, and optionally a second:

```python
class MySystem:
    def transcribe(self, audio: Path) -> Sequence[tuple[float, float, float]]:
        """(onset seconds, offset seconds, MIDI pitch) per note."""

    def settings(self) -> dict:
        """Recorded as provenance, and what the cache is keyed on. Optional."""
```

`--list-transcribers` shows what is installed; `--transcriber NAME` runs one.
Nothing is imported until it is asked for, so a system that is not installed is
simply not offered.

## Before believing any score

Two things produce a confident, wrong number, and both are visible in seconds.

**Check what the dataset actually contains.**

```shell
transcription-benchmark --inspect path/to/dataset
```

A file census, the directory layout, and a preview of each kind of annotation
with what the loader made of it. Datasets disagree about whether the second
column is an offset or a duration and whether pitch is MIDI or Hz, so both are
inferred — and **the inference is reported**, because a duration read as an
offset gives notes that start correctly and end immediately, which scores badly
in a way that looks like a poor transcriber rather than a misread file.

**Check what got paired with what.**

```shell
transcription-benchmark path/to/dataset --dry-run
```

Reads no audio. Reports which annotation went with which recording, how it was
matched, and the note, time and pitch ranges read from it. Where a recording has
several annotations the note-level one is chosen and the choice is reported as
`prefix (1 of 4)`; `--annotation-contains notesB` pins a different one.

## The metrics

**COn**, **COnP** and **COnPOff** are the note-transcription measures the
transcription literature reports, computed through `mir_eval` at MIREX
tolerances: an onset within 50 ms, a pitch within 50 cents, an offset within
50 ms or 20% of the reference note's duration. They nest — a note counted in
COnPOff is counted in COnP and in COn. **COnP is the headline.**

Reference pitches are kept as floats rather than rounded, so a reference that
does not quantise is not silently quantised on its behalf.

### Why there are error bars

A single number is not a measurement. The interval comes from a bootstrap
resampled over **recordings**, not notes, because notes within a recording are
not independent: a singer whose vibrato defeats a decoder defeats it for the
whole track. Where the items are segments of longer performances the resampling
is clustered by performance — on M4Singer that widened the interval by 5.4x,
which is the difference between a defensible claim and a flattering one.

Forty recordings support "COnP 0.59, 95% CI 0.54–0.64". They do not support
"0.59 beats 0.58".

### Comparing two systems

Two overlapping confidence intervals do not mean two systems are
indistinguishable. `--compare` scores the recordings both runs share and
bootstraps the *difference*, which is the question actually being asked:

```shell
transcription-benchmark --compare theirs.json ours.json
```

```text
COnP F  +0.234  95% CI [+0.204, +0.265]   better on 40 of 40 recordings
```

*(that one is a real result: two singing transcribers on vocadito's 40
recordings, the same references and the same tolerances on both sides.)*

`--by-metadata vocadito_metadata.csv:language` breaks that down by a column of a
metadata CSV. It turns a story about why one system trails into a measurement: a
deficit that tracks the column is a domain effect, one that does not is the
model. It is worth running before believing your own explanation — the first
language-domain hypothesis tested here died against 0.247 on Mandarin versus
0.254 on English.

## Three corrections, and when they are honest

Some references disagree with the audio in ways that are not the system's fault.
Each of these is recorded in the result and printed in the report, because a
conditional number must not be readable as a plain one.

**`--align`** warps each reference onto its recording before scoring, for
references notated at a nominal tempo rather than transcribed from the audio.
BiMMuDa's MuseScore-notated references drift 0.61 s by the end of a song; scored
as-is they give COnP 0.061, and aligned, 0.331. The warp is fitted to the f0
contour — computed by this package, identically for every system — so it cannot
absorb the differences being measured, and a reference whose warp is not a
plausible clock is refused and reported rather than fitted anyway.

**`--onset-shift`** moves estimated note starts only, leaving ends alone, for a
reference that calls something else the start of a note. M4Singer marks the
syllable including its leading consonant, so its notes run about 66 ms wider
than a system marking the vowel.

**`--time-offset`** shifts whole notes, for a reference offset from its audio by
a constant.

The report searches for the global shift that would maximise COnP and says so if
one helps materially, so a misaligned reference announces itself rather than
presenting as a broken transcriber. It also distinguishes the three cases above
from each other using the sign of the start and end deltas — an earlier version
of that diagnostic classified ROSVOT's wider notes as a clock mismatch and
recommended a correction with the wrong sign, which is exactly the failure this
package exists to prevent.

## The ceiling

No system can be meaningfully scored above the rate at which two people agree
with each other about the same recording.

```shell
transcription-benchmark vocadito/annotations --agreement notesA1 notesA2
```

Measured on vocadito, that ceiling is COn 0.817 / COnP 0.740 / COnPOff 0.642.
It changes what a score means: a system scoring COnP 0.589 there is at about
80% of what these annotations can support, which is a different claim from
"0.589 out of 1.0". The COnPOff figure of 0.642 reproduces the 0.64 published in the vocadito
paper, which is the check that validates this metric stack rather than merely
exercising it.

## Corpora

Readers for CSV, TSV, TXT, MIDI, JSON and JAMS, plus the shapes real corpora
actually ship in:

- `--annotations-json FILE` — one JSON for the whole corpus keyed by recording
  id, including parallel-array forms with durations and no onset column, as
  M4Singer and MIR-ST500 ship them.
- `--pairs FILE` — an explicit audio-to-annotation CSV, for corpora where no
  name matching can work: separated stems all called `lead-vocal.wav` against
  references named by year and rank.
- `--items FILE` — restrict to a published test split. Scoring a model on
  recordings it was trained on is not a result.
- `--sample N` — draw across the whole corpus rather than taking the first N. On
  a corpus laid out one folder per song, `--limit` measures one song and reports
  it as the dataset.

Item ids are built to survive collisions: M4Singer's 20,896 segments are all
named `0000.wav`, `0001.wav` and so on inside their own directories, and naive
stem matching pairs every song's `0000.wav` with one song's annotation. Pairing
prefers the same directory, refuses ambiguous stems rather than guessing, and
warns when an annotation is reused.

## Reproducibility

Every result records which system produced it, that system's own settings, the
seed, the versions of the packages that matter, this repository's commit, and a
SHA-256 digest of the dataset files. Change the data or a dependency and the
digest or the version string changes with it.

`--cache-dir` makes re-scoring instant and is keyed on the system's settings, so
changing a parameter re-transcribes rather than scoring the previous run.

One discipline worth keeping: if parameters are tuned until the benchmark score
improves, that score is no longer an estimate of performance on unseen material
— it is an estimate of how well the parameters fit that benchmark. Tune on one
dataset and report on another, or split one and keep the held-out half unseen.

## Install

```shell
pip install -e .
```

Python 3.9 or newer. No transcriber is a dependency, and none should be.

## Tests

```shell
pytest -q
```

The suite brings its own signals and its own stand-in transcribers, whose errors
are stated rather than measured, so everything the benchmark does to a system's
output is testable without any system installed.

## Credit

The metrics are computed through **[mir_eval](https://github.com/mir-evaluation/mir_eval)**
(Raffel et al., *mir_eval: A Transparent Implementation of Common MIR Metrics*,
ISMIR 2014) at the tolerances used by MIREX's Note Tracking task.
**[librosa](https://librosa.org/)** (McFee et al., SciPy 2015) provides pYIN,
DTW and audio loading, **[pretty_midi](https://github.com/craffel/pretty-midi)**
(Raffel and Ellis, ISMIR 2014) MIDI reading.

Datasets referenced above, each under its own licence and none redistributed
here:

- **vocadito** — Bittner et al., *vocadito: A dataset of solo vocals with f0,
  note, and lyric annotations*, 2021.
- **M4Singer** — Zhang et al., *M4Singer: A Multi-Style, Multi-Singer and
  Musical Score Provided Mandarin Singing Corpus*, NeurIPS 2022.
- **BiMMuDa** — the Billboard Melodic Music Dataset, Bell et al., 2023.
- **MIR-ST500** — Wang and Su, *On the Preparation and Validation of a Large-scale
  Dataset of Singing Transcription*, ICASSP 2021.

**ROSVOT** (Li et al., ACL 2024) is the system scored as a comparison above; it
was run unmodified, from its own repository, and scored here only from the MIDI
it wrote.

## Licence

MIT. See `LICENSE`.
