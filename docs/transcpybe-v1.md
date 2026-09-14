# transcPybe v1 on vocadito, against nine other systems

Ten systems over the same forty recordings, scored against the same references
at the same tolerances, read against the same ceiling. This is the measurement
the survey in `docs/vocal-transcription-tools.md` was written to make possible,
and it fixes where transcPybe stands before anyone tries to improve it.

Run 14 September 2026. Orchestrator at `d7ec86f`, transcPybe at `6fe3e12`.

## The result

| system | COn F | COnP F | COnPOff F | octave err | offset |
|---|---|---|---|---:|---:|
| **transcpybe** | 0.710 [0.690-0.728] | **0.591 [0.569-0.613]** | 0.410 [0.382-0.438] | 0.1% | +0.003 |
| game | **0.755 [0.735-0.775]** | 0.587 [0.557-0.615] | 0.270 [0.245-0.297] | 0.0% | -0.015 |
| omnizart | 0.723 [0.697-0.750] | 0.581 [0.551-0.612] | 0.443 [0.405-0.483] | 0.0% | +0.010 |
| phoneme-informed | 0.731 [0.706-0.758] | 0.574 [0.540-0.608] | **0.450 [0.410-0.493]** | 0.8% | -0.010 |
| basic-pitch | 0.553 [0.523-0.582] | 0.486 [0.455-0.517] | 0.307 [0.277-0.337] | 1.5% | -0.020 |
| crepe-notes | 0.623 [0.598-0.646] | 0.477 [0.448-0.504] | 0.310 [0.278-0.341] | 0.1% | -0.010 |
| essentia | 0.669 [0.646-0.692] | 0.469 [0.440-0.498] | 0.318 [0.285-0.357] | 1.0% | -0.010 |
| mirst500 | 0.708 [0.680-0.736] | 0.467 [0.432-0.502] | 0.320 [0.287-0.354] | 1.2% | +0.020 |
| rosvot | 0.359 [0.329-0.389] | 0.262 [0.235-0.291] | 0.184 [0.163-0.207] | 0.0% | +0.075 |
| aubio | 0.435 [0.409-0.462] | 0.145 [0.127-0.163] | 0.061 [0.048-0.075] | 2.5% | -0.070 |
| *two annotators* | *0.817* | *0.740* | *0.642* | | |

40 recordings, 2237 reference notes. Macro mean over recordings, 95% bootstrap
interval over 2000 resamples. Bold marks the best in each column, which is not
the same as a winner -- see below.

## What this establishes

**The pipeline reproduces.** transcPybe scored 0.591 here; the hand-run figure
in `docs/benchmarking-rosvot.md` was 0.589. ROSVOT scored 0.262 against a
documented 0.262. Those runs went through an entirely different path -- one
container per system, mounted adapters, filenames rewritten to mirror the audio
tree -- and landed on the same numbers. The orchestration is not moving the
measurement.

**No system trained on vocadito.** Checked rather than assumed: Basic Pitch's
training registry names five datasets and vocadito is not among them, appearing
in that repository only as a test fixture. ROSVOT trained on M4Singer, the
york135 models on MIR-ST500. The comparison is legitimate on this corpus in a
way it would not be on either of those.

**Nothing is near the ceiling.** Two annotators agree at COnP 0.740. The best
system here reaches 0.591, which is 80% of the distance available. The
remaining headroom is smaller than the raw figures suggest, and a system
reporting far above 0.74 on this data has a scoring fault rather than a
remarkable model.

## What this does not establish

**That transcPybe is the best system here.** The top four are
0.591, 0.587, 0.581 and 0.574, with intervals that sit almost entirely on top
of one another. A 0.004 lead over GAME is not a result. Forty recordings
support "COnP 0.59, 95% CI 0.57-0.61"; they do not support "0.591 beats 0.587".

Separate intervals are also the wrong instrument: they count the difficulty of
each recording twice, once on each side. `bench.py compare` bootstraps the
*paired* difference, which is the question being asked and is far more
sensitive. **Until that has been run, the honest claim is that four systems are
indistinguishable at COnP on this corpus, and transcPybe is one of them.**

## Where transcPybe v1 actually stands

The interesting finding is not the ordering. It is that **transcPybe is not the
best at anything individually, and is the best at the combination.**

| | best | transcPybe | gap |
|---|---|---|---|
| onsets (COn) | game 0.755 | 0.710 | **-0.045** |
| onsets + pitch (COnP) | transcpybe 0.591 | 0.591 | -- |
| + offsets (COnPOff) | phoneme-informed 0.450 | 0.410 | **-0.040** |

GAME finds note boundaries better than transcPybe does. phoneme-informed and
omnizart (0.443) place note ends better. transcPybe leads on COnP because it is
strong on both and best at neither, and because its pitch stage is close to
clean -- 0.1% octave errors, bettered only by systems at 0.0%.

That decomposition is the roadmap, and it is two separate pieces of work:

1. **Onsets.** GAME is +0.045 COn ahead. It reaches that with a generative
   boundary model (D3PM over note boundaries) rather than an onset detector,
   which is an architectural difference and not a tuning one. Worth
   understanding before imitating.
2. **Offsets.** phoneme-informed is +0.040 COnPOff ahead while being *behind*
   on COnP, so it is placing note ends better without transcribing better
   overall. Its thesis is that singing onsets are linguistic events, and it
   feeds a phonetic posteriorgram alongside the mel spectrogram; whatever it
   gains there, transcPybe does not have.

The cheaper of the two is offsets. transcPybe's COnPOff/COnP ratio is 0.69;
phoneme-informed's is 0.78 and omnizart's 0.76. Closing that ratio alone,
without improving a single onset or pitch, would put COnPOff around 0.46.

**transcPybe's alignment is already right.** Its median best offset is +0.003 s
-- effectively zero, and the smallest in the table. It agrees with vocadito's
annotation convention, so none of its score is waiting on a correction.

## Caveats, each attached to a number

**GAME's offsets may be this repository's fault, not GAME's.** GAME publishes
no PyTorch checkpoint and ships no ONNX inference pipeline, so the adapter in
`orchestrator/images/game/` is an implementation of its `ONNX.md` spec written
here. The D3PM step count (10) is a guess, and the boundary threshold (0.2) and
radius (2) are the spec's recommended values rather than tuned ones. A system
that leads the table on COn and sits near the bottom on COnPOff is the profile
of a duration bug. Sweep those before concluding anything about GAME's offsets.

**ROSVOT's 0.262 is uncorrected and understates it.** Its +0.075 s offset is
the largest here, and it is the M4Singer convention travelling with the model:
a note there begins at the syllable including its leading consonant, where
vocadito annotates from pitch. The same correction in
`docs/benchmarking-rosvot.md` took it from 0.262 to 0.355. That rescoring has
not been redone in this run, so the row above should be read as the
uncorrected figure and not as ROSVOT's fair score.

**transcPybe ran on its defaults, and that is checkable rather than
asserted.** The adapter passes `--f0-backend crepe --device auto` and nothing
else; `bench-work/out/transcpybe/adapter.json` records `extra_args: []` for the
run. Its `TranscriptionConfig` documents each default on domain grounds -- 16
kHz because that is what CREPE was trained at, A1 as a floor because below it
is almost never sung pitch -- rather than as the output of a sweep. So 0.591 is
an out-of-the-box number, which makes it a stronger result than a tuned one and
not a weaker one: every other system here also ran on its published defaults.

The package does ship `transcpybe-tune`, and its README demonstrates it against
vocadito, so the capability to tune on this corpus exists and has not been used
for this figure. Worth stating explicitly in any write-up, because a reader who
notices that the benchmark and the transcriber share an author will ask.

What remains true is narrower: vocadito is the corpus transcPybe was developed
alongside, and a system's home corpus flatters it in ways that have nothing to
do with parameter sweeps -- the failure modes its author noticed are the ones
these forty recordings contain. A second corpus, M4Singer or MIR-ST500's test
split, would turn "best on vocadito" into evidence about the method. That is a
generalisation question now, not a contamination one.

**aubio is the floor and behaves like it.** COnP 0.145, 2.5% octave errors, and
a -0.070 s offset from merging legato runs into single long notes. It is in
the table so that "better than a classical onset-detection pipeline" is a
measured claim rather than an assumption.

## Reproducing this

```shell
cd orchestrator
export TRANSCPYBE_SRC=~/transcpybe
./bench.py doctor
./bench.py build --prune
./bench.py fetch                    # rosvot needs a human; the rest are automatic
./bench.py transcribe --audio ~/vocadito/
./bench.py score --audio ~/vocadito/Audio -a ~/vocadito/Annotations
./bench.py table
./bench.py compare
```

Transcription takes about 70 minutes on one RTX 3080, of which omnizart is 39.
Each system's `run.json` records the image id, the exact command, and the
wall clock; each `adapter.json` records per-item status.

## What to do next, in order

1. **Run `compare`.** Four systems are tied on this evidence and the paired
   test is what separates them. Everything in this document that sounds like a
   ranking is waiting on it.
2. **Rescore ROSVOT with `--onset-shift`,** so its row is a fair one.
3. **Sweep GAME's `GAME_STEPS`, `GAME_THRESHOLD`, `GAME_RADIUS`,** to find out
   whether its weak offsets are its own.
4. **Score transcPybe on a second corpus.** Not because this one is
   contaminated -- it ran on defaults, and nothing here trained on vocadito --
   but because one corpus cannot separate a good method from a method suited
   to forty particular recordings.
5. Then improve it, against this table rather than against a feeling.
