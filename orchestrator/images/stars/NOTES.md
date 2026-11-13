# STARS

Guo et al., "STARS: A Unified Framework for Singing Transcription, Alignment, and Refined Style Annotation",
Findings of ACL 2025 (arXiv 2507.06670).

- **Code:** github.com/gwx314/STARS, MIT licence, pinned to f0e43e9 (18 August 2026). It is built on ROSVOT by an
  overlapping group of authors.
- **Status:** prepared on 12 November 2026, and run on all five datasets after the corrections described under
  [Failure handling](#failure-handling) (`run_five_r2.sh`). Its scores are in the README's results table, marked ‡.

## Lyrics

Unlike ROSVOT, STARS cannot run from audio alone:
- **What it needs:** `inference/stars.py` requires `word`, `ph` and `ph2words` in its metadata.
- **How it uses them:** it aligns that phoneme sequence to its own frame-level phoneme posteriors (Viterbi), pools
  features over the aligned phoneme and word spans for the note decoder, and adjusts the decoded notes to the aligned
  word boundaries before writing MIDI (`infer_regulate_real_note_itv: true`).
- **Where they come from:** the paper (section 3.2) states that lyrics "can be obtained using ASR models", and the
  repository's `scripts/process_ch.py` does so for audio without lyrics.

The adapter follows that route:

1. `process_ch.cut_long_audio`, unchanged: the fsmn-vad model divides each recording longer than 20 s into segments
   of 8–20 s, each extended by 100 ms at both ends. A recording of 20 s or less is kept whole.
2. SenseVoiceSmall transcribes each segment, with `process_ch`'s own `generate()` arguments (`language="auto"`).
3. `scripts/mixedtext2phoneme.py`, the README's phonemiser for the bilingual model, converts the text to phonemes with
   its default settings. Chinese text passes through pypinyin without tones, and Latin script through the MFA English
   dictionary, which falls back to letters for words it does not contain.
4. `inference/stars.py` runs with the bilingual checkpoint, its configuration and its phone set, at the authors'
   defaults: `--thr 0.85`, with note regulation enabled.
5. Each segment's notes are shifted by the segment's start time, and one MIDI file is written per recording.

A segment for which speech recognition returns no text, or whose text yields no phonemes, is omitted, as `process_ch`
omits it, and its notes are lost. A recording left with no notes still receives an empty MIDI file, so that it scores
zero rather than being skipped. `adapter.json` counts both, for each recording.

## Checkpoint

Of the two checkpoints on Hugging Face (verstar/STARS at 744a7ad), the bilingual one is used:
- **Files:** `stars_chinese_english_bilingual/model_ckpt_steps_300000.ckpt`, with `configs/stars_bilingual.yaml` and
  `chinese_and_english_phone_set.json`.
- **Why this one:** the benchmark's datasets are sung in English, Chinese, Japanese, Spanish and other languages. The
  Chinese model's phone set has no English phones (59 entries, all pinyin), and its phonemiser maps each English word
  to a single placeholder token. The bilingual model has ARPAbet phones for English and pinyin finals for Chinese, so
  it covers most of the audio.
- **Validation:** the paper reports validation on Chinese and English only (section 6).

## Training data

The paper trains STARS on the Chinese and English subsets of GTSinger (CC BY-NC-SA 4.0), and on 30 hours of Chinese
singing recorded by the authors with two professional singers (section 4.1.1; appendix C.1).
- **Overlap with this benchmark:** the paper names none of vocadito, Molina, SSVD, RWC-P or MIR-ST500. Molina et al.
  appear only as the source of the COnPOff metric.
- **Overlap with transcPybe:** GTSinger is also among transcPybe's training data.
- **Speech recognition:** SenseVoiceSmall is a separate model, trained on speech rather than on any dataset here.

## Licences

- **Code:** MIT.
- **Weights:** the verstar/STARS model card states no licence. Its training data are CC BY-NC-SA, so the weights should
  be treated as non-commercial.
- **Supporting models:** SenseVoiceSmall is under FunASR's model licence ("other" on Hugging Face), and fsmn-vad is
  Apache-2.0.

## Departures from upstream

All are recorded in the Dockerfile and the adapter:
- **Environment:** Python 3.10 with torch 2.4.0 (CUDA 12.4 wheels), the README's tested configuration.
  - Unpinned requirements are pinned where Python 3.10 requires it: `numpy<2`, `scipy<1.14`, `scikit-image<0.25` and
    pyworld 0.3.5.
  - g2p_en is omitted, because nothing on the inference path imports it.
- **Local models:** `process_ch` refers to its models by Hugging Face identifier. The adapter serves the same models
  from `/ckpt`, because the container runs without network access.
- **Input conversion:** pydub reads PCM WAV only, so each recording is given to the pipeline as a mono 16-bit copy.
  Separated stems that peak above full scale are scaled to a peak of 0.99 rather than clipped.
- **Phonemiser:** `process_ch` uses a Chinese-only phonemiser written for the Chinese model. Because the bilingual
  checkpoint is used, the README's mixed-text phonemiser is used instead.
- **Phone set path:** `stars.py` builds its phone encoder from `<processed_data_dir>/phone_set.json`, a training
  directory that the repository does not include. That path points to a copy of the `--phset` file.
- **Joining segments:** segment outputs are combined into one MIDI file per recording. Notes may overlap within the
  100 ms extensions where two segments meet; they are kept as STARS produced them.

## Failure handling

SenseVoiceSmall produces Korean script or Japanese kana for some singing. The phonemiser passes such characters through
as tokens outside the bilingual phone set. The aligner discards unknown tokens and `<SP>`, then indexes the first
remaining label; for these segments, none remains, and `perform_viterbi_bd` (`modules/stars/utils.py`, line 308)
raises an IndexError.

- **Frequency:** such segments occurred in every dataset: 6 in vocadito, 5 in Molina, 5 in RWC-P, 11 in SSVD and 18 in
  MIR-ST500.
- **Effect:** because `stars.py` processes a whole dataset in one process, a single such segment caused the whole
  dataset to fail.

The adapter therefore does two things:
1. **It omits such segments before `stars.py` sees them.** These are segments with no phone in the set, or with more
   phones than frames. They are counted as `segments_unalignable`, an omission of the same kind as `process_ch` makes
   for a segment without text.
2. **It splits a failing run.** The split is first by recording and then by segment, down to single segments. A
   segment that fails on its own is recorded in `failed_segments` with its error. Splitting is limited to 40
   invocations of `stars.py`.

Both behaviours were tested:
- With the filter disabled, on five vocadito recordings, splitting isolated the four failing segments in 11 runs and
  kept the rest.
- With the filter enabled, every vocadito and Molina recording that had failed produced MIDI.

## Dependence on batch composition

`stars.py` batches segments up to its defaults, `--bsz 128` and `--max_tokens 100000`, padding each batch to its
longest member, and the padding changes the output. The same vocadito_10 segment gave:
- 22 notes when batched with vocadito_11;
- 22 notes, with different first notes, when batched with another recording's segment;
- 35 notes when run alone.

Two runs over the same dataset are identical to the byte, so the output is deterministic for a fixed set of inputs, but
it depends on the rest of the dataset. The benchmark keeps the authors' defaults; `--bsz 1` would make each segment's
output independent of the others.

## Verification

Before the full run, the image was tested on the first two vocadito recordings (10 and 11, both in English; 0.37
minutes of audio), on the RTX 3080 with CDI (`--device nvidia.com/gpu=all`), `--network none` and `--cpus 8`:
- **Lyrics:** speech recognition found lyrics in both segments ("o my darling o my darling ... clementine" for the
  song).
- **Notes:** 22 and 23 notes, against 35 and 37 reference notes.
- **Scores:** against annotator 1, COnPOff 0.171 macro-averaged (interval 0.167–0.175), and COnP 0.274
  micro-averaged.
- **Repeatability:** a second run produced identical MIDI files.
- **Memory:** 1.5 GB of GPU memory at peak above the idle card (1.9 of 10 GB in use).
- **Time:** 53 s on first run and 26 s thereafter, almost all of it spent loading SenseVoiceSmall, STARS and RMVPE;
  generation took 13 s for the batch.
