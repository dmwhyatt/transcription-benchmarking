# Tony (pYIN note tracker), 12 November 2026

What runs: the pYIN Vamp plugin's `notes` output, hosted by Sonic Annotator 1.7
(official release), with pYIN built at the commit Tony pins (c4dm/pyin
`1d68cac`, tag v1.2). CPU only, single-threaded, no checkpoint, no network.
GPL-2.0 (Tony, pYIN); Sonic Annotator GPL-2.0-or-later.

## Parameters, all from Tony's own source

`main/Analyser.cpp` (sonic-visualiser/tony, branch `default`), with Tony's
analysis settings at their defaults: step 256, block 2048, `precisetime` 0,
`lowampsuppression` 0.2 (the plugin's own default is 0.1), `onsetsensitivity`
0.7, `prunethresh` 0.1. Everything else is the plugin default at that commit
(`fixedlag` 1, `threshdistr` 2, `outputunvoiced` 0). Nothing tuned here.

`main/MainWindow.cpp` also conditions the audio: resample on load to a fixed
44100 Hz, and peak-normalise. The adapter does both (soxr VHQ; Sonic
Annotator `--normalise`). This matters: pYIN's low-amplitude suppression is an
absolute RMS threshold, so the unnormalised output depends on recording level.

## Circularity: do not report Tony on vocadito as a transcription result

vocadito (Bittner et al. 2021, sec. 2.2.2): "Note annotations were also
created using Tony, which similarly for f0, uses an algorithm to estimate note
events and allows an annotator to correct the estimates."

Measured on the smoke pair (vocadito_1, vocadito_2), this image's output
against the references:

| | A1 | A2 |
|---|---|---|
| reference onsets within 1 ms of a Tony onset, vocadito_1 | 0.86 | 0.72 |
| reference onsets within 1 ms of a Tony onset, vocadito_2 | 0.68 | 0.62 |
| COnPOff F, both recordings | 0.832 | 0.640 |

The references are, to the millisecond, largely Tony's output left as it was.
That also confirms this image reproduces Tony. Its vocadito scores measure how
much the annotators changed, not transcription.

Molina (Molina et al. 2014, sec. 2.2.2): "we have transcribed the audio
recordings with a baseline algorithm (Section 4.2), and then all the
transcription errors have been corrected by an expert musician". The baseline
is YIN with notes formed by rounding to the nearest MIDI note, not Tony (which
postdates it). But Tony's note defaults were chosen on Molina: Mauch et al.
2015, sec. 5.1, compare methods "using a publicly available dataset [24]"
([24] = Molina et al. 2014) and "ran 16 different versions of Tony's note
transcription algorithm, a grid search of 4 parameter settings for each of the
two post-processing methods"; s = 0.7 and 100 ms pruning come from that grid.
So Molina is Tony's development set, as vocadito and Molina are for transcPybe.

## Checks run

- Smoke: 2/2 vocadito files, 52 notes each; 0.59 and 0.55 s for 33 and 35 s of
  audio, about 1.0 s per minute of audio including Sonic Annotator's start-up.
- A 48 kHz stereo float copy of vocadito_1, scaled by 2.4, gave the same 52
  notes (all within 6 ms, same semitone), so the resample, mixdown and
  normalise path holds for the pop stems' formats.

## Output

`midi/<item>.mid` with pitch rounded to the nearest semitone, as every other
adapter writes it; `notes/<item>.csv` keeps pYIN's unrounded pitch
(onset_s, offset_s, midi_float) for any measured-pitch comparison.
