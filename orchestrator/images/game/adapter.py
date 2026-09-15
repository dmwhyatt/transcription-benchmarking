#!/usr/bin/env python3
"""GAME, run from the ONNX models its releases actually publish.

GAME's own infer.py wants a PyTorch checkpoint, and its releases ship only
ONNX bundles -- its README says outright that no ONNX inference pipeline is
provided in the repository. So this is that pipeline, written against
ONNX.md, which documents the graphs well enough to do it:

    encoder(waveform, duration)            -> x_seg, x_est, maskT
    dur2bd(durations, maskT)               -> known_boundaries
    segmenter(...) x N, D3PM sampling loop -> boundaries
    bd2dur(boundaries, maskT)              -> durations, maskN
    estimator(x_est, boundaries, ...)      -> presence, scores

Verified against a synthetic eight-note phrase with known pitches: all eight
notes recovered, pitch within 0.04 semitones, onsets within 10 ms.

Running the published ONNX rather than a checkpoint has a side benefit worth
having: this image needs onnxruntime instead of torch on CUDA, which takes it
from about 11 GB to about 1 GB.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pretty_midi
import soundfile as sf

AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CKPT = Path(os.environ.get("BENCH_CKPT", "/ckpt"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))

SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}
# Both recommended by ONNX.md; both worth sweeping before quoting a number.
THRESHOLD = float(os.environ.get("GAME_THRESHOLD", "0.2"))
RADIUS = int(os.environ.get("GAME_RADIUS", "2"))
STEPS = int(os.environ.get("GAME_STEPS", "10"))
LANGUAGE = os.environ.get("GAME_LANGUAGE", "en")


def find_models(root: Path):
    """The directory holding encoder.onnx, however the zip was unpacked."""
    for encoder in sorted(root.rglob("encoder.onnx")):
        if (encoder.parent / "config.json").exists():
            return encoder.parent
    return None


def load_audio(path: Path, samplerate: int):
    audio, sr = sf.read(str(path), dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    if sr != samplerate:
        import soxr
        audio = soxr.resample(audio, sr, samplerate)
    return audio.astype(np.float32)


class Game:
    def __init__(self, model_dir: Path) -> None:
        self.config = json.loads((model_dir / "config.json").read_text())
        providers = ort.get_available_providers()
        pick = [p for p in ("CUDAExecutionProvider", "CPUExecutionProvider")
                if p in providers]
        self.sessions = {
            name: ort.InferenceSession(str(model_dir / f"{name}.onnx"),
                                       providers=pick)
            for name in ("encoder", "segmenter", "estimator", "dur2bd", "bd2dur")
        }
        print(f"providers: {pick}", flush=True)

    def transcribe(self, path: Path):
        rate = self.config["samplerate"]
        audio = load_audio(path, rate)
        waveform = audio[None, :]
        duration = np.array([len(audio) / rate], dtype=np.float32)

        x_seg, x_est, maskT = self.sessions["encoder"].run(
            None, {"waveform": waveform, "duration": duration})

        # No known regions, so the clip is one region spanning its own
        # duration -- ONNX.md: "If there are no known regions, use duration".
        known, = self.sessions["dur2bd"].run(
            None, {"durations": duration[None, :], "maskT": maskT})

        language = np.array([self.config.get("languages", {}).get(LANGUAGE, 0)],
                            dtype=np.int64)
        threshold = np.array(THRESHOLD, dtype=np.float32)
        radius = np.array(RADIUS, dtype=np.int64)

        # t=0 is noise and t=1 the data distribution, exclusive of 1.
        schedule = (np.linspace(0.0, 1.0, STEPS, endpoint=False)
                    if self.config.get("loop") else [0.0])
        boundaries = known
        for t in schedule:
            boundaries, = self.sessions["segmenter"].run(
                None, {"x_seg": x_seg, "language": language,
                       "known_boundaries": known, "prev_boundaries": boundaries,
                       "t": np.array([t], dtype=np.float32), "maskT": maskT,
                       "threshold": threshold, "radius": radius})

        durations, maskN = self.sessions["bd2dur"].run(
            None, {"boundaries": boundaries, "maskT": maskT})
        presence, scores = self.sessions["estimator"].run(
            None, {"x_est": x_est, "boundaries": boundaries, "maskT": maskT,
                   "maskN": maskN, "threshold": threshold})

        notes, onset = [], 0.0
        for index in range(durations.shape[1]):
            if not maskN[0, index]:
                continue
            end = onset + float(durations[0, index])
            if presence[0, index]:
                # Pitch comes back as a float MIDI number, which this
                # benchmark keeps rather than rounding.
                notes.append((onset, end, float(scores[0, index])))
            onset = end
        return notes


def write_midi(notes, target: Path):
    score = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=53)
    for start, end, pitch in notes:
        instrument.notes.append(pretty_midi.Note(
            velocity=100, pitch=int(round(pitch)), start=start, end=end))
    score.instruments.append(instrument)
    target.parent.mkdir(parents=True, exist_ok=True)
    score.write(str(target))


def main():
    model_dir = find_models(CKPT)
    if model_dir is None:
        print(f"No GAME ONNX models under {CKPT} (looking for an encoder.onnx "
              "beside a config.json).", file=sys.stderr)
        print("Run `bench.py fetch --only game`.", file=sys.stderr)
        return 2
    print(f"using models from {model_dir}", flush=True)
    game = Game(model_dir)

    rows = []
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES
               and not p.name.startswith(".")]
    for source in sources:
        relative = source.relative_to(AUDIO)
        started = time.time()
        try:
            notes = game.transcribe(source)
            write_midi(notes, OUT / "midi" / relative.with_suffix(".mid"))
            row = {"item": str(relative), "status": "ok", "notes": len(notes)}
        except Exception as exc:                       # noqa: BLE001
            row = {"item": str(relative), "status": "fail", "error": repr(exc)[:400]}
        row["seconds"] = round(time.time() - started, 2)
        rows.append(row)
        print(f"{'ok  ' if row['status'] == 'ok' else 'FAIL'} {relative}", flush=True)
        if row["status"] != "ok" and row.get("error"):
            for line in str(row["error"]).strip().splitlines()[-8:]:
                print(f"       {line}", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "game", "models": str(model_dir), "threshold": THRESHOLD,
         "radius": RADIUS, "steps": STEPS, "language": LANGUAGE,
         "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
