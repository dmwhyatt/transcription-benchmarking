# Vocal transcription systems, and which are worth scoring next

ROSVOT was scored here because it was to hand, not because it was the right
comparison. This is the survey that should have come first: what else exists
that turns a sung recording into notes, what it costs to run, and which of them
this benchmark can actually score.

The question a survey like this usually answers -- which system is most
accurate -- is the one it must not answer. Published figures compare datasets:
ROSVOT reports COnPOff 77.4 on M4Singer, two humans agree at 64.2 on vocadito,
and neither number says which model is better. So nothing below is ranked by
accuracy. Systems are ranked by whether you can get them to write a directory
of MIDI files, because that is the step between a paper and a measurement.

Surveyed 11 September 2026.

## How this was compiled, and what that is worth

Three channels, in decreasing order of trust.

**The repositories themselves.** Every licence, language, output format and
last-commit date below was read from the repository on 11 September 2026 --
anonymous `git` reads and `raw.githubusercontent.com`, not from a paper's claim
about its own code. Last-commit dates are the default branch's head.

**A clean-venv install test.** Where a system is on PyPI, it was installed into
a fresh Python 3.11 venv and, if it installed, run on a synthetic sung phrase:
eight notes, 5.6 s, 5.2 Hz vibrato, a 40 ms attack and a legato slur, generated
with known onsets and pitches. This is a smoke test and nothing more. It says
whether a system installs and emits notes at all; it says nothing about
accuracy, because eight synthetic notes are not a corpus and a system that
nails them can still fail on a phone recording of an untrained singer. It is
reported because "available" is otherwise a README's word for itself, and two
of the five packages tested do not install as documented.

**Search, for the literature.** `arxiv.org` is blocked by this environment's
egress policy, so no paper below was read in full from here -- including the
CREPE Notes paper that prompted the survey. Claims about a paper's contents are
attributed to the repository's own README or to a search result, and marked
where that matters. Anything resting on a PDF I could not open is flagged
rather than asserted.

What none of this establishes: no system below has been scored on real audio
here. There is no corpus in this container.

## The shortlist

Ranked by how cheaply each becomes a number in this benchmark, not by how good
it is.

| # | System | Why it is next | Cost to run |
|---|--------|----------------|-------------|
| 1 | **Basic Pitch** | Installed and ran here, first try. Instrument-agnostic, so it is the generalist floor every singing-specific model should beat. Also the baseline CREPE Notes measures itself against. | `pip install basic-pitch` |
| 2 | **GAME** (OpenVPI) | The most recent singing-specific system that transcribes a whole directory to MIDI in one command, MIT, explicitly built for separated or noisy vocals. Not trained on any corpus here. | clone + checkpoint from releases |
| 3 | **MIR-ST500 baseline** (york135) | Pretrained weights committed *in the repository* -- no Drive link, no Baidu. One command per file, MIDI out. The natural representative of the MIR-ST500 line of work. | clone + `do_everything.py` |
| 4 | **STARS** | ROSVOT's successor, built on ROSVOT's code by an overlapping group. The `metadata.json` runner in `docs/benchmarking-rosvot.md` transfers almost unchanged. | clone + HuggingFace checkpoints |
| 5 | **Essentia** `PitchContourSegmentation` | Zero-friction non-neural floor; got all eight synthetic notes right. Worth having so "better than a 2013 signal-processing pipeline" is a measured claim. | `pip install essentia` |
| 6 | **Phoneme-informed** (seyong92) | Its whole thesis is the onset-convention problem that cost ROSVOT 0.09 COnP here. High diagnostic value regardless of where it scores. | clone + Git LFS checkpoint |
| 7 | **CREPE Notes** | Architecturally the closest cousin to an f0-tracker-plus-segmenter, so it measures whether this pipeline's shape or its details are doing the work. Four install blockers; not run here. | an afternoon |

Below that line: **Omnizart** (`vocal`) via its Docker image since pip fails,
**YourMT3+** if you want a multi-instrument model that claims direct vocal
transcription, and **VocalParse** if you are willing to write a token-sequence
to MIDI converter for a 1.7B checkpoint.

## Singing-specific note transcription

These are trained on singing and predict note events. Language is Python and
the framework PyTorch unless stated.

| System | Licence | Last commit | Writes | Checkpoints |
|---|---|---|---|---|
| [ROSVOT](https://github.com/RickyL-2000/ROSVOT) | MIT | 2024-11-20 | MIDI per item | Google Drive |
| [STARS](https://github.com/gwx314/STARS) | MIT | 2026-08-18 | notes + phoneme alignment | HuggingFace |
| [GAME](https://github.com/openvpi/GAME) | MIT | 2026-08-30 | MIDI, txt, csv | GitHub releases |
| [SOME](https://github.com/openvpi/SOME) | MIT | 2026-03-07 | MIDI (float pitch) | GitHub releases |
| [VOCANO](https://github.com/B05901022/VOCANO) | MIT | 2021-08-09 | MIDI + wav | in repo |
| [Omnizart](https://github.com/Music-and-Culture-Technology-Lab/omnizart) `vocal` | MIT | 2026-05-31 | MIDI | `omnizart download-checkpoints` |
| [singing_transcription_ICASSP2021](https://github.com/york135/singing_transcription_ICASSP2021) | none | 2026-03-05 | MIDI | **in repo** |
| [CTC_CE_for_AST](https://github.com/york135/CTC_CE_for_AST) | none | 2025-03-25 | MIDI | Google Drive |
| [phoneme-informed](https://github.com/seyong92/phoneme-informed-note-level-singing-transcription) | MIT | 2023-09-09 | MIDI | Git LFS / release |
| [icassp2022-vocal-transcription](https://github.com/keums/icassp2022-vocal-transcription) | none | 2022-05-12 | MIDI | in repo |
| [MusicYOLO](https://github.com/itec-hust/MusicYOLO) | Apache-2.0 | 2022-01-29 | onset/offset + pitch | Baidu Pan |
| [VocalParse](https://github.com/pymaster17/VocalParse) | Apache-2.0 | 2026-06-16 | token sequence | HuggingFace |
| [SVT_SpeechBrain](https://github.com/guxm2021/SVT_SpeechBrain) | Apache-2.0 | 2024-08-30 | note events | on request |

**ROSVOT** (Li et al., ACL 2024) is the one already scored -- see
`docs/benchmarking-rosvot.md`. Trained on M4Singer only, in the checkpoint its
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

None of these are singing systems. They are here because a solo vocal is a
monophonic instrument, and because a generalist that has never seen a singer is
the honest floor for a specialist that has.

| System | Language | Licence | Last commit | Installs here? |
|---|---|---|---|---|
| [Basic Pitch](https://github.com/spotify/basic-pitch) | Python (TF/CoreML/TFLite/ONNX) | Apache-2.0 | 2025-11-13 | **yes** |
| [basic-pitch-ts](https://github.com/spotify/basic-pitch-ts) | TypeScript | Apache-2.0 | 2023-01-10 | npm |
| [NeuralNote](https://github.com/DamRsn/NeuralNote) | C++ / JUCE | Apache-2.0 | 2025-01-16 | VST3/AU/standalone |
| [CREPE Notes](https://github.com/xavriley/crepe_notes) | Python | GPL-3.0 | 2026-03-13 | **no** -- see below |
| [YourMT3](https://github.com/mimbres/YourMT3) | Python | GPL-3.0 | 2024-11-29 | clone |
| [MT3](https://github.com/magenta/mt3) | Python / JAX / T5X | Apache-2.0 | 2026-07-08 | Colab |
| [Sheet Sage](https://github.com/chrisdonahue/sheetsage) | Python + Docker | MIT | 2025-05-13 | Docker |
| [Essentia](https://github.com/MTG/essentia) | C++ / Python | AGPL-3.0 | 2026-08-27 | **yes** |
| [aubio](https://github.com/aubio/aubio) | C / Python | GPL-3.0 | 2026-04-10 | **yes** |
| [Tony](https://github.com/sonic-visualiser/tony) / pYIN | C++ / Qt | GPL-2.0+ | 2024-07-02 | source build |

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

Two cautions. Basic Pitch is polyphonic, so on a vocal it can return
simultaneous notes where the reference has one, and that is a precision
penalty for a capability the task does not want -- worth reporting alongside,
not silently filtering. And Rachel Bittner is an author of both Basic Pitch and
vocadito; before quoting a vocadito number for it, check its training mix in the
ICASSP 2022 paper, which I could not open from this environment.

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

Also noted and not pursued: [bill317996/Audio-to-midi](https://github.com/bill317996/Audio-to-midi)
(MIT, melody extraction via MSnet, python 3.6/torch 1.0, last touched 2019-era)
and [tuneflow/singing-transcription-plugin](https://github.com/tuneflow/singing-transcription-plugin),
which is a DAW wrapper around york135's ICASSP 2021 model rather than a system
of its own.

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

**Training contamination.** Two of this project's four corpora appear on the
training side of systems here. M4Singer trained ROSVOT and, presumably, STARS.
MIR-ST500 songs 1-400 trained york135's two models. Anything from the
DiffSinger world has seen large quantities of Mandarin singing of unclear
provenance. `--items` exists for published test splits and should be used by
default, not when someone remembers.

**Annotation convention, again.** The 41 ms that `--onset-shift` corrected for
ROSVOT is not a ROSVOT bug; it is M4Singer's definition of where a note starts
(the syllable, including its leading consonant) travelling with the model.
Expect it from every M4Singer-trained system, expect it not to appear in
systems trained on pitch-annotated corpora, and let the report's own diagnostic
say which case each one is rather than assuming.

**Where checkpoints live** is a real axis of availability, not an
inconvenience. In repository (york135 ICASSP2021, keums, VOCANO) is best;
GitHub releases (SOME, GAME, phoneme-informed) is fine; HuggingFace (STARS,
VocalParse) is fine; Google Drive (ROSVOT, CTC_CE_for_AST) rots and rate-limits;
Baidu Pan (MusicYOLO) is effectively unavailable outside China. A system whose
weights you cannot fetch is not a baseline.

**Licences that constrain more than the code.** CREPE Notes is GPL-3.0 *and*
inherits madmom's non-commercial restriction. Essentia is AGPL-3.0. YourMT3 and
Tony are GPL. Three of the singing-specific repositories -- york135's two and
keums' -- ship **no licence file at all**, which means no grant of rights, not
"do as you like": fine for measuring privately, not for anything downstream.

**Filename pairing.** `pair_estimates` matches an estimate to an item by exact
stem first, then by a prefix followed by `_`, `-` or `.`. Basic Pitch's
`sung_phrase_basic_pitch.mid` and CREPE Notes'
`sung_phrase.crepe.transcription.mid` both pair through the prefix rule, so
neither needs renaming -- but the pairing is reported as non-exact, and that
line in the report is worth reading rather than skipping. Systems that write
one file per directory, or number their outputs, will need renaming before
`--estimates` sees them.

**What the smoke test does not tell you.** Basic Pitch and Essentia both scored
8/8 on a synthetic phrase with clean harmonics and a steady 5.2 Hz vibrato.
vocadito is untrained singers on phone microphones in seven languages. The
agreement here means only that the plumbing works.
