# A survey of singing transcription systems

This survey identifies publicly available systems that transcribe singing into notes, records what is required to run
each one, and determines which of them this benchmark can evaluate. It was conducted on 11 September 2026.

The survey does not rank systems by accuracy. Published results are reported on different datasets and under different
annotation conventions, so they describe datasets as much as systems. For example, ROSVOT reports a COnPOff of 77.4 on
M4Singer, while two annotators of vocadito agree with each other at 64.2. Accuracy measured under a common procedure is
reported in the README and [RESULTS.md](../RESULTS.md). [What was run](#what-was-run) lists the systems that those tables cover, and gives the
reason for each system that was not run.

## Method

### Question

Which publicly available systems convert singing audio into note events, and what is required for each to produce a
directory of transcriptions that this benchmark can read?

### Sources

1. **Seed set.** Systems already named in this repository or in the brief for the survey: ROSVOT, Basic Pitch, VOCANO
   and CREPE Notes.
2. **Web search.** Seventeen queries, listed below, were run on 11 September 2026. The search environment could not
   reach arxiv.org, so searches returned titles, abstracts and result snippets rather than full text.
3. **Citations and links.**
   - Where a search result named a system not yet on the list, a targeted query followed. This is how the
     phoneme-informed model, Kum et al.'s teacher–student model, SVT_SpeechBrain, VocalParse and three of the four
     publications without code were found.
   - Links in the READMEs of included repositories were also followed: VOCANO to Omnizart, SOME to GAME, STARS to
     ROSVOT, CREPE Notes to PESTO, PENN and torchcrepe, and Tony to pYIN and sonic-annotator.
4. **Repository inspection.** Each included system's repository was read directly: its README, licence file,
   dependency manifest, and the date of the latest commit on its default branch.
5. **Installation.** Each included system published on PyPI was installed into a clean Python 3.11 environment. Where
   installation succeeded, it was run on a synthetic sung phrase with known notes. That phrase has clean harmonics and
   steady vibrato, so success on it shows only that a system runs, not how accurate it is.

### Search log

Queries as issued. "New" lists what each query surfaced that earlier queries had not.

| # | Query | New |
|---|-------|-----|
| S1 | CREPE Notes new method segmenting pitch contours into discrete notes DAFx 2023 Riley Dixon | crepe_notes repository; SMC (not DAFx) as the venue |
| S2 | VOCANO note transcription singing voice polyphonic music github ISMIR 2021 Hsu Su | SongTrans, MusicMamba, Kum et al.'s pseudo-label paper |
| S3 | MIR-ST500 singing transcription baseline github york135 | SVT_SpeechBrain, CTC_CE_for_AST, HumTrans, TuneFlow plugin, YourMT3+ |
| S4 | SOME Singing-Oriented MIDI Extractor openvpi github vocal to midi | GAME, Vocal2Midi, bill317996/Audio-to-midi |
| S5 | singing voice transcription note-level open source 2025 2026 state of the art github | VocalParse, the phoneme-informed paper |
| S6 | CREPE Notes SMC 2023 evaluation datasets Filosax compared against Basic Pitch Omnizart | FiloSax and FiloBass as its evaluation corpora |
| S7 | YourMT3 singing voice transcription vocal stem multi-instrument github mimbres | YourMT3's claim of direct vocal transcription; MLSP 2024 |
| S8 | Omnizart vocal transcription module MCT lab install status maintained | Omnizart's module list; its Docker image |
| S9 | phoneme-informed note-level singing transcription ICASSP 2023 github seyong92 | the seyong92 repository; WhisperMSS |
| S10 | MusicYOLO sight-singing onset offset detection object detection github | MusicYOLO repository; the SSVD-v2.0 dataset |
| S11 | STARS unified framework singing transcription alignment refined style annotation github | STARS repository; ACL 2025 Findings |
| S12 | SongTrans unified song transcription alignment lyrics notes github code release | confirmation that no code is released |
| S13 | sheet sage Donahue lead sheet transcription vocal melody github docker | Sheet Sage's resource requirements |
| S14 | WhisperMSS two-stage Mandarin singing transcription Interspeech 2025 code | Cycle FHT Transformer; confirmation that no code is released |
| S15 | vocadito Bittner 2021 f0 note annotations Tony pYIN manual correction | Tony among vocadito's references |
| S16 | sonic-annotator pyin vamp plugin batch CLI note transcription CSV | the command-line route to pYIN's note output |
| S17 | MT3 training datasets Slakh MAESTRO URMP Cerberus GuitarSet MusicNet | MT3's instrumental training data |

### Inclusion criteria

- **I1. Note output.** The system emits discrete note events (onset, offset and pitch), not only a frame-level f0
  contour.
- **I2. Applicable to the voice.** The system is either trained on singing, or instrument-agnostic and usable on a solo
  vocal stem.
- **I3. Publicly obtainable.** Source code or a binary is publicly available. Alternatively, the system is published
  with enough prominence that the absence of code is worth recording (see [Published without code](#published-without-code)).
- **I4. Assessable.** The documentation is sufficient to determine the system's language, licence, inputs and outputs
  without running it.

### Exclusion criteria

- **E1. f0 estimators without segmentation.** CREPE, pYIN, RMVPE, PESTO, PENN, torchcrepe, SPICE and Praat fail I1.
  They appear only as components of systems that do segment notes. Audio-to-midi is also excluded under E1: it is an
  application of the MSnet melody extractor whose notes come from an undocumented rounding rule rather than a
  segmentation method.
- **E2. Closed or commercial software.** Melodyne, AnthemScore, Klangio, Dubler and the audio-to-MIDI functions of
  digital audio workstations. This is a decision about the survey's scope, not a judgement of relevance: these are the
  tools most musicians use, and the survey makes no claim about them.
- **E3. Not applicable to the voice.** Piano- or drum-specific transcription, such as Onsets and Frames, fails I2.
- **E4. Not a system.** Datasets (SSVD-v2.0, HumTrans, MIR-ST500) and wrappers that add no transcription capability of
  their own. They are mentioned where they explain a system. The TuneFlow plugin is a borderline case: it is listed,
  and identified as a wrapper around the MIR-ST500 model.

### Screening

Forty-eight candidates were identified:

- **Twenty-five met criteria I1–I4,** and are described below: thirteen singing-specific systems, ten general
  systems, and two that were noted but not pursued.
- **Four are published without obtainable code.**
- **Nineteen were excluded under E1–E4:** nine f0 estimators, five commercial products, one piano-specific model, and
  four datasets or training-only repositories.

Screening proceeded in three passes: title and README, then repository inspection, then installation. No candidate
was excluded on the evidence of its abstract alone, and none was included on the evidence of its README alone; every
included repository was read.

**Amendment, 13 November 2026.** Audio-to-midi was first counted among the candidates that met I1–I4, as one of three
noted but not pursued. Reading its code showed that it is an f0 estimator with an undocumented note rule, and that the
MIDI it writes is mistimed, so it was reclassified under E1. The counts above include this change.

### Excluded candidates

The nineteen excluded candidates are listed individually, so that each exclusion can be examined. Several are
nonetheless important: the f0 estimators excluded under E1 are components of many of the included systems.

| Candidate | Criterion | Reason | Found via |
|---|---|---|---|
| [CREPE](https://github.com/marl/crepe) | E1 | f0 only. It is the tracker that CREPE Notes segments. | link from crepe_notes |
| pYIN (as an f0 estimator) | E1 | f0 only. Its note output comes from the Vamp plugin, which is why Tony is included and this is not. | S16 |
| [RMVPE](https://github.com/yxlllc/RMVPE) | E1 | f0 only. It is the pitch stage of ROSVOT, SOME and STARS. | links from the ROSVOT and SOME READMEs |
| [PESTO](https://github.com/SonyCSLParis/pesto) | E1 | f0 only. An alternative backend for CREPE Notes. | link from the crepe_notes README |
| [PENN](https://github.com/interactiveaudiolab/penn) | E1 | f0 only. An alternative backend for CREPE Notes. | link from the crepe_notes README |
| [torchcrepe](https://github.com/maxrmorrison/torchcrepe) | E1 | f0 only. An alternative backend for CREPE Notes. | link from the crepe_notes README |
| SPICE | E1 | f0 only; self-supervised, distributed as a TensorFlow Hub model rather than a transcription system. | prior knowledge |
| Praat / Parselmouth | E1 | f0 only. Widely used, but does not produce notes. | prior knowledge |
| [Audio-to-midi](https://github.com/bill317996/Audio-to-midi) (bill317996) | E1 | f0 in substance. A demonstration application around MSnet, a melody extraction network (Hsieh, Su and Yang, ICASSP 2019) that outputs one pitch every 23.22 ms. Notes are formed by an undocumented rule: rounding to the nearest semitone and keeping runs of three frames or more. Its MIDI places frames on a 22.06 ms grid (170 BPM, 16 steps per beat), so every time is 5% early. Reclassified on 13 November 2026; see the amendment above. | S4 |
| Melodyne (Celemony) | E2 | Closed and commercial. The professional standard for note-level vocal editing, and the most significant omission from this survey. | prior knowledge |
| AnthemScore | E2 | Closed and commercial. | prior knowledge |
| Klangio / Melody Scanner | E2 | Closed and commercial; available only through an API and the web. | prior knowledge |
| Dubler 2 (Vochlea) | E2 | Closed and commercial; a real-time voice-to-MIDI controller, a task that favours latency over accuracy. | prior knowledge |
| Audio-to-MIDI in digital audio workstations (Logic, Ableton, Cubase) | E2 | Closed, and cannot be run over a corpus. | prior knowledge |
| Onsets and Frames, ByteDance piano transcription | E3 | Piano-specific. Listed because they are what automatic music transcription usually denotes in the literature. | lineage from MT3 |
| [SSVD-v2.0](https://github.com/xk-wang/SSVD-v2.0) | E4 | A dataset: MusicYOLO's sight-singing training and evaluation data. | S10 |
| [HumTrans](https://github.com/shansongliu/HumTrans) | E4 | A dataset for humming transcription. | S3 |
| MIR-ST500 | E4 | A dataset. | S3 |
| [Note-Segmentation-SSL](https://github.com/B05901022/Note-Segmentation-SSL) | E4 | VOCANO's training repository, with no inference path of its own. | link from the VOCANO README |

Two of these exclusions would merit reconsideration if the survey's scope changed:
- **E2:** Melodyne is the tool a working musician would use, and this survey cannot say whether any system below
  outperforms it.
- **E1:** a combination of an f0 estimator and a segmenter describes CREPE Notes and transcPybe, so the trackers
  excluded there are interchangeable components of such systems rather than competitors.

### Threats to validity

- **Searches were in English only.** Much singing transcription work is published in Chinese. OpenVPI's systems and
  MusicYOLO were found because they are also published on GitHub in English; comparable work published only on Gitee
  or documented only in Chinese would not have been found. This is the most likely source of omissions.
- **Full texts were not screened.** A system named only in the body of a paper would not have been found. This
  applies to the CREPE Notes paper that prompted the survey, whose reference list was not read.
- **Search ranking is not reproducible.** The same queries on a different day return results in a different order,
  and may surface different systems. The repository facts below are reproducible; the discovery process is not.
- **Coverage varies with recency.** Systems from 2021–2022 were found mainly by following citations rather than by
  search, so earlier work is covered less evenly than work from 2024 onwards.

## What was run

Fifteen of the twenty-five systems were run and scored; the results are in the README and RESULTS.md. The other ten were not
run, for the following reasons:

| System | Reason |
|---|---|
| VOCANO | Another version of a system that was run: its README states that the work is now distributed as Omnizart's `vocal` model. |
| basic-pitch-ts | Another version of a system that was run: Basic Pitch's model in TypeScript. |
| NeuralNote | Another version of a system that was run: a plugin built on Basic Pitch's model. |
| TuneFlow singing-transcription-plugin | Another version of a system that was run: a wrapper around the MIR-ST500 model (Wang and Jang, ICASSP 2021) for a digital audio workstation. |
| Vocal2Midi | Another version of a system that was run: a desktop pipeline built on GAME's note extraction, adding lyric recognition and alignment. |
| MusicYOLO | Weights not publicly available: its checkpoints are distributed only through Baidu Pan. |
| SVT_SpeechBrain | Weights not publicly available: its checkpoints are available on request. |
| VocalParse | No timed notes: it produces note values against a predicted tempo, not times in seconds. |
| Sheet Sage | No timed notes: its melody is a beat-quantised lead sheet. |
| MT3 | Not trained on singing: its training data are instrumental only. |

The fifteen systems evaluated were:

- Phoneme-informed, the MIR-ST500 model, CTC_CE_for_AST, Tony, YourMT3+, GAME, Omnizart (`vocal`) and SOME;
- Kum et al.'s teacher–student model, Basic Pitch, Essentia, CREPE Notes, ROSVOT, aubio and STARS.

## Singing-specific note transcription

These systems are trained on singing and predict note events. Unless stated otherwise, they are written in Python
with PyTorch.

| System | Licence | Last commit | Output | Checkpoints | Found via |
|---|---|---|---|---|---|
| [ROSVOT](https://github.com/RickyL-2000/ROSVOT) | MIT | 2024-11-20 | MIDI per item | Google Drive | seed set |
| [STARS](https://github.com/gwx314/STARS) | MIT | 2026-08-18 | notes and phoneme alignment | Hugging Face | S11 |
| [GAME](https://github.com/openvpi/GAME) | MIT | 2026-08-30 | MIDI, text, CSV | GitHub releases | link from the SOME README |
| [SOME](https://github.com/openvpi/SOME) | MIT | 2026-03-07 | MIDI (fractional pitch) | GitHub releases | S4 |
| [VOCANO](https://github.com/B05901022/VOCANO) | MIT | 2021-08-09 | MIDI and audio | in the repository | seed set |
| [Omnizart](https://github.com/Music-and-Culture-Technology-Lab/omnizart) `vocal` | MIT | 2026-05-31 | MIDI | `omnizart download-checkpoints` | link from the VOCANO README |
| [singing_transcription_ICASSP2021](https://github.com/york135/singing_transcription_ICASSP2021) | none | 2026-03-05 | MIDI | **in the repository** | S3 |
| [CTC_CE_for_AST](https://github.com/york135/CTC_CE_for_AST) | none | 2025-03-25 | MIDI | Google Drive | citation from S3 |
| [phoneme-informed](https://github.com/seyong92/phoneme-informed-note-level-singing-transcription) | MIT | 2023-09-09 | MIDI | Git LFS or release | citation from S5 to S9 |
| [icassp2022-vocal-transcription](https://github.com/keums/icassp2022-vocal-transcription) | none | 2022-05-12 | MIDI | in the repository | citation from S2 |
| [MusicYOLO](https://github.com/itec-hust/MusicYOLO) | Apache-2.0 | 2022-01-29 | onsets, offsets and pitch | Baidu Pan | S10 |
| [VocalParse](https://github.com/pymaster17/VocalParse) | Apache-2.0 | 2026-06-16 | token sequence | Hugging Face | S5 |
| [SVT_SpeechBrain](https://github.com/guxm2021/SVT_SpeechBrain) | Apache-2.0 | 2024-08-30 | note events | on request | S3 |

**ROSVOT** (Li et al., ACL 2024) was the first system scored in this project, on vocadito in September 2026.
- Its published checkpoint was trained on M4Singer only, and it carries M4Singer's annotation convention.
- Its notes were on average 66 ms longer than vocadito's references, and began 41 ms earlier.
- Other systems trained on M4Singer may be expected to show the same offset.

**STARS** (Findings of ACL 2025) is built on ROSVOT, according to its README.
- **Model:** a single model performs transcription, phoneme alignment, vocal-technique tagging and global style
  classification.
- **Interface:** it takes the same `metadata.json` input as ROSVOT, and its Chinese and Chinese–English checkpoints
  are on Hugging Face with an RMVPE pitch extractor.
- **Environment:** its authors tested it with Python 3.10, torch 2.4.0 and CUDA 12.8.
- **Lyrics:** STARS requires lyrics. How these were obtained for the benchmark is described in
  `orchestrator/images/stars/NOTES.md`.

**SOME** and **GAME** come from the OpenVPI (DiffSinger) community, where they are used to label singing datasets for
speech synthesis.
- **SOME** reports a speed of nine times real time on an Intel i5 CPU, and can be trained on three hours of data.
- **GAME**, its successor, transcribes a directory of files to MIDI, text and CSV in one command
  (`python infer.py extract /audio/dir/ -m model.pt --glob *.wav --output-formats mid,txt,csv`), which matches the
  input that `--estimates` expects. It claims robustness to reverberation, noise and accompaniment, adjustable
  note-presence thresholds, and multilingual segmentation.
- **Pitch output:** both emit fractional MIDI pitches, which this benchmark retains rather than rounding.

GAME was the most recently updated system in the survey (30 August 2026). Its training data were not verified.

**VOCANO** (Hsu and Su, ISMIR 2021) separates pitch extraction (a patch-based CNN) from note segmentation
(PyramidNet-110 with ShakeDrop, trained semi-supervised). It was last updated in August 2021, and requires NVIDIA apex
and a CUDA 10.1-era environment. Its README states that the work is now distributed as part of Omnizart.

**Omnizart**'s `vocal` module packages VOCANO in a toolbox that also transcribes chords, drums, beats and pitched
instruments, described in a JOSS paper.
- **Interface:** `omnizart vocal transcribe audio.wav`; `vocal-contour` gives a frame-level f0 from the same
  installation.
- **Installation at survey time:** `pip install omnizart` failed while building pyaudio, which requires the system
  library PortAudio (`apt install portaudio19-dev`). The Docker image `mctlab/omnizart` avoids this.
- **Platforms:** ARM macOS is not supported.

**singing_transcription_ICASSP2021** is the model of the MIR-ST500 paper (Wang and Jang, ICASSP 2021): an
EfficientNet-b0, whose pretrained checkpoint is committed to the repository.
- **Interface:** `python do_everything.py in.wav out.mid -p model/1005_e_4 -s -on 0.4 -off 0.5` runs the full
  pipeline. `-s` applies Spleeter separation to polyphonic input, and `-on` and `-off` set the onset and silence
  thresholds.
- **Training data:** MIR-ST500 songs 1–400, so it can be evaluated on MIR-ST500 songs 401–500 only (`--items`).

**CTC_CE_for_AST** (Wang and Jang, TASLP 2022) is the same authors' follow-up, which adds a CTC loss to the
cross-entropy objective.
- **Interface:** the same as above, with checkpoints on Google Drive.
- **Labels:** its experiments shift MIR-ST500's onset labels by +30 ms, and it distributes the corrected labels. This
  independently indicates that MIR-ST500's published onsets are early relative to the audio.

**phoneme-informed-note-level-singing-transcription** (Yong et al., ICASSP 2023) treats note onsets as a linguistic
problem: a note that begins on a plosive and one that begins on a vowel are different events.
- **Model:** it takes a phonetic posteriorgram alongside the mel spectrogram.
- **Interface:** `python infer.py checkpoints/model.pt in.wav out.mid --bpm 120` writes MIDI. Because it takes a
  tempo, its output should be checked for quantisation.
- **Checkpoint:** available through Git LFS or as a release asset.

**icassp2022-vocal-transcription** (Kum et al., ICASSP 2022) transcribes singing directly from polyphonic audio.
- **Model:** pseudo-labels derived from frame-level pitch estimators, refined by teacher–student self-training.
- **Environment:** Keras and TensorFlow 2.5, on Linux only.
- **Interface:** `python singing_transcription.py -i in.wav -o outdir`, with `-ot midi|fps` selecting note or
  frame-level output.

**MusicYOLO** (Wang et al., ICASSP 2022, with a 2022 journal extension) detects notes as bounding boxes on the
spectrogram with YOLOX, and estimates pitch by spectral peak search. It reports an onset F1 of 94.16% on the ISMIR2014
dataset.
- **Checkpoints:** distributed only through Baidu Pan.
- **Environment:** torch 1.8, CUDA 10.2, apex and a vendored copy of pycocotools.
- **Output:** not MIDI, so a converter would be required.

**VocalParse** (May 2026) extends the vocabulary of Qwen3-ASR with about 400 tokens for pitch, note value and tempo.
- **Output:** a single sequence interleaving lyrics and notes (`感 <P_68> <NOTE_4> 受 <P_60> <NOTE_8> ... <BPM_89>`).
- **Checkpoint:** a 1.7-billion-parameter model on Hugging Face, under Apache-2.0.
- **Timing:** its output gives note values (for example, quavers and crotchets) against a predicted global tempo,
  rather than times in seconds. Converting it to timed notes depends on that tempo estimate, so a tempo error becomes
  a proportional timing error across the whole recording, which `--align` cannot correct.

**SVT_SpeechBrain** (Gu et al., TOMM 2024) transcribes notes from singing with self-supervised speech encoders,
optionally combined with lip-movement video.
- **Design:** its dataset (N20EM) and much of its design assume video.
- **Environment:** SpeechBrain, AV-HuBERT, torch 1.9 and CUDA 11.1.
- **Checkpoints:** available on request.

## General transcription applied to a vocal stem

These systems are not specific to singing, although some have been trained on it: Basic Pitch's training data include
two vocal corpora. They are included because a solo vocal is a monophonic source, and because systems not designed for
singing provide a reference for those that are.

| System | Language | Licence | Last commit | Installation at survey time | Found via |
|---|---|---|---|---|---|
| [Basic Pitch](https://github.com/spotify/basic-pitch) | Python (TensorFlow, CoreML, TFLite, ONNX) | Apache-2.0 | 2025-11-13 | **succeeded** | seed set |
| [basic-pitch-ts](https://github.com/spotify/basic-pitch-ts) | TypeScript | Apache-2.0 | 2023-01-10 | npm | link from the Basic Pitch README |
| [NeuralNote](https://github.com/DamRsn/NeuralNote) | C++ / JUCE | Apache-2.0 | 2025-01-16 | VST3, AU, standalone | prior knowledge, verified |
| [CREPE Notes](https://github.com/xavriley/crepe_notes) | Python | GPL-3.0 | 2026-03-13 | **failed**; see below | seed set |
| [YourMT3](https://github.com/mimbres/YourMT3) | Python | GPL-3.0 | 2024-11-29 | from source | S3, then S7 |
| [MT3](https://github.com/magenta/mt3) | Python / JAX / T5X | Apache-2.0 | 2026-07-08 | Colab | lineage from YourMT3 |
| [Sheet Sage](https://github.com/chrisdonahue/sheetsage) | Python and Docker | MIT | 2025-05-13 | Docker | S13 |
| [Essentia](https://github.com/MTG/essentia) | C++ / Python | AGPL-3.0 | 2026-08-27 | **succeeded** | prior knowledge, verified |
| [aubio](https://github.com/aubio/aubio) | C / Python | GPL-3.0 | 2026-04-10 | **succeeded** | prior knowledge, verified |
| [Tony](https://github.com/sonic-visualiser/tony) / pYIN | C++ / Qt | GPL-2.0 or later | 2024-07-02 | from source | S15, S16 |

**Basic Pitch** (Bittner et al., ICASSP 2022) installed into a clean Python 3.11 environment with
`pip install basic-pitch`.
- **Installation check:** `basic-pitch outdir sung_phrase.wav` transcribed all eight notes of the synthetic phrase at
  the correct pitches, with every onset within 36 ms.
- **Model:** polyphonic and instrument-agnostic, with pitch-bend output and TensorFlow, CoreML, TFLite and ONNX
  runtimes. basic-pitch-ts (TypeScript) and NeuralNote (a VST3, AU and standalone plugin) are built on the same model.
- **Polyphony:** because it is polyphonic, it can return simultaneous notes where a vocal reference has one, which
  lowers its precision.
- **Training data:** Basic Pitch and vocadito share an author (R. M. Bittner). Basic Pitch's training pipeline
  registers five datasets (GuitarSet, iKala, MAESTRO, MedleyDB-Pitch and Slakh, in `basic_pitch/data/download.py`),
  none of which is vocadito. vocadito appears in that repository only as a test fixture. Two of the five datasets,
  iKala and MedleyDB-Pitch, contain singing.

**CREPE Notes** (Riley and Dixon, SMC 2023; the paper that prompted this survey) derives notes from CREPE's f0.
- **Method:** it combines the gradient of the pitch contour with the inverse of the estimate's confidence, takes peaks
  of the combined signal as onsets, and uses madmom's onset detector for repeated notes at one pitch. It uses 97% fewer
  parameters than the deep models it is compared with.
- **Published evaluation:** instrumental. Its README reports F-measures of 90% on Filosax (saxophone), 74% on ITM GT
  Flute 99 and 72% on FiloBass, and advises raising `--min-duration` to 50 ms or more for vocals.
- **Licence:** GPL-3.0. According to its README, madmom's restriction on commercial use also applies to it.

At the time of the survey, CREPE Notes could not be installed as documented. On a clean Python 3.11 environment:
1. `pip install crepe-notes[crepe]` failed, because madmom's source distribution does not declare Cython as a build
   requirement.
2. The README's workaround (`pip install --no-build-isolation git+https://github.com/CPJKU/madmom@main`, with
   `Cython<3` and `numpy<2`) built madmom.
3. The `crepe` package then failed to build, because recent versions of setuptools no longer provide `pkg_resources`.
   The README documents this under macOS, but it is not specific to that platform.
4. Without the `[crepe]` extra, crepe-notes installed but failed on import, because it does not declare its
   dependency on matplotlib.
5. With matplotlib and the torchcrepe backend installed, it failed in `torchaudio.load`, because torchaudio 2.11
   delegates decoding to TorchCodec, which requires FFmpeg shared libraries.

It was later run for the benchmark in its own container.

**YourMT3+** (Chang et al., MLSP 2024) extends MT3's token-based decoding.
- **Model:** a hierarchical time–frequency attention encoder and a mixture of experts.
- **Claims:** direct singing transcription without source separation, evaluated on ten datasets.
- **Licence:** GPL-3.0.
- **Availability at survey time:** its code was a pre-release, linked from issue 2 of its repository, and its main
  interface was a Hugging Face Space.

How it was run for the benchmark is described in `orchestrator/images/yourmt3/NOTES.md`.

**MT3** (Gardner et al., ICLR 2022) is YourMT3's predecessor.
- **Training data:** MAESTROv3, Slakh2100/Cerberus4, GuitarSet, MusicNet and URMP, which contain no singing.
- **Distribution:** primarily a Colab notebook built on T5X and JAX.

It was therefore not evaluated as a singing transcription system.

**Sheet Sage** (Donahue et al., ISMIR 2022) transcribes a lead sheet from a mixed recording: melody and chords,
aligned to beats, with an estimated key. It uses Jukebox representations and models trained on HookTheory.
- **Output:** the melody is a component of the lead sheet, and is quantised to beats, which would appear as timing
  error against references annotated from audio.
- **Requirements:** Linux, Docker and about 4 GB of container. The Jukebox features need a further 10 GB or so, and a
  GPU with 12 GB of memory.

**Essentia** installed directly with pip.
- **Installation check:** its classical pipeline (`PredominantPitchMelodia` followed by `PitchContourSegmentation`)
  returned all eight synthetic notes with the correct pitches, and every onset within 22 ms. It took a few seconds of
  CPU time and needed no model download.
- **Library:** C++ with Python bindings, from the Music Technology Group in Barcelona.
- **Licence:** AGPL-3.0, which constrains redistribution and use as a service.

**aubio** also installed cleanly.
- **Installation check:** `aubio notes` returned three notes for the eight-note phrase, holding pitch 62 from 0.03 s to
  2.30 s through the notes at 64, 65 and 67 above it. An onset detector that responds to energy but not to pitch
  change merges a legato phrase into a single note.
- **Output:** text rather than MIDI, so a converter is required.

It serves as a lower reference.

**Tony** (Mauch et al., TENOR 2015) is software for computer-aided melody annotation rather than an automatic system.
- **Basis:** pYIN and the Sonic Visualiser libraries.
- **Licence:** GPL-2.0 or later; last updated in July 2024.
- **Automatic component:** the note output of the pYIN Vamp plugin, which runs without the interface under
  sonic-annotator.
- **Overlap with vocadito:** vocadito's note annotations were produced by correcting Tony's output, so Tony's scores on
  vocadito measure agreement with the annotation tool. RESULTS.md excludes vocadito from Tony's mean, and the README's
  table, which averages vocadito, Molina and RWC-P, leaves Tony out.

Two further systems met the criteria but were not pursued:
- [tuneflow/singing-transcription-plugin](https://github.com/tuneflow/singing-transcription-plugin): a wrapper for a
  digital audio workstation around the MIR-ST500 model.
- [Xiantaidu/Vocal2Midi](https://github.com/Xiantaidu/Vocal2Midi): a desktop tool for vocal-to-MIDI extraction with
  lyric alignment, built on GAME's note extraction.

## Published without code

Each of these was searched for by name, with "github" and "code"; no repository was found.

- **SongTrans** (2024): joint lyric and note transcription with alignment, combining an autoregressive word and
  duration module with a non-autoregressive pitch module.
- **WhisperMSS** (Interspeech 2025): two-stage Mandarin singing transcription built on pretrained models.
- **MusicMamba** (2025): a Mamba-based singing transcription model.
- **Cycle Frequency-Harmonic-Time Transformer** (2024): note-level singing transcription.

## Considerations across systems

### Overlap between training and evaluation data

The training data of each system, as far as they were established:

| System | Training data | Source |
|---|---|---|
| Basic Pitch | GuitarSet, iKala, MAESTRO, MedleyDB-Pitch, Slakh | the dataset registry in its source (`basic_pitch/data/download.py`) |
| ROSVOT | M4Singer | its README, for the published checkpoint |
| MIR-ST500 model, CTC_CE_for_AST | MIR-ST500 songs 1–400 | their READMEs |
| YourMT3+ | ten datasets, including MIR-ST500 songs 1–400 (with songs 401–500 used for validation) and CMedia | its paper and source code |
| MT3 | MAESTROv3, Slakh2100/Cerberus4, GuitarSet, MusicNet, URMP | its paper; instrumental only |
| CREPE Notes | none; it post-processes CREPE's output | its README |
| STARS | the Chinese and English subsets of GTSinger, and 30 hours of Chinese singing recorded by its authors | its paper (section 4.1.1) |
| SOME, GAME | OpenVPI community data | not verified |

No system in the survey was found to train on vocadito, which was released in 2021 as an evaluation set. The overlaps
that affect the five datasets used in the benchmark are marked in RESULTS.md.

### Annotation conventions

The 41 ms by which ROSVOT's onsets preceded vocadito's is not a defect of ROSVOT. It reflects M4Singer's definition of
where a note starts: the beginning of the syllable, including its initial consonant. The same offset may be expected
from other systems trained on M4Singer, but not from systems trained on corpora annotated by pitch. The report's own
diagnostic indicates which case applies.

### Availability of checkpoints

Where a system's weights are hosted determines whether it can be evaluated:
- **Reliable:** weights committed to the repository (the MIR-ST500 model, Kum et al., VOCANO), GitHub releases (SOME,
  GAME, phoneme-informed) and Hugging Face (STARS, VocalParse).
- **Unreliable:** Google Drive (ROSVOT, CTC_CE_for_AST) is subject to rate limits and link expiry.
- **Effectively unavailable outside China:** Baidu Pan (MusicYOLO).

A system whose weights cannot be obtained cannot serve as a baseline.

### Licences

- **CREPE Notes** is GPL-3.0, and inherits madmom's restriction on commercial use.
- **Essentia** is AGPL-3.0.
- **YourMT3 and Tony** are GPL.
- **Three singing-specific repositories** (the MIR-ST500 model, CTC_CE_for_AST and Kum et al.'s) include no licence
  file. That grants no rights: it permits private measurement, but not redistribution or derived work.

### Pairing output files with recordings

`pair_estimates` matches an output file to a recording by exact file stem first, then by a prefix followed by `_`, `-`
or `.`. Basic Pitch's `sung_phrase_basic_pitch.mid` and CREPE Notes' `sung_phrase.crepe.transcription.mid` both pair
through the prefix rule, without renaming, and the report identifies such pairings as non-exact. Systems that write one
file per directory, or that number their outputs, require renaming before `--estimates` can read them.
