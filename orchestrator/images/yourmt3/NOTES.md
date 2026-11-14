# YourMT3+

Prepared on 12 November 2026, and run on all five datasets the same day. Its scores and computation time are in
RESULTS.md, and its scores on the datasets no system was trained on are in the README.

## What runs

- **Code:** the authors' Hugging Face Space `mimbres/YourMT3`, revision `5e66c1ea173a8186e0d20432b841d3180cc015b5`
  (31 January 2025): `amt/src` and `model_helper.py`, code only. The GitHub repository (`mimbres/YourMT3`, 8a4fbca)
  contains a README that refers to the Space for the pre-release code (issue 2).
- **Model:** "YPTF.MoE+Multi (noPS)", checkpoint
  `mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops/checkpoints/last.ckpt`.
  - Size and hash: 561,544,628 bytes, sha256 `ae38e415c79efd5592dcb9b658cdb99ddb11d4c4e1eaa364cab04a052473fc25`,
    which matches the Space's LFS pointer.
  - Why this model: it is the Space's default (`app.py`), and the model the author identifies as the best performing
    in issue 2 (comment of 28 April 2026, referring to `default_mode_name="YPTF.MoE+Multi (noPS)"`).
- **Settings:**
  - `app.py`'s arguments for that model, unchanged, with precision "16";
  - `transcribe()`'s steps: mono downmix, resampling to 16 kHz, segments of 32,767 samples, and
    `inference_file(bsz=8)`;
  - no parameter was tuned on any dataset here.
- **Audio:** read with soundfile as 32-bit floating point, as `torchaudio.load` would read it. Peaks above full scale in
  the separated pop stems are passed through, not clipped.

## Notes kept

YourMT3+ transcribes every instrument:
- Its vocabulary (`config/vocabulary.py`) reserves program 100 for "singing voice (melody)" and program 101 for
  "singing voice (chorus)".
- The authors' singing evaluation counts both (`SINGING_SOLO_CLASS = [100, 101]`).
- The adapter keeps programs 100 and 101, and discards all others, including drums.
- `adapter.json` records, for each recording, the number of notes in each program, so that the discarded notes are
  visible.

## Training data and the five evaluation datasets

From `amt/src/config/data_presets.py` (presets `all_cross_v6`, `all_cross_v7` and `all_cross_final`), and the paper
(arXiv 2407.04822, Table 1 and Section E):

| Dataset | Relation to YourMT3+'s data |
|---|---|
| MIR-ST500 test (songs 401–500) | **Not trained on, but used for validation.** `mir_st500_voc` trains on `train_vocal` (songs 1–400, vocals separated with Spleeter) and validates on `test_vocal` (songs 401–500); `preprocess_mir_st500.py` splits at song 401. The paper states that validation loss was used to tune sampling weights. Its MIR-ST500 score is therefore marked as trained on the same dataset (\*). |
| RWC-P | Not trained on: `rwc_pop_bass` and `rwc_pop_full` have `train_split: None`, and RWC-Pop is a test set in the paper. |
| vocadito, Molina, SSVD | Not mentioned in the source code or the paper. |

The training data also include singing from CMedia (100 songs from MIREX 2020), for training only.

## Licence

The code is GPL-3.0 (the GitHub repository's licence). The weights are distributed by the authors through the Space;
no separate licence for them is stated.

## Verification

Before the full run, the image was tested on two vocadito recordings (42.3 s of audio), scored against annotator 1:
- **Scores:** COnPOff 0.290, COnP 0.480 and COn 0.752 (scorer at commit 2985482).
- **Notes kept:** every note was in program 100 (61 and 26 notes), so none was discarded.
- **Speed and memory on the GPU:** 2.5 s per minute of audio after a model load of 2.5 s. PyTorch's peak allocation was
  1,515 MiB, against a card baseline of 403 MiB (2,288 MiB in total).
- **Network:** the image runs without network access (`--network none`).
