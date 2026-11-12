#!/usr/bin/env python3
"""STARS over /audio, by the route its repository gives for audio without lyrics.

STARS cannot transcribe from audio alone. At inference it force-aligns a
phoneme sequence to the audio (Viterbi over its frame-level phoneme logits),
feeds features pooled over the aligned phoneme and word spans to its note
decoder, and regulates the decoded notes against the aligned word boundaries
before writing MIDI. Its metadata must therefore carry `word`, `ph` and
`ph2words`, and none of the benchmark's corpora come with lyrics. The paper
says the lyrics "can be obtained using ASR models", and the repository's
scripts/process_ch.py does exactly that, so this adapter follows it:

  1. cut each recording into 8-20 s segments with FunASR's fsmn-vad, using
     process_ch.cut_long_audio unchanged (a recording of 20 s or less is kept
     whole, and each cut is widened by 100 ms either side);
  2. transcribe each segment with SenseVoiceSmall, with process_ch's own
     generate() arguments (language "auto");
  3. phonemise the text with scripts/mixedtext2phoneme.py, the phonemiser the
     README gives for the bilingual model, at its CLI defaults (no tones,
     English dictionary for Latin script, letters for words not in it);
  4. run inference/stars.py with the bilingual checkpoint, its config and phone
     set, at the authors' defaults (--thr 0.85, note regulation on);
  5. shift each segment's notes by where the segment starts, and write one MIDI
     per recording.

process_ch is written for the Chinese model and phonemises with its own
Chinese-only processor; steps 1 and 2 are its, step 3 is swapped for the
README's mixed-text phonemiser because the bilingual checkpoint is the one run.

A segment for which ASR returns no text, or text that phonemises to nothing, is
dropped, as process_ch drops it, and its notes are lost. So is a segment none of
whose phones is in the bilingual phone set (SenseVoice writes Korean or kana for
some singing, which the phonemiser passes through as unknown tokens): the
aligner discards unknown phones and <SP>, and with nothing left it raises
(perform_viterbi_bd indexes the first remaining label). That is the same kind of
drop, made before stars.py sees the segment rather than by its crashing; a
segment with more phones than frames is dropped for the same reason.

stars.py runs every segment in one process, so one segment that raises loses
them all. If a run fails, the segments are split -- by recording first, then
within a recording -- and each half is run again, down to single segments; a
segment that fails alone is recorded and its notes are lost. The splitting
stops after MAX_RUNS processes, so a failure that is not about any one segment
cannot turn into hundreds of model loads.

A recording left with no notes still gets an empty MIDI file, so it scores zero
rather than being skipped; adapter.json counts every kind of drop, per recording.

Paths are the container's by default and overridable by environment.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

AUDIO = Path(os.environ.get("BENCH_AUDIO", "/audio"))
OUT = Path(os.environ.get("BENCH_OUT", "/out"))
CKPT = Path(os.environ.get("BENCH_CKPT", "/ckpt"))
CACHE = Path(os.environ.get("BENCH_CACHE", "/cache"))
APP = Path(os.environ.get("STARS_APP", "/app"))
SUFFIXES = {".wav", ".flac", ".mp3", ".m4a", ".ogg", ".aif", ".aiff"}
CHECKPOINT = "stars_chinese_english_bilingual/model_ckpt_steps_300000.ckpt"
CONFIG = "stars_bilingual.yaml"
PHSET = "chinese_and_english_phone_set.json"
MAX_RUNS = 40


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_dir(name):
    """The directory holding <name>/model.pt under /ckpt, at any depth."""
    hits = sorted(CKPT.rglob(f"{name}/model.pt"))
    return hits[0].parent if hits else None


def item_name(relative: Path) -> str:
    # Unique across nested directories, and free of the brackets and spaces
    # that stars.py's "<item>[P].mid" naming and process_ch's "<stem>_<i>.wav"
    # naming would trip over.
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(relative.with_suffix("")).replace("/", "__"))


def pcm_copy(source: Path, target: Path) -> float:
    """A mono 16-bit copy for pydub, which reads PCM WAV only.

    Stems separated from a mix are float and can peak above full scale; those
    are scaled to a 0.99 peak rather than clipped. Returns the duration in s.
    """
    import numpy as np
    import soundfile as sf
    x, sr = sf.read(str(source), dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak > 1.0:
        x = x * (0.99 / peak)
    target.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(target), x, sr, subtype="PCM_16")
    return len(x) / sr


def rewrite_config(workdir: Path) -> Path:
    """The bilingual config with its paths made to resolve inside the container.

    stars.py builds its dataset's phone encoder from
    <processed_data_dir>/phone_set.json, a training-time directory the
    repository does not ship; it is pointed at a copy of the phone set passed as
    --phset, so the two encoders agree. pe_ckpt, and any other value under
    checkpoints/, is looked up under /ckpt.
    """
    import shutil
    import yaml
    workdir.mkdir(parents=True, exist_ok=True)
    for sibling in (APP / "configs").glob("*.yaml"):
        shutil.copy2(sibling, workdir / sibling.name)
    phset_dir = workdir / "phset"
    phset_dir.mkdir(exist_ok=True)
    shutil.copy2(APP / PHSET, phset_dir / "phone_set.json")
    target = workdir / CONFIG
    loaded = yaml.safe_load(target.read_text()) or {}
    loaded["processed_data_dir"] = str(phset_dir)
    for key, value in list(loaded.items()):
        if isinstance(value, str) and value.startswith("checkpoints/"):
            found = sorted(CKPT.rglob(value[len("checkpoints/"):]))
            if not found:
                raise SystemExit(f"config wants {value}; nothing under {CKPT} matches")
            loaded[key] = str(found[0])
            print(f"config: {key} -> {found[0]}", flush=True)
    target.write_text(yaml.safe_dump(loaded, sort_keys=False))
    return target


def main():
    sources = [p for p in sorted(AUDIO.rglob("*"))
               if p.is_file() and p.suffix.lower() in SUFFIXES and not p.name.startswith(".")]
    if not sources:
        print("no audio under /audio", file=sys.stderr)
        return 2
    stars_ckpt = sorted(CKPT.rglob(CHECKPOINT))
    vad_dir, asr_dir = find_dir("fsmn-vad"), find_dir("SenseVoiceSmall")
    missing = [n for n, v in (("STARS bilingual checkpoint", stars_ckpt), ("fsmn-vad", vad_dir),
                              ("SenseVoiceSmall", asr_dir), ("rmvpe", find_dir("rmvpe"))) if not v]
    if missing:
        print(f"missing under {CKPT}: {', '.join(missing)}. Run fetch.sh (see the Dockerfile).",
              file=sys.stderr)
        return 2
    stars_ckpt = stars_ckpt[0]

    os.chdir(APP)                      # mixedtext2phoneme opens ./mfa_dict/...
    sys.path.insert(0, str(APP))
    pc = load_module("process_ch", APP / "scripts" / "process_ch.py")
    mt = load_module("mixedtext2phoneme", APP / "scripts" / "mixedtext2phoneme.py")

    # process_ch names its models by hub ID ("fsmn-vad", "iic/SenseVoiceSmall"),
    # which FunASR would download. The container is offline, so the same
    # models are served from /ckpt; nothing else about the calls changes.
    hub_auto_model = pc.AutoModel
    local = {"fsmn-vad": str(vad_dir), "iic/SenseVoiceSmall": str(asr_dir)}

    def auto_model(model, **kwargs):
        return hub_auto_model(model=local.get(model, model), disable_update=True, **kwargs)
    pc.AutoModel = auto_model

    work = CACHE / "stars"
    timings, rows, segments = {}, {}, []

    # 1. cut
    started = time.time()
    total_audio_s = 0.0
    for source in sources:
        relative = source.relative_to(AUDIO)
        name = item_name(relative)
        rows[name] = {"item": str(relative), "segments": 0, "segments_without_text": 0,
                      "segments_unalignable": 0, "segments_failed": 0, "notes": 0}
        copy = work / "pcm" / f"{name}.wav"
        total_audio_s += pcm_copy(source, copy)
        try:
            cuts = pc.cut_long_audio(str(copy), str(work / "cut" / name))
        except Exception as error:     # process_ch skips such a file and goes on
            rows[name].update(status="fail", error=f"cutting failed: {error}")
            continue
        for path, start_ms, end_ms in cuts:
            segments.append({"item": name, "path": path, "start_ms": start_ms, "end_ms": end_ms})
        rows[name]["segments"] = len(cuts)
    timings["cut"] = time.time() - started
    print(f"{len(segments)} segments from {len(sources)} recordings "
          f"({total_audio_s / 60:.1f} min of audio)", flush=True)

    # 2-3. lyrics, then phonemes
    started = time.time()
    asr = pc.AutoModel(model="iic/SenseVoiceSmall", device="cuda:0")
    import yaml
    # PhoneEncoder's ids: 0 is <Blank> (anything unknown), then the phone set in
    # order, so <SP> is 1. The aligner keeps only ids above 1.
    phone_id = {tok: i + 1 for i, tok in enumerate(json.loads((APP / PHSET).read_text()))}
    config = yaml.safe_load((APP / "configs" / CONFIG).read_text())
    frames_per_s = config["audio_sample_rate"] / config["hop_size"]
    zh_args = {"use_tone": False, "with_phsep": False, "add_eos_bos": False}
    latin_args = {"latin_lang": "english", "with_phsep": False, "add_eos_bos": False}
    metadata = []
    for segment in segments:
        text = ""
        try:
            result = asr.generate(input=segment["path"], cache={}, language="auto",
                                  use_itn=False, batch_size_s=60, ban_emo_unk=True)
            if result and result[0].get("text"):
                text = pc.remove_emojis_simple(pc.rich_transcription_postprocess(result[0]["text"]))
            struct, _ = mt.process_mixed(text, zh_args, latin_args)
            words, phs, ph2word, _ = mt.get_phone(struct)
        except Exception as error:
            print(f"{Path(segment['path']).name}: {error}", flush=True)
            words, phs, ph2word = [], [], []
        segment["text"] = text
        if not phs:
            rows[segment["item"]]["segments_without_text"] += 1
            continue
        alignable = sum(1 for p in phs if phone_id.get(p, 0) > 1)
        frames = int((segment["end_ms"] - segment["start_ms"]) / 1000 * frames_per_s)
        if alignable == 0 or alignable > frames:
            segment["dropped"] = ("no phone in the phone set" if alignable == 0
                                  else f"{alignable} phones for {frames} frames")
            rows[segment["item"]]["segments_unalignable"] += 1
            continue
        segment["name"] = Path(segment["path"]).stem
        metadata.append({"item_name": segment["name"], "wav_fn": segment["path"],
                         "word": words, "ph": phs, "ph2words": ph2word})
    del asr
    import torch
    torch.cuda.empty_cache()
    timings["asr"] = time.time() - started
    work.mkdir(parents=True, exist_ok=True)
    (work / "segments.json").write_text(json.dumps(segments, indent=1, ensure_ascii=False))
    meta_path = work / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=1, ensure_ascii=False))
    unalignable = sum(1 for s in segments if "dropped" in s)
    print(f"{len(metadata)} of {len(segments)} segments have lyrics to align "
          f"({len(segments) - len(metadata) - unalignable} without text, {unalignable} with no "
          f"alignable phone)", flush=True)

    # 4. STARS
    started = time.time()
    seg_item = {s["name"]: s["item"] for s in segments if "name" in s}
    runs, failed, done = [], {}, {}
    if metadata:
        config_path = rewrite_config(work / "config")
        pending = [metadata]
        while pending:
            entries = pending.pop(0)
            if len(runs) >= MAX_RUNS:
                for e in entries:
                    failed[e["item_name"]] = f"not run: {MAX_RUNS} stars.py processes already started"
                continue
            k = len(runs)
            run_dir, meta = work / "infer" / f"run{k:03d}", work / "meta" / f"run{k:03d}.json"
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_text(json.dumps(entries, indent=1, ensure_ascii=False))
            argv = ["python3", "inference/stars.py", "--ckpt", str(stars_ckpt),
                    "--config", str(config_path), "--phset", str(APP / PHSET),
                    "-o", str(run_dir), "--metadata", str(meta), "-v"]
            proc = subprocess.run(argv, cwd=str(APP), capture_output=True, text=True,
                                  env={**os.environ, "CUDA_VISIBLE_DEVICES": "0"})
            aligned = set()
            if proc.returncode == 0 and (run_dir / "output.json").exists():
                aligned = {r["item_name"] for r in json.loads((run_dir / "output.json").read_text())}
            wanted = {e["item_name"] for e in entries}
            runs.append({"run": k, "segments": len(entries), "exit": proc.returncode,
                         "aligned": len(aligned & wanted)})
            print(f"run{k:03d}: {len(entries)} segments, exit {proc.returncode}, "
                  f"{len(aligned & wanted)} aligned", flush=True)
            if wanted <= aligned:
                done.update({name: run_dir for name in wanted})
                continue
            tail = [line for line in proc.stderr.strip().splitlines() if line.strip()]
            print(f"--- run{k:03d} stderr, last 1500 chars ---\n{proc.stderr[-1500:]}", flush=True)
            if len(entries) == 1:
                failed[entries[0]["item_name"]] = tail[-1] if tail else f"exit {proc.returncode}"
                continue
            recordings = list(dict.fromkeys(seg_item[e["item_name"]] for e in entries))
            if len(recordings) > 1:      # split by recording first
                first = set(recordings[: len(recordings) // 2])
                halves = ([e for e in entries if seg_item[e["item_name"]] in first],
                          [e for e in entries if seg_item[e["item_name"]] not in first])
            else:
                halves = (entries[: len(entries) // 2], entries[len(entries) // 2:])
            pending[:0] = [h for h in halves if h]
    for name in failed:
        rows[seg_item[name]]["segments_failed"] += 1
    timings["stars"] = time.time() - started

    # 5. stitch
    import pretty_midi
    by_item = {}
    for segment in segments:
        if "name" in segment:
            by_item.setdefault(segment["item"], []).append(segment)
    for name, row in rows.items():
        if row.get("status") == "fail":
            continue
        merged = pretty_midi.PrettyMIDI()
        voice = pretty_midi.Instrument(program=0)
        for segment in by_item.get(name, []):
            if segment["name"] not in done:    # failed, and counted as failed
                continue
            midi = done[segment["name"]] / "midi" / f"{segment['name']}[P].mid"
            if not midi.exists():          # save_midi writes nothing for no notes
                continue
            offset = segment["start_ms"] / 1000.0
            for instrument in pretty_midi.PrettyMIDI(str(midi)).instruments:
                for note in instrument.notes:
                    voice.notes.append(pretty_midi.Note(velocity=note.velocity, pitch=note.pitch,
                                                        start=note.start + offset, end=note.end + offset))
        voice.notes.sort(key=lambda n: (n.start, n.pitch))
        merged.instruments.append(voice)
        target = OUT / "midi" / Path(row["item"]).with_suffix(".mid")
        target.parent.mkdir(parents=True, exist_ok=True)
        merged.write(str(target))
        row.update(status="ok", notes=len(voice.notes))

    OUT.mkdir(parents=True, exist_ok=True)
    rows_list = list(rows.values())
    (OUT / "adapter.json").write_text(json.dumps(
        {"system": "stars", "checkpoint": CHECKPOINT, "seconds": round(sum(timings.values()), 1),
         "stage_seconds": {k: round(v, 1) for k, v in timings.items()},
         "audio_minutes": round(total_audio_s / 60, 2),
         "segments": len(segments),
         "segments_without_text": len(segments) - len(metadata) - unalignable,
         "segments_unalignable": unalignable, "segments_failed": len(failed),
         "failed_segments": failed, "stars_runs": runs,
         "dropped_segments": {s["name"] if "name" in s else Path(s["path"]).stem: s["dropped"]
                              for s in segments if "dropped" in s},
         "items": rows_list}, indent=2, ensure_ascii=False))
    failed_rows = [r for r in rows_list if r.get("status") != "ok"]
    empty = [r for r in rows_list if r.get("status") == "ok" and r["notes"] == 0]
    print(f"\n{len(rows_list) - len(failed_rows)}/{len(rows_list)} transcribed; {len(empty)} with no "
          f"notes. Of {len(segments)} segments: {len(segments) - len(metadata) - unalignable} without "
          f"text, {unalignable} with no alignable phone, {len(failed)} failed in stars.py "
          f"({len(runs)} runs). Stages {', '.join(f'{k} {v:.0f}s' for k, v in timings.items())}")
    return 1 if failed_rows else 0


if __name__ == "__main__":
    sys.exit(main())
