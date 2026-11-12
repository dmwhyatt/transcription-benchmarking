# YourMT3+ in this benchmark

Prepared 12 November 2026 on musix, and run on all five sets the same day. Its scores and timing are in the
README's results table; the smoke test below came first.

## What runs

- Code: the authors' HuggingFace Space `mimbres/YourMT3`, revision
  `5e66c1ea173a8186e0d20432b841d3180cc015b5` (31 Jan 2025), `amt/src` plus
  `model_helper.py`, code only. The GitHub repo (`mimbres/YourMT3`, 8a4fbca)
  holds a README and points to the Space as the pre-release code (issue #2).
- Model: "YPTF.MoE+Multi (noPS)", checkpoint
  `mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops/checkpoints/last.ckpt`,
  561,544,628 bytes, sha256 `ae38e415c79efd5592dcb9b658cdb99ddb11d4c4e1eaa364cab04a052473fc25`
  (matches the Space's LFS pointer). Chosen because it is the Space's default
  (`app.py`) and the model the author names as best-performing in issue #2
  (comment of 28 April 2026, pointing to `default_mode_name="YPTF.MoE+Multi (noPS)"`).
- Settings: `app.py`'s argument list for that model verbatim, precision "16",
  and `transcribe()`'s steps (mono downmix, resample to 16 kHz, 32767-sample
  segments, `inference_file(bsz=8)`). Nothing tuned on any set here.
- Audio is read with soundfile as float32, as `torchaudio.load` would; peaks
  above full scale in the float pop stems are passed through, not clipped.

## Which notes are kept

YourMT3+ transcribes every instrument. Its vocabulary reserves program 100 for
"singing voice (melody)" and 101 for "singing voice (chorus)"
(`config/vocabulary.py`); the authors' singing evaluation counts both
(`SINGING_SOLO_CLASS = [100, 101]`). The adapter keeps programs 100 and 101 and
drops everything else, drums included. `adapter.json` records, per item, how
many notes fell in each program, so what was dropped is visible.

Smoke (vocadito_1, vocadito_10): every note was program 100 (61 and 26); none
dropped.

## Training data, and what it means for our five sets

From `amt/src/config/data_presets.py` (presets `all_cross_v6` / `all_cross_v7` /
`all_cross_final`) and the paper (arXiv 2407.04822, Table 1, Section E):

| Our set | In YourMT3+'s data? |
|---|---|
| MIR-ST500 test (songs 401-500) | **Not trained on, but used as its validation split.** `mir_st500_voc` trains on `train_vocal` (songs 1-400, Spleeter vocals) and validates on `test_vocal` (songs 401-500); `preprocess_mir_st500.py` splits at id 401. The paper says validation loss was used to tune sampling weights. Mark its MIR-ST500 score as trained on the same dataset (*). |
| RWC-P | Not trained on: `rwc_pop_bass` / `rwc_pop_full` have `train_split: None`; RWC-Pop is a test set in the paper. |
| vocadito, Molina, SSVD | Not mentioned anywhere in the source or the paper. |

Other singing in the mix: CMedia (100 MIREX 2020 songs, vocals), training only.

## Licence

GPL-3.0 (GitHub repo LICENSE). Weights are distributed by the authors on the
Space; no separate weight licence is stated.

## Smoke result

2 vocadito recordings (42.3 s of audio), annotator A1: COnPOff 0.290, COnP 0.480,
COn 0.752 (scorer at commit 2985482). GPU: 2.5 s per minute of audio after a
2.5 s model load; torch peak allocation 1,515 MiB, card use 2,288 MiB against a
403 MiB baseline. Offline (`--network none`) works.
