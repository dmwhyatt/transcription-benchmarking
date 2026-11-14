# Tony (pYIN note tracker)

Prepared 12 November 2026.

- **What runs:** the `notes` output of the pYIN Vamp plugin, hosted by Sonic Annotator 1.7 (official release). pYIN is
  built at the commit Tony pins (c4dm/pyin `1d68cac`, tag v1.2).
- **Execution:** CPU only and single-threaded, with no checkpoint and no network access.
- **Licences:** Tony and pYIN are GPL-2.0; Sonic Annotator is GPL-2.0 or later.

## Parameters

All parameters are taken from Tony's own source (`main/Analyser.cpp` in sonic-visualiser/tony, branch `default`), with
Tony's analysis settings at their defaults. None was tuned for this benchmark.

| Parameter | Value | Note |
|---|---|---|
| step | 256 | |
| block | 2048 | |
| `precisetime` | 0 | |
| `lowampsuppression` | 0.2 | the plugin's own default is 0.1 |
| `onsetsensitivity` | 0.7 | |
| `prunethresh` | 0.1 | |
| `fixedlag`, `threshdistr`, `outputunvoiced` | 1, 2, 0 | the plugin's defaults at that commit |

Tony also prepares the audio (`main/MainWindow.cpp`): it resamples to 44,100 Hz on loading, and normalises the peak
level. The adapter does both, with soxr at very high quality and Sonic Annotator's `--normalise`. Normalisation matters
because pYIN's low-amplitude suppression is an absolute RMS threshold, so without it the output would depend on the
recording level.

## Overlap with vocadito and Molina

### vocadito

vocadito's note annotations were made with Tony. Its paper (Bittner et al., 2021, section 2.2.2) states that note
annotations were created using Tony, which estimates note events and allows an annotator to correct them.

On two vocadito recordings, this image's output agrees with the references as follows:

| | Annotator 1 | Annotator 2 |
|---|---|---|
| Reference onsets within 1 ms of a Tony onset, vocadito_1 | 0.86 | 0.72 |
| Reference onsets within 1 ms of a Tony onset, vocadito_2 | 0.68 | 0.62 |
| COnPOff F, both recordings | 0.832 | 0.640 |

Two conclusions follow:
- Many reference onsets are Tony's output, unchanged to the millisecond.
- This image therefore reproduces Tony.

Tony's scores on vocadito measure how much the annotators changed its output, rather than transcription accuracy.
RESULTS.md therefore excludes vocadito from Tony's mean, and the README's table, which averages vocadito, Molina and
RWC-P, leaves Tony out.

### Molina

Molina's annotations were produced by correcting the output of a baseline algorithm: YIN, with notes formed by rounding
to the nearest MIDI note (Molina et al., 2014, section 2.2.2). That baseline is not Tony, which postdates it.

However, Tony's default note settings were selected on Molina's dataset. Mauch et al. (2015, section 5.1) compare
methods on that dataset, and ran sixteen versions of Tony's note transcription algorithm, a grid of four settings for
each of two post-processing methods. The onset sensitivity of 0.7 and the 100 ms pruning threshold come from that grid.
Molina is therefore a development set for Tony, as vocadito and Molina are for transcPybe.

## Verification

- **Speed:** both of the two vocadito recordings produced 52 notes, in 0.59 s and 0.55 s for 33 s and 35 s of audio.
  That is about 1.0 s per minute of audio, including Sonic Annotator's start-up.
- **Input formats:** a 48 kHz stereo floating-point copy of vocadito_1, scaled by 2.4, gave the same 52 notes, all
  within 6 ms and on the same semitone. Resampling, mixing down to mono and normalisation therefore behave as intended
  for the formats of the separated pop stems.

## Output

- `midi/<item>.mid`: pitch rounded to the nearest semitone, as every other adapter writes it.
- `notes/<item>.csv`: pYIN's unrounded pitch (`onset_s`, `offset_s`, `midi_float`), for comparisons that use measured
  pitch.
