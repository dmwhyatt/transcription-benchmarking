# Vocal transcription systems, and which are worth scoring next

ROSVOT was scored here because it was to hand, not because it was the right
comparison. This is the survey that should have come first: what else exists
that turns a sung recording into notes, what it costs to run, and which of them
this benchmark can actually score.

Which of them is most accurate is the question, and answering it is the whole
point of the exercise: every system run over the same recordings, scored
against the same references at the same tolerances, read against the same
inter-annotator ceiling. What cannot be done is answering it from the papers.
ROSVOT reports COnPOff 77.4 on M4Singer, two annotators agree at 64.2 on
vocadito, and those two numbers describe datasets rather than systems. Nothing
below is ranked by accuracy. The accuracy measured since, on five datasets, is
in the README's results table; [What was run](#what-was-run) says which of the
systems below that covers, and why the others were not run.

vocadito is the venue that makes the comparison fair, and that is a checked
claim rather than a hope: **no system in this survey trains on vocadito**. The
evidence is in [Training contamination](#training-contamination) below. What
contamination there is sits on M4Singer and MIR-ST500, which matters when
scoring on those corpora and not when scoring on vocadito.

Surveyed 11 September 2026.

## Method

### Question

Which publicly available systems convert singing audio into note events, and
what does it cost to get each one to write a directory of transcriptions this
benchmark can read?

### Sources

**1. Seed set.** Systems already named in this repository or in the request
that commissioned the survey: ROSVOT, Basic Pitch, VOCANO, CREPE Notes.

**2. Web search.** Seventeen queries, logged below, run 11 September 2026.
`arxiv.org` is blocked by this environment's egress policy, so searches
returned titles, abstracts and result snippets rather than full text.

**3. Citation and link chasing.** Two kinds. Result titles naming a system not
yet on the list were followed up with a targeted query -- this is how the
phoneme-informed model, keums' teacher-student model, SVT_SpeechBrain,
VocalParse and three of the four code-less papers arrived. README links from
included repositories were followed -- VOCANO to Omnizart, SOME to GAME, STARS
to ROSVOT, CREPE Notes to PESTO/PENN/torchcrepe, Tony to pYIN and
sonic-annotator.

**4. Repository inspection.** Every included system's repository was read
directly over anonymous git and `raw.githubusercontent.com`: README, licence
file, dependency manifest, and `git log -1` on the default branch for the
last-commit date.

**5. Installation.** Every included system published to PyPI was installed into
a clean Python 3.11 venv and, where it installed, run on a synthetic sung
phrase with known notes.

### Search log

Queries as issued. "New" lists what each first surfaced that earlier queries
had not.

| # | Query | New |
|---|-------|-----|
| S1 | CREPE Notes new method segmenting pitch contours into discrete notes DAFx 2023 Riley Dixon | crepe_notes repo, SMC (not DAFx) venue |
| S2 | VOCANO note transcription singing voice polyphonic music github ISMIR 2021 Hsu Su | SongTrans, MusicMamba, keums pseudo-label paper |
| S3 | MIR-ST500 singing transcription baseline github york135 | SVT_SpeechBrain, CTC_CE_for_AST, HumTrans, tuneflow plugin, YourMT3+ |
| S4 | SOME Singing-Oriented MIDI Extractor openvpi github vocal to midi | GAME, Vocal2Midi, bill317996/Audio-to-midi |
| S5 | singing voice transcription note-level open source 2025 2026 state of the art github | VocalParse, phoneme-informed paper |
| S6 | CREPE Notes SMC 2023 evaluation datasets Filosax compared against Basic Pitch Omnizart | FiloSax/FiloBass as its evaluation corpora |
| S7 | YourMT3 singing voice transcription vocal stem multi-instrument github mimbres | YourMT3 direct-vocal claim, MLSP 2024 |
| S8 | Omnizart vocal transcription module MCT lab install status maintained | Omnizart module table, Docker image |
| S9 | phoneme-informed note-level singing transcription ICASSP 2023 github seyong92 | seyong92 repo, WhisperMSS |
| S10 | MusicYOLO sight-singing onset offset detection object detection github | MusicYOLO repo, SSVD-v2.0 dataset |
| S11 | STARS unified framework singing transcription alignment refined style annotation github | STARS repo, ACL 2025 Findings |
| S12 | SongTrans unified song transcription alignment lyrics notes github code release | confirmed no code release |
| S13 | sheet sage Donahue lead sheet transcription vocal melody github docker | Sheet Sage resource requirements |
| S14 | WhisperMSS two-stage Mandarin singing transcription Interspeech 2025 code | Cycle FHT Transformer; confirmed no code |
| S15 | vocadito Bittner 2021 f0 note annotations Tony pYIN manual correction | Tony cited in vocadito's references |
| S16 | sonic-annotator pyin vamp plugin batch CLI note transcription CSV | the headless batch route for pYIN |
| S17 | MT3 training datasets Slakh MAESTRO URMP Cerberus GuitarSet MusicNet | MT3's instrumental-only training mix |

### Inclusion criteria

- **I1 -- Note output.** Emits discrete note events (onset, offset, pitch), not
  only a frame-level f0 contour.
- **I2 -- Applicable to voice.** Either trained on singing, or
  instrument-agnostic and usable on a solo vocal stem.
- **I3 -- Publicly obtainable.** Source or binary available to the public,
  *or* published with enough prominence that the absence of code is itself
  worth recording (the "no code found" section).
- **I4 -- Assessable.** Enough documentation to determine language, licence,
  inputs and outputs without running it.

### Exclusion criteria

- **E1 -- f0 estimators without segmentation.** CREPE, pYIN, RMVPE, PESTO,
  PENN, torchcrepe, SPICE, Praat. They fail I1. They appear only as named
  components of systems that do segment.
- **E2 -- Closed or commercial.** Melodyne, AnthemScore, Klangio, Dubler, DAW
  built-in audio-to-MIDI. Excluded by the scoping decision for this survey, not
  because they are irrelevant -- they are what a musician would actually reach
  for, and the survey says nothing about them.
- **E3 -- Inapplicable to voice.** Piano- or drum-specific transcription
  (Onsets and Frames, piano transcription models). Fails I2.
- **E4 -- Not a system.** Datasets (SSVD-v2.0, HumTrans, MIR-ST500 itself),
  and wrappers that add no transcription capability of their own. Recorded
  where they explain a system, not listed as entries. The TuneFlow plugin is
  the borderline case: it is listed, flagged as a wrapper around york135's
  model.

### Screening

Forty-eight candidates were identified. **Twenty-six** met I1-I4 and are
described below (thirteen singing-specific, ten general, three noted but not
pursued); **four** are published without obtainable code; **eighteen** were
excluded under E1-E4 -- eight f0 estimators, five commercial products, one
piano-only model, and four datasets or training-only repositories.

Screening ran in three passes: title and README, then repository inspection,
then installation. Nothing was excluded on the strength of its abstract alone,
and nothing was included on the strength of its README alone -- every included
repository was read.

### Excluded candidates

The eighteen, named individually so each exclusion is arguable rather than
invisible. Several are excluded *and* important: E1 in particular contains the
components most of the included systems are built out of.

| Candidate | By | Reason | Found via |
|---|---|---|---|
| [CREPE](https://github.com/marl/crepe) | E1 | f0 only. The tracker CREPE Notes segments; its accuracy bounds that system from below. | link from crepe_notes |
| pYIN (as an f0 estimator) | E1 | f0 only. Its *note* output comes from the Vamp plugin, which is why Tony is included and this is not. | S16 |
| [RMVPE](https://github.com/yxlllc/RMVPE) | E1 | f0 only. Ships as the pitch stage inside ROSVOT, SOME and STARS. | link from ROSVOT and SOME READMEs |
| [PESTO](https://github.com/SonyCSLParis/pesto) | E1 | f0 only. An alternative CREPE Notes backend. | link from crepe_notes README |
| [PENN](https://github.com/interactiveaudiolab/penn) | E1 | f0 only. Ditto. | link from crepe_notes README |
| [torchcrepe](https://github.com/maxrmorrison/torchcrepe) | E1 | f0 only. Ditto, and the backend this survey fell back to when `crepe` would not build. | link from crepe_notes README |
| SPICE | E1 | f0 only, self-supervised. TF Hub artefact rather than a transcription system. | prior knowledge |
| Praat / Parselmouth | E1 | f0 only. Included here because people do reach for it, and it does not do notes. | prior knowledge |
| Melodyne (Celemony) | E2 | Closed, commercial. The professional default for per-note vocal editing and the strongest omission in this survey. | prior knowledge |
| AnthemScore | E2 | Closed, commercial. | prior knowledge |
| Klangio / Melody Scanner | E2 | Closed, commercial, API and web only. | prior knowledge |
| Dubler 2 (Vochlea) | E2 | Closed, commercial. Real-time voice-to-MIDI controller; a different task (latency over accuracy). | prior knowledge |
| DAW built-ins (Logic, Ableton, Cubase audio-to-MIDI) | E2 | Closed, and not scriptable over a corpus. What a musician actually uses, and unmeasurable here. | prior knowledge |
| Onsets and Frames, ByteDance piano transcription | E3 | Piano-specific. Fails I2. Listed because they are what "AMT" usually means in the literature. | lineage from MT3 |
| [SSVD-v2.0](https://github.com/xk-wang/SSVD-v2.0) | E4 | Dataset, not a system: MusicYOLO's sight-singing training and evaluation data. | S10 |
| [HumTrans](https://github.com/shansongliu/HumTrans) | E4 | Dataset, not a system: humming transcription. Relevant if the task ever widens to humming. | S3 |
| MIR-ST500 | E4 | Dataset, not a system. Already one of this project's corpora. | S3 |
| [Note-Segmentation-SSL](https://github.com/B05901022/Note-Segmentation-SSL) | E4 | VOCANO's training-only repository; no inference path of its own. | link from VOCANO README |

Two of these deserve a second look if the survey's scope ever changes. **E2 is
a scoping decision, not a judgement**: Melodyne is the tool a working musician
would use, and this survey cannot say whether any of the systems below beats
it. And **E1 is not a rejection of the approach** -- an f0 estimator plus a
segmenter is precisely what CREPE Notes is, and what this project's own
transcriber is, so the trackers listed there are components to swap rather than
competitors to beat.

### Threats to validity

**English-language search only.** Much of the singing-transcription ecosystem
is Chinese-language. OpenVPI and MusicYOLO surfaced because they also publish
to GitHub in English; comparable work on Gitee or documented only in Chinese
would not have. This is the most likely source of missed systems.

**No full-text screening.** With `arxiv.org` blocked, a system named only in
the body of a paper -- not in a title, abstract, README or search snippet --
would not have been found. The CREPE Notes paper that prompted the survey is
itself in this category: its reference list was not read.

**Search ranking is not reproducible.** The same seventeen queries on a
different day return a different ordering and may surface different systems.
The repository facts below are reproducible; the discovery process is not.

**Recency skews coverage.** Systems from 2021-2022 were found mainly by
citation chasing rather than search, so older work is covered less evenly than
work from 2024 onward.

## What was run

Fifteen of the twenty-six were run and scored; the results are in the README's
table. The other eleven, and why:

| System | Why it was not run |
|---|---|
| VOCANO | Another version of a system that was run: its README says the work now ships as Omnizart's `vocal` model. |
| basic-pitch-ts | Another version of a system that was run: Basic Pitch's model in TypeScript. |
| NeuralNote | Another version of a system that was run: a plugin wrapping Basic Pitch's model. |
| tuneflow singing-transcription-plugin | Another version of a system that was run: a DAW wrapper around the MIR-ST500 model (york135, ICASSP 2021). |
| Vocal2Midi | Another version of a system that was run: a desktop pipeline around GAME's note extraction, adding lyric recognition and alignment. |
| MusicYOLO | Weights not publicly downloadable: its checkpoints are on Baidu Pan only. |
| SVT_SpeechBrain | Weights not publicly downloadable: its checkpoints are available on request. |
| VocalParse | No timed notes: it writes note values against a predicted tempo, not times in seconds. |
| Sheet Sage | No timed notes: its melody is a beat-quantised lead sheet. |
| MT3 | Not trained on singing: its training mix is instrumental only. |
| Audio-to-midi (bill317996) | Not pursued: a 2019 vocal melody extractor (MSnet) on Python 3.6 and torch 1.0. |

The fifteen run were Phoneme-informed, the MIR-ST500 model, CTC_CE_for_AST,
Tony, YourMT3+, GAME, Omnizart `vocal`, SOME, Kum et al.'s teacher-student
model, Basic Pitch, Essentia, CREPE Notes, ROSVOT, aubio and STARS.

## Singing-specific note transcription

These are trained on singing and predict note events. Language is Python and
the framework PyTorch unless stated.

| System | Licence | Last commit | Writes | Checkpoints | Found via |
|---|---|---|---|---|---|
| [ROSVOT](https://github.com/RickyL-2000/ROSVOT) | MIT | 2024-11-20 | MIDI per item | Google Drive | seed (already scored here) |
| [STARS](https://github.com/gwx314/STARS) | MIT | 2026-08-18 | notes + phoneme alignment | HuggingFace | S11 |
| [GAME](https://github.com/openvpi/GAME) | MIT | 2026-08-30 | MIDI, txt, csv | GitHub releases | link from SOME README |
| [SOME](https://github.com/openvpi/SOME) | MIT | 2026-03-07 | MIDI (float pitch) | GitHub releases | S4 |
| [VOCANO](https://github.com/B05901022/VOCANO) | MIT | 2021-08-09 | MIDI + wav | in repo | seed (named in request) |
| [Omnizart](https://github.com/Music-and-Culture-Technology-Lab/omnizart) `vocal` | MIT | 2026-05-31 | MIDI | `omnizart download-checkpoints` | link from VOCANO README |
| [singing_transcription_ICASSP2021](https://github.com/york135/singing_transcription_ICASSP2021) | none | 2026-03-05 | MIDI | **in repo** | S3 |
| [CTC_CE_for_AST](https://github.com/york135/CTC_CE_for_AST) | none | 2025-03-25 | MIDI | Google Drive | snowball from S3 |
| [phoneme-informed](https://github.com/seyong92/phoneme-informed-note-level-singing-transcription) | MIT | 2023-09-09 | MIDI | Git LFS / release | snowball S5 to S9 |
| [icassp2022-vocal-transcription](https://github.com/keums/icassp2022-vocal-transcription) | none | 2022-05-12 | MIDI | in repo | snowball from S2 |
| [MusicYOLO](https://github.com/itec-hust/MusicYOLO) | Apache-2.0 | 2022-01-29 | onset/offset + pitch | Baidu Pan | S10 |
| [VocalParse](https://github.com/pymaster17/VocalParse) | Apache-2.0 | 2026-06-16 | token sequence | HuggingFace | S5 |
| [SVT_SpeechBrain](https://github.com/guxm2021/SVT_SpeechBrain) | Apache-2.0 | 2024-08-30 | note events | on request | S3 |

**ROSVOT** (Li et al., ACL 2024) was the first one scored, on vocadito in
September 2026. Trained on M4Singer only, in the checkpoint its
authors publish, and it carries M4Singer's annotation convention with it: its
notes arrived 66 ms wider than vocadito's references, 41 ms early at the start.
Everything in this section that trains on M4Singer should be expected to do the
same thing, and that is a prediction the benchmark can test rather than a
caveat to write down.

**STARS** (Findings of ACL 2025) says in its own README that it is built on
ROSVOT. It does transcription, phoneme alignment, vocal-technique tagging and
global style classification in one model, takes the same `metadata.json`
input shape, and ships Chinese and Chinese/English checkpoints on HuggingFace
alongside an RMVPE pitch extractor. Two consequences: the launcher already
written for ROSVOT is most of the launcher for STARS, and if the M4Singer onset
convention is inherited along with the architecture, the same `--onset-shift`
should land on the same 41 ms. Tested by its authors on Python 3.10 / torch
2.4.0 / CUDA 12.8.

**SOME** and **GAME** come out of the DiffSinger/OpenVPI world, where the job
is labelling singing datasets for synthesis rather than publishing F-measures.
That shows in the engineering. SOME reports 9x real time on an i5 CPU and
trains usefully on three hours of data; GAME, its declared successor, takes a
directory and a glob and writes MIDI, txt and csv beside each input --
`python infer.py extract /audio/dir/ -m model.pt --glob *.wav
--output-formats mid,txt,csv`, which is exactly the shape `--estimates` wants.
GAME advertises robustness to reverb, noise and even accompaniment, adjustable
note-presence thresholds, and multilingual segmentation. Both emit non-integer
MIDI pitches, which this benchmark keeps as floats rather than rounding, so
nothing is lost on the way in. GAME is the most recently touched system in this
survey (30 August 2026) and, being outside the academic loop, the least likely
to have trained on anything scored here -- worth confirming against its
technical report before claiming it.

**VOCANO** (Hsu and Su, ISMIR 2021) decomposes the problem the way this
project's own transcriber does: pitch extraction (a patch-based CNN) then note
segmentation (PyramidNet-110 with ShakeDrop, semi-supervised). It is also the
most dormant thing here -- last commit August 2021, installation via NVIDIA
apex and a CUDA 10.1-era `requirements.txt`. Do not fight it: its README says
the work now ships as part of Omnizart, and that is the runnable form.

**Omnizart** `vocal` is VOCANO productionised, in a toolbox that also does
chords, drums, beats and pitched instruments, with a JOSS paper and a Docker
image. `omnizart vocal transcribe audio.wav` is the whole interface, and
`vocal-contour` gives frame-level f0 from the same install if you want the
contour a segmenter could be swapped onto. **It does not install from PyPI
here**: `pip install omnizart` fails building `pyaudio`, which needs
`portaudio.h`. That is a system dependency (`apt install portaudio19-dev`) and
not a fault in the package, but the package mirror is unreachable from this
container so I could not confirm the fix. `docker pull mctlab/omnizart` avoids
the question. ARM macOS is unsupported outright.

**singing_transcription_ICASSP2021** (Wang and Jang) is the MIR-ST500 paper's
own model: an EfficientNet-b0, and unusually, the pretrained checkpoint is
committed to the repository rather than parked on a file host.
`python do_everything.py in.wav out.mid -p model/1005_e_4 -s -on 0.4 -off 0.5`
does the lot, with `-s` running Spleeter first for polyphonic input and `-on`
/`-off` exposing the onset and silence thresholds. Updated as recently as March
2026 (the YouTube downloader moved to yt-dlp). **It trained on MIR-ST500 songs
1-400**, so scoring it on MIR-ST500 means `--items` restricted to 401-500 or
the number is meaningless.

**CTC_CE_for_AST** (Wang and Jang, TASLP 2022) is the same author's follow-up,
adding a CTC loss to the cross-entropy objective. Same `do_everything.py`
interface, MIDI out, but the checkpoints live on Google Drive. One detail in
its README is worth more than the model: its experiments shift MIR-ST500's
labels by +30 ms and it ships the corrected labels, which is independent
confirmation that MIR-ST500's published onsets sit early against its audio.
This benchmark's `--time-offset` exists for exactly that, and its report already
searches for the shift that maximises COnP -- running this repo's `--inspect`
and a dry run against MIR-ST500 should reproduce roughly +30 ms, which would be
a genuine cross-check of the diagnostic rather than a use of it.

**phoneme-informed-note-level-singing-transcription** (Yong et al., ICASSP
2023) is the system to run for reasons other than its score. Its argument is
that singing onsets are hard because they are linguistic -- a note beginning on
a plosive and a note beginning on a vowel are different events -- so it feeds a
phonetic posteriorgram alongside the mel spectrogram. That is the same
phenomenon that made ROSVOT's notes 41 ms early here, approached as a modelling
problem rather than a correction. `python infer.py checkpoints/model.pt in.wav
out.mid --bpm 120` writes MIDI; note that it takes a BPM, so check whether its
output is quantised to that grid before comparing offsets. Checkpoint via Git
LFS, or a release asset if LFS is awkward.

**icassp2022-vocal-transcription** (Kum et al., ICASSP 2022) transcribes
singing from *polyphonic* audio directly, using pseudo-labels transferred from
frame-level pitch estimators and refined by teacher-student self-training. Keras
and TensorFlow 2.5, Linux only, `python singing_transcription.py -i in.wav -o
outdir` with `-ot midi|fps` to choose notes or a frame-level pitch score. The
TF 2.5 pin will be the fight.

**MusicYOLO** (Wang et al., ICASSP 2022 and a 2022 journal extension) is the
most interesting idea and the least available implementation. It draws notes as
bounding boxes on the spectrogram with YOLOX and reads pitch off a spectral
peak search, reporting 94.16% onset F1 on ISMIR2014. But the checkpoints are on
Baidu Pan, and the install is torch 1.8 / CUDA 10.2 plus apex plus a vendored
pycocotools. Note also that it produces onsets, offsets and pitches through a
non-MIDI path, so it needs a converter before `--estimates` will read it.

**VocalParse** (May 2026) is the newest thing in the field and the furthest
from a MIDI file. It extends Qwen3-ASR's vocabulary with ~400 tokens for pitch,
note value and tempo and emits one autoregressive stream interleaving lyrics
with notes -- `感 <P_68> <NOTE_4> 受 <P_60> <NOTE_8> ... <BPM_89>` -- collapsing
ASR, pitch estimation and segmentation into one decoder. A 1.7B checkpoint is
on HuggingFace, Apache-2.0. Two things to understand before budgeting for it:
the output is note *values* (quavers, crotchets) against a predicted global BPM,
not seconds, so converting to the (onset, offset, pitch) triples this benchmark
scores means trusting its tempo estimate, and a tempo error becomes a
proportional timing error across the whole recording. That is a different error
mode from everything else here and `--align` will not rescue it.

**SVT_SpeechBrain** (Gu et al., TOMM 2024) transcribes notes from singing using
self-supervised speech encoders, optionally fusing lip-movement video. It is a
strong single-modal system too, but the multimodal framing means its dataset
(N20EM) and much of its value assume video, and the install is SpeechBrain plus
AV-HuBERT plus torch 1.9/CUDA 11.1. Low priority unless the video angle
interests you.

## General transcription pointed at a vocal stem

None of these are singing systems, though that does not mean none has heard
singing -- Basic Pitch's training mix includes two vocal corpora, and it is
worth knowing which generalists are actually naive about voice before reading
anything into their scores. They are here because a solo vocal is a monophonic
instrument, and because a model that was not built for singing is the control
condition for one that was.

| System | Language | Licence | Last commit | Installs here? | Found via |
|---|---|---|---|---|---|
| [Basic Pitch](https://github.com/spotify/basic-pitch) | Python (TF/CoreML/TFLite/ONNX) | Apache-2.0 | 2025-11-13 | **yes** | seed (named in request) |
| [basic-pitch-ts](https://github.com/spotify/basic-pitch-ts) | TypeScript | Apache-2.0 | 2023-01-10 | npm | link from Basic Pitch README |
| [NeuralNote](https://github.com/DamRsn/NeuralNote) | C++ / JUCE | Apache-2.0 | 2025-01-16 | VST3/AU/standalone | prior knowledge, verified |
| [CREPE Notes](https://github.com/xavriley/crepe_notes) | Python | GPL-3.0 | 2026-03-13 | **no** -- see below | seed (named in request) |
| [YourMT3](https://github.com/mimbres/YourMT3) | Python | GPL-3.0 | 2024-11-29 | clone | S3, then S7 |
| [MT3](https://github.com/magenta/mt3) | Python / JAX / T5X | Apache-2.0 | 2026-07-08 | Colab | lineage from YourMT3 |
| [Sheet Sage](https://github.com/chrisdonahue/sheetsage) | Python + Docker | MIT | 2025-05-13 | Docker | S13 |
| [Essentia](https://github.com/MTG/essentia) | C++ / Python | AGPL-3.0 | 2026-08-27 | **yes** | prior knowledge, verified |
| [aubio](https://github.com/aubio/aubio) | C / Python | GPL-3.0 | 2026-04-10 | **yes** | prior knowledge, verified |
| [Tony](https://github.com/sonic-visualiser/tony) / pYIN | C++ / Qt | GPL-2.0+ | 2024-07-02 | source build | S15, S16 |

**Basic Pitch** (Bittner et al., ICASSP 2022) is the one to run first, for the
dull reason that it works. `pip install basic-pitch` succeeded into a clean
3.11 venv, and `basic-pitch outdir sung_phrase.wav` found all eight synthetic
notes at the right pitches, every onset within 36 ms, writing
`sung_phrase_basic_pitch.mid`. It is polyphonic and instrument-agnostic with
pitch-bend output, has TensorFlow, CoreML, TFLite and ONNX runtimes, and sibling
implementations in TypeScript (`basic-pitch-ts`, npm) and C++ (**NeuralNote**, a
VST3/AU/standalone plugin that wraps the same model with a piano-roll editor and
drag-out MIDI -- the right answer if the comparison you want is against what a
musician would actually reach for).

Two cautions, one of which turned out not to be a problem. Basic Pitch is
polyphonic, so on a vocal it can return simultaneous notes where the reference
has one -- a precision penalty for a capability the task does not want, worth
reporting alongside rather than silently filtering.

The other was the shared authorship: Rachel Bittner wrote both Basic Pitch and
vocadito, which is exactly the shape a contaminated baseline takes. It checks
out clean. Basic Pitch's training pipeline registers five datasets and only
five -- `guitarset`, `ikala`, `maestro`, `medleydb_pitch`, `slakh`, in
`basic_pitch/data/download.py` -- and vocadito appears nowhere in them. It
appears in that repository only as a *test fixture* (`vocadito_10.wav` in the
inference tests) and in `NOTICE` for its licence. Note in passing that two of
the five, iKala and MedleyDB-Pitch, are vocal corpora: Basic Pitch is not a
model that has never heard a singer, it is a model that was never tuned to be
one.

**CREPE Notes** (Riley and Dixon, SMC 2023 -- the paper that prompted this
survey) post-processes CREPE's f0 into notes by combining the gradient of the
pitch contour with the inverse confidence of the estimate, using the peak of
that combined signal as an onset indicator, and falling back to madmom's onset
detector for repeated notes at the same pitch. It reaches its results with 97%
fewer parameters than the deep models it is compared against.

Two things matter for this benchmark. First, **its published evaluation is
instrumental, not vocal**: 90% F-measure on Filosax (saxophone), 74% on ITM GT
Flute 99 (+7% over Basic Pitch), 72% on FiloBass (+10% over Basic Pitch), per
its README. Its README separately advises raising `--min-duration` to 50 ms or
more "for things like vocals", which is as close to a vocal result as the
repository offers. Scoring it on vocadito would be new information, not a
reproduction.

Second, **it does not install as documented**, and I did not get it to run at
all. The chain, on a clean Python 3.11 venv, in order:

1. `pip install crepe-notes[crepe]` fails. madmom's sdist does not declare
   Cython as a build requirement: `ModuleNotFoundError: No module named
   'Cython'`. Preinstalling Cython does not help -- pip's build isolation hides
   it.
2. The README's own fix works:
   `pip install --no-build-isolation git+https://github.com/CPJKU/madmom@main`,
   with `Cython<3` and `numpy<2` present. madmom builds.
3. `crepe` then fails to build, for the `pkg_resources` reason the README
   documents under "macOS / Apple Silicon". It is not Apple-specific; recent
   setuptools drops `pkg_resources` everywhere.
4. `crepe-notes` without the `[crepe]` extra installs, then fails at import on
   `matplotlib`, which it does not declare.
5. With matplotlib and the `torchcrepe` backend installed, it dies in
   `torchaudio.load`: torchaudio 2.11 has handed decoding to TorchCodec, which
   needs FFmpeg shared libraries this container does not have.

Step 5 is environmental and would not bite on a normal workstation; steps 1, 3
and 4 will bite anyone. The likely one-line fix for step 5 is pinning
`torchaudio<2.9`, which still carries its own loader -- **untested**, and stated
as a guess. The PESTO, PENN and torchcrepe backends exist precisely to escape
the TensorFlow-era `crepe` package, so step 3 is avoidable. Budget an
afternoon, not a command.

Licensing is the other catch: CREPE Notes is GPL-3.0, and its madmom dependency
carries a restriction on commercial use that the README says is conferred onto
CREPE Notes as a result.

**YourMT3 / YourMT3+** (Chang et al., MLSP 2024) extends MT3's language-token
decoding with a hierarchical time-frequency attention encoder and a mixture of
experts, and -- the reason it is in a vocal survey -- claims direct singing
voice transcription with no separation pre-processor, benchmarked across ten
datasets. GPL-3.0. The catch is packaging: the README's own link for the
YourMT3+ code points at a comment in issue #2 marked pre-release, and the
friendly path is a HuggingFace Spaces demo rather than a batch CLI.

**MT3** (Gardner et al., ICLR 2022) is the ancestor and is the wrong tool here,
which is worth stating so nobody spends a week finding out. Its training mix is
MAESTROv3, Slakh2100/Cerberus4, GuitarSet, MusicNet and URMP -- piano, guitar,
classical ensembles, synthesised multitrack. No singing. It is also Colab-first
by its authors' own admission ("we do not (easily) support training") and built
on T5X/JAX. Run it to quantify how badly an instrumental model handles a voice,
not as a candidate.

**Sheet Sage** (Donahue et al., ISMIR 2022) transcribes a full lead sheet --
melody plus chords, beat-aligned and key-estimated -- from a mixed recording,
using Jukebox representations and models trained on HookTheory. Melody
transcription is a component rather than the product, and the melody is
beat-quantised, which will read as timing error against references annotated
from audio. Cost: Linux, Docker, ~4 GB of container, and for the Jukebox
features another ~10 GB and a 12 GB GPU.

**Essentia** deserves more attention than a survey of neural models usually
gives it. `pip install essentia` worked immediately, and the classical pipeline
-- `PredominantPitchMelodia` into `PitchContourSegmentation` -- returned all
eight synthetic notes with correct pitches and every onset within 22 ms, in a
couple of seconds of CPU, with no checkpoint to download. It is C++ with Python
bindings from MTG Barcelona. The catch is **AGPL-3.0**, which is a real
constraint if anything here is ever distributed or offered as a service.

**aubio** installed cleanly too, and its note tracker is the honest floor:
`aubio notes` on the same phrase returned **three** notes where there were
eight, holding pitch 62 from 0.03 s to 2.30 s straight through the 64, 65 and 67
above it. That is the classic failure -- onset detection that hears energy but
not pitch change, so a legato phrase becomes one long note. Useful precisely
for that: a system that cannot beat aubio on a corpus has a problem. Note it
prints text triples rather than MIDI, so it needs a converter.

**Tony** (Mauch et al.) is the odd one out: a GUI for *computer-aided* melody
annotation rather than an automatic system, built on pYIN and the Sonic
Visualiser libraries, GPL-2.0+, still maintained (July 2024). Its automatic
component runs headless -- the pYIN Vamp plugin under `sonic-annotator` will
batch-extract a note track to CSV, which `--estimates` reads directly. **Check
for circularity before scoring it on vocadito**: vocadito's paper cites Mauch et
al.'s Tony paper among its references, and if its note annotations were made
with Tony then measuring Tony against them measures agreement with an editing
tool, not transcription accuracy. The vocadito technical report will say; this
is a flag, not a finding.

Three more met the criteria and were not pursued, listed so the exclusion is
visible rather than silent: [bill317996/Audio-to-midi](https://github.com/bill317996/Audio-to-midi)
(MIT, melody extraction via MSnet, python 3.6 / torch 1.0, 2019-era),
[tuneflow/singing-transcription-plugin](https://github.com/tuneflow/singing-transcription-plugin)
(a DAW wrapper around york135's ICASSP 2021 model rather than a system of its
own), and [Xiantaidu/Vocal2Midi](https://github.com/Xiantaidu/Vocal2Midi),
a one-click vocal MIDI extraction and lyric injection tool that surfaced in S4
and which I did not assess beyond its description.

## Published, no code found

Each of these was searched for by name plus "github" and "code"; none surfaced a
repository. Listed so the next person does not repeat the search.

- **SongTrans** (Alibaba et al., 2024) -- joint lyric and note transcription
  with alignment, autoregressive word/duration module plus non-autoregressive
  pitch module.
- **WhisperMSS** (Interspeech 2025) -- two-stage Mandarin singing transcription
  on pretrained models.
- **MusicMamba** (2025) -- a Mamba-based singing transcription model.
- **Cycle Frequency-Harmonic-Time Transformer** (2024) -- note-level singing
  voice transcription.

## Hazards that apply to the whole list

### Training contamination

**No system in this survey trains on vocadito**, which is why vocadito is where
the comparison should be run. What was checked, and how:

| System | Trains on | Source of the claim |
|---|---|---|
| Basic Pitch | GuitarSet, iKala, MAESTRO, MedleyDB-Pitch, Slakh | **read from source** -- the dataset registry in `basic_pitch/data/download.py` |
| ROSVOT | M4Singer | its README, for the published checkpoint |
| york135 x2 | MIR-ST500 songs 1-400 | its README |
| YourMT3+ | ten datasets; singing from MIR-ST500 and CMedia | paper, via search (repo code is pre-release) |
| MT3 | MAESTROv3, Slakh2100/Cerberus4, GuitarSet, MusicNet, URMP | paper, via search -- instrumental only |
| CREPE Notes | nothing; it is post-processing over CREPE | its README and method |
| STARS | Chinese / bilingual singing corpora | **not verified** -- assume M4Singer-like |
| SOME, GAME | OpenVPI community data | **not verified** -- check the technical report |

Two of this project's four corpora *are* contaminated, which matters the moment
you score on them rather than on vocadito. M4Singer trained ROSVOT and probably
STARS. MIR-ST500 songs 1-400 trained both york135 models and fed YourMT3+.
`--items` exists for published test splits and should be the default there, not
something remembered.

The three unverified rows are the honest gaps. None of them threatens a
vocadito comparison -- vocadito is 40 excerpts released in 2021 as an
evaluation set and appears in no training pipeline examined -- but each should
be pinned down before quoting a number on M4Singer or MIR-ST500.

### Annotation convention, again

The 41 ms that `--onset-shift` corrected for ROSVOT is not a ROSVOT bug; it is
M4Singer's definition of where a note starts (the syllable, including its
leading consonant) travelling with the model. Expect it from every
M4Singer-trained system, expect it not to appear in systems trained on
pitch-annotated corpora, and let the report's own diagnostic say which case
each one is rather than assuming.

### Where checkpoints live

This is a real axis of availability, not an inconvenience. In repository
(york135 ICASSP2021, keums, VOCANO) is best; GitHub releases (SOME, GAME,
phoneme-informed) is fine; HuggingFace (STARS, VocalParse) is fine; Google
Drive (ROSVOT, CTC_CE_for_AST) rots and rate-limits; Baidu Pan (MusicYOLO) is
effectively unavailable outside China. A system whose weights you cannot fetch
is not a baseline.

### Licences that constrain more than the code

CREPE Notes is GPL-3.0 *and* inherits madmom's non-commercial restriction.
Essentia is AGPL-3.0. YourMT3 and Tony are GPL. Three of the singing-specific
repositories -- york135's two and keums' -- ship **no licence file at all**,
which means no grant of rights, not "do as you like": fine for measuring
privately, not for anything downstream.

### Filename pairing

`pair_estimates` matches an estimate to an item by exact stem first, then by a
prefix followed by `_`, `-` or `.`. Basic Pitch's
`sung_phrase_basic_pitch.mid` and CREPE Notes'
`sung_phrase.crepe.transcription.mid` both pair through the prefix rule, so
neither needs renaming -- but the pairing is reported as non-exact, and that
line in the report is worth reading rather than skipping. Systems that write
one file per directory, or number their outputs, will need renaming before
`--estimates` sees them.

### What the smoke test does not tell you

Basic Pitch and Essentia both scored 8/8 on a synthetic phrase with clean
harmonics and a steady 5.2 Hz vibrato. vocadito is untrained singers on phone
microphones in seven languages. The agreement here means only that the
plumbing works, which is all a survey can establish. The ordering is a
question for the benchmark, on the same 40 recordings, against the same
references, read against the 0.740 COnP two annotators manage between them.
