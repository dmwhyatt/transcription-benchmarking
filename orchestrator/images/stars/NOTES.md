# STARS in the benchmark

Guo et al., "STARS: A Unified Framework for Singing Transcription, Alignment, and Refined Style Annotation", Findings
of ACL 2025, arXiv 2507.06670. Code: github.com/gwx314/STARS, MIT, pinned to f0e43e9 (18 August 2026). Built on ROSVOT
by an overlapping group. Prepared 12 November 2026 and run on all five
sets after the fix described below (`run_five_r2.sh`). Its scores are in the README's results table, marked ‡.

## It needs lyrics

Unlike ROSVOT, STARS cannot run from audio alone. `inference/stars.py` reads `word`, `ph` and `ph2words` from its
metadata and requires them. It force-aligns that phoneme sequence to its own frame-level phoneme logits (Viterbi),
pools features over the aligned phoneme and word spans into the note decoder, and regulates the decoded notes against
the aligned word boundaries before writing MIDI (`infer_regulate_real_note_itv: true`). The paper (section 3.2) says
the lyrics "can be obtained using ASR models", and the repository's `scripts/process_ch.py` does that for audio that
arrives without them. The adapter follows that route:

1. `process_ch.cut_long_audio`, unchanged: fsmn-vad cuts each recording longer than 20 s into 8-20 s segments, each
   widened by 100 ms either side. A recording of 20 s or less is kept whole.
2. SenseVoiceSmall transcribes each segment with `process_ch`'s own `generate()` arguments (`language="auto"`).
3. `scripts/mixedtext2phoneme.py`, the README's phonemiser for the bilingual model, phonemises the text at its CLI
   defaults. Chinese goes through pypinyin without tones, and Latin script through the MFA English dictionary, falling
   back to letters for words it does not contain.
4. `inference/stars.py` runs with the bilingual checkpoint, its config and phone set, at the authors' defaults:
   `--thr 0.85` with note regulation on.
5. Each segment's notes are shifted by the segment's start, and one MIDI file is written per recording.

A segment for which ASR returns no text, or text that phonemises to nothing, is dropped, as `process_ch` drops it.
Its notes are lost. A recording left with no notes still gets an empty MIDI file, so it scores zero rather than being
skipped. `adapter.json` counts both, per recording.

## Checkpoint

Of the two on HuggingFace (verstar/STARS @ 744a7ad), the bilingual one is used:
`stars_chinese_english_bilingual/model_ckpt_steps_300000.ckpt`, with `configs/stars_bilingual.yaml` and
`chinese_and_english_phone_set.json`. The benchmark's sets are sung in English, Chinese, Japanese, Spanish and others.
The Chinese model's phone set has no English phones (59 entries, all pinyin), and its phonemiser turns each English
word into one placeholder token. The
bilingual model has ARPAbet phones for English and pinyin finals for Chinese, so it covers the most of our audio. The
paper says it was validated only on Chinese and English (section 6).

## Training data and contamination

The paper trains on the Chinese and English subsets of GTSinger (CC BY-NC-SA 4.0) and on a 30-hour Chinese set the
authors recorded with two professional singers (section 4.1.1; appendix C.1). It names none of vocadito, Molina, SSVD,
RWC-P or MIR-ST500; Molina et al. appear only as the source of the COnPOff metric. GTSinger is also in transcPybe's
training data. The ASR model, SenseVoiceSmall, is a separate speech model trained on speech, not on any set here.

## Licences

The code is MIT. The verstar/STARS model card states no licence, and its training data is CC BY-NC-SA, so treat the
weights as non-commercial. SenseVoiceSmall is under FunASR's model licence ("other" on HuggingFace), and fsmn-vad is
Apache-2.0.

## Deviations from upstream, all recorded in the Dockerfile and adapter

- **Environment:** Python 3.10 with torch 2.4.0 (cu124 wheels) is the README's tested stack.
  - The unpinned requirements were pinned where Python 3.10 needed it: `numpy<2`, `scipy<1.14`, `scikit-image<0.25`
    and pyworld 0.3.5.
  - g2p_en was left out, because nothing on the inference path imports it.
- **Models are local:** `process_ch` names its models by hub ID. The adapter serves the same models from `/ckpt`,
  because the container runs offline.
- **Input conversion:** pydub reads PCM WAV only, so each recording is given to the pipeline as a mono 16-bit copy.
  Separated stems that peak above full scale are scaled to a 0.99 peak rather than clipped.
- **Phonemiser:** `process_ch` phonemises with a Chinese-only processor written for the Chinese model. Because the
  bilingual checkpoint is run, the README's mixed-text phonemiser is used instead.
- **Phone set path:** `stars.py` builds its dataset's phone encoder from `<processed_data_dir>/phone_set.json`, a
  training directory the repository does not ship. That path is pointed at a copy of the `--phset` file.
- **Stitching:** segment outputs are joined into one MIDI file per recording. Notes can overlap within the 100 ms
  widening where two segments meet; they are kept as STARS wrote them.

## Smoke test, 12 November 2026

The first two vocadito recordings (10 and 11, both English), 0.37 minutes of audio. On the RTX 3080 with CDI
(`--device nvidia.com/gpu=all`), `--network none`, `--cpus 8`:

- **Lyrics:** ASR found them in both segments. "o my darling o my darling ... clementine" is close to the song.
- **Notes:** 22 and 23 notes, against 35 and 37 reference notes.
- **Score:** against annotator 1, COnPOff 0.171 macro (interval 0.167–0.175), and COnP 0.274 micro.
- **Repeatability:** a second run wrote byte-identical MIDI.
- **GPU memory:** 1.5 GB at peak above the idle card (1.9 of 10 GB in use).
- **Time:** 53 s cold and 26 s warm. Almost all of it is loading SenseVoiceSmall, STARS and RMVPE; generation was
  13 s for the batch. The per-minute cost on long recordings is still to be measured.

Untested: long recordings, where `stars.py` batches up to 100,000 frames, roughly 26 twenty-second segments, and may
need more GPU memory. Also untested: singing that ASR cannot read, such as non-lexical syllables, or Japanese kana, which
the phonemiser passes through as unknown tokens.

## The first five-set run, and the fix (12 November 2026)

`run_five.sh` (10:49–11:06) crashed on every set at `modules/stars/utils.py:308`, in `perform_viterbi_bd`, with
`IndexError: index 0 is out of bounds for axis 0 with size 0`.

- **Cause:** SenseVoiceSmall writes Korean or kana for some singing. The phonemiser passes those characters through
  as tokens outside the bilingual phone set. The aligner discards unknown tokens and `<SP>`, then indexes the first
  label that remains, and for these segments none remains.
- **Scale:** 6 such segments on vocadito, 5 on Molina, 5 on RWC-P, 11 on SSVD and 18 on MIR-ST500.
- **Why every set failed:** `stars.py` runs a whole set in one process, so a single such segment lost the set.

The adapter now does two things:

1. **It drops those segments before `stars.py` sees them.** It drops any segment with no phone in the set, or with
   more phones than frames, and counts them as `segments_unalignable`. This is the same kind of drop `process_ch`
   makes for a segment with no text.
2. **It splits a failing run.** The split is by recording first, then by segment, down to single segments. A segment
   that fails alone is recorded in `failed_segments` with its error. The splitting is capped at 40 `stars.py`
   processes.

Tests:

- **Isolation:** with the pre-filter switched off on five vocadito recordings, 11 runs isolated the 4 bad segments,
  each with that IndexError, and kept the rest.
- **The fix:** with the pre-filter on, the vocadito and Molina recordings that had failed all wrote MIDI.

The first attempt's work directories are left as they were. The rerun writes to `bench-work-stars-<set>-20261112-r2`
(`run_five_r2.sh`).

## Results depend on the batch

`stars.py` batches segments up to its defaults, `--bsz 128` and `--max_tokens 100000`, padding each batch to its
longest member, and the padding changes the output. The same vocadito_10 segment gave:

- 22 notes batched with vocadito_11;
- 22 notes, with different first notes, batched with another recording's segment;
- 35 notes run on its own.

Two runs over the same set are byte-identical, so the output is deterministic for a fixed input set but not
independent of the rest of the set. The benchmark keeps the authors' defaults. `--bsz 1` would make each segment's
output independent of the set; that is a decision to make on purpose, not here.
