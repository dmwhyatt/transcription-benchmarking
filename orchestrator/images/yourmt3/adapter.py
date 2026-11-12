#!/usr/bin/env python3
"""Run YourMT3+ over /audio, keeping only the notes it labels as singing.

The model is loaded once, the way the authors' Space loads it
(app.py, model "YPTF.MoE+Multi (noPS)", precision "16"), and each file goes
through the Space's own transcribe() steps: downmix to mono, resample to
16 kHz, slice into 32767-sample segments, inference_file(bsz=8), detokenize
each of the 13 decoding channels, merge, mix. Nothing here is tuned.

YourMT3+ transcribes every instrument it hears. Its vocabulary reserves
program 100 for "singing voice (melody)" and 101 for "singing voice
(chorus)" (config/vocabulary.py), and the authors' own singing evaluation
counts both (SINGING_SOLO_CLASS = [100, 101]). So this adapter keeps notes
with program 100 or 101 and drops everything else, drums included; the
per-item tally of what was dropped is in adapter.json.

The Space reads its checkpoint from amt/logs/<project>/<exp>/checkpoints/
relative to the working directory, so the adapter builds that path under
/cache as a symlink to whatever .ckpt it finds under /ckpt.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CKPT = Path(os.environ.get("BENCH_CKPT", "/ckpt"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))
APP = Path(os.environ.get("YMT3_APP", "/app"))
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}

MODEL_NAME = "YPTF.MoE+Multi (noPS)"
EXP = "mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops"
PROJECT = "2024"
PRECISION = "16"
# app.py's argument list for this model, verbatim apart from the checkpoint id.
ARGS = [f"{EXP}@last.ckpt", "-p", PROJECT, "-tk", "mc13_full_plus_256", "-dec", "multi-t5",
        "-nl", "26", "-enc", "perceiver-tf", "-sqr", "1", "-ff", "moe",
        "-wf", "4", "-nmoe", "8", "-kmoe", "2", "-act", "silu", "-epe", "rope",
        "-rp", "1", "-ac", "spec", "-hop", "300", "-atc", "1", "-pr", PRECISION]
SINGING = {100, 101}


def items():
    return [p for p in sorted(AUDIO.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUFFIXES
            and not p.name.startswith(".")]


def find_checkpoint():
    found = sorted(CKPT.rglob("*.ckpt"))
    preferred = [p for p in found if EXP in str(p)]
    return (preferred or found or [None])[0]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_empty_midi(target: Path):
    import mido
    mid = mido.MidiFile(ticks_per_beat=480)
    mid.tracks.append(mido.MidiTrack())
    mid.save(str(target))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    checkpoint = find_checkpoint()
    if checkpoint is None:
        problem = f"no .ckpt under {CKPT}"
        print(f"FAIL {problem}", flush=True)
        (OUT / "adapter.json").write_text(json.dumps(
            {"system": "yourmt3", "error": problem, "items": []}, indent=2))
        return 1

    run = CACHE / "ymt3"
    link = run / "amt" / "logs" / PROJECT / EXP / "checkpoints" / "last.ckpt"
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(checkpoint)
    os.chdir(run)
    sys.path.insert(0, str(APP))

    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio
    from model_helper import load_model_checkpoint  # the Space's own loader
    from utils.audio import slice_padded_array
    from utils.event2note import merge_zipped_note_events_and_ties_to_notes
    from utils.note2event import mix_notes
    from utils.utils import write_model_output_as_midi

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"checkpoint: {checkpoint}", flush=True)
    print(f"device: {device}", flush=True)
    started = time.time()
    model = load_model_checkpoint(args=ARGS, device="cpu")
    model.to(device)
    load_seconds = round(time.time() - started, 2)
    sr_model = model.audio_cfg["sample_rate"]
    frames = model.audio_cfg["input_frames"]

    rows = []
    for source in items():
        relative = source.relative_to(AUDIO)
        target = OUT / "midi" / relative.with_suffix(".mid")
        target.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        row = {"item": str(relative)}
        try:
            x, sr = sf.read(str(source), dtype="float32", always_2d=True)
            row["audio_seconds"] = round(len(x) / sr, 3)
            audio = torch.from_numpy(x.T.copy()).mean(dim=0).unsqueeze(0)
            audio = torchaudio.functional.resample(audio, sr, sr_model)
            segments = slice_padded_array(audio, frames, frames)
            segments = torch.from_numpy(segments.astype("float32")).to(device).unsqueeze(1)
            with torch.no_grad():
                pred_token_arr, _ = model.inference_file(bsz=8, audio_segments=segments)
            n_items = segments.shape[0]
            start_secs = [frames * i / sr_model for i in range(n_items)]
            per_channel = []
            for ch in range(model.task_manager.num_decoding_channels):
                arr_ch = [arr[:, ch, :] for arr in pred_token_arr]
                zipped, _, _ = model.task_manager.detokenize_list_batches(
                    arr_ch, start_secs, return_events=True)
                notes_ch, _ = merge_zipped_note_events_and_ties_to_notes(zipped)
                per_channel.append(notes_ch)
            notes = mix_notes(per_channel)
            tally = Counter("drum" if n.is_drum else int(n.program) for n in notes)
            kept = [n for n in notes if not n.is_drum and int(n.program) in SINGING]
            if kept:
                with tempfile.TemporaryDirectory(dir=str(CACHE)) as tmp:
                    write_model_output_as_midi(kept, tmp, "item", model.midi_output_inverse_vocab)
                    shutil.move(str(Path(tmp, "model_output", "item.mid")), str(target))
            else:
                write_empty_midi(target)
            row.update(status="ok", notes_kept=len(kept),
                       notes_by_program={str(k): v for k, v in sorted(tally.items(), key=str)})
        except Exception as exc:  # one recorded failure, not an abandoned sweep
            import traceback
            row.update(status="fail", stderr=traceback.format_exc()[-3000:])
        row["seconds"] = round(time.time() - t0, 2)
        rows.append(row)
        print(f"{'ok  ' if row['status'] == 'ok' else 'FAIL'} {relative} "
              f"{row.get('notes_kept', '')} kept {row.get('notes_by_program', '')} "
              f"{row['seconds']} s", flush=True)
        if row["status"] != "ok":
            print(row["stderr"], flush=True)

    peak = torch.cuda.max_memory_allocated() // (1 << 20) if device == "cuda" else None
    revision = APP / "REVISION"
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "yourmt3",
         "model": MODEL_NAME,
         "source": "huggingface.co/spaces/mimbres/YourMT3",
         "source_revision": revision.read_text().strip() if revision.exists() else "",
         "checkpoint": str(checkpoint),
         "checkpoint_sha256": sha256(checkpoint),
         "args": ARGS,
         "device": device,
         "torch_peak_allocated_mib": peak,
         "load_seconds": load_seconds,
         "kept_programs": sorted(SINGING),
         "items": rows}, indent=2))
    failed = [r for r in rows if r["status"] != "ok"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} transcribed; peak torch allocation {peak} MiB")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
