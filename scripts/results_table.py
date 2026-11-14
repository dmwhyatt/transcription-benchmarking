"""The results tables, recomputed from each system's per-recording scores and the timing records.

    python scripts/results_table.py           # the full table (RESULTS.md), as markdown
    python scripts/results_table.py --common  # the README's table: the datasets no system was trained on
    python scripts/results_table.py --tests   # and the paired tests between neighbours in the full table's ranking

Inputs, beside this file:
- scores.json: COnPOff@50 for every row of the table, per dataset and recording, computed with this package's
  ``transcription_benchmarking.metrics.score_item`` from each system's MIDI.
- timing.jsonl: one record per timed run.

Scores. A dataset's score is the mean over its recordings, with vocadito's two annotators averaged per recording.
*A cappella* averages vocadito, Molina and SSVD test; *pop* averages RWC-P dev and MIR-ST500 test; the five-set mean
averages all five. Tony leaves vocadito out of its mean and its a cappella average: vocadito's references were made by
correcting Tony's output.

Common set. The README's table, and the DMRN+21 abstract's, average the three datasets that no system was trained on:
vocadito, Molina and RWC-P dev. Tony is left out of it, because vocadito's references were made by correcting its
output and a mean over the other two would not be comparable with the rest.

Intervals. A paired bootstrap over recordings, stratified by dataset. Each of 10,000 resamples draws every dataset's
recordings with replacement, the same draw for every row, and the datasets are drawn in the order of DATASETS from one
generator seeded 0. The interval is the 2.5th to 97.5th percentile of the resampled mean.

Tests. The difference between neighbours in the ranking, bootstrapped from the same resamples. The two-sided p-value
is Holm-corrected across all neighbour pairs. A pair involving Tony is compared over the four datasets other than
vocadito. The tests leave out STARS and transcPybe v2's PESTO and pYIN rows, as the DMRN+21 abstract's figure does.

Timing. Seconds of computation per minute of audio, model loading included, summed over the timing sets. A system
with a GPU path is timed with and without the GPU. A system without one ran its single timed run on the CPU, and that
run is its CPU figure.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
COLUMNS = ["vocadito A1", "vocadito A2", "Molina", "RWC-P dev", "SSVD test", "MIR-ST500 test"]
DATASETS = ["vocadito", "Molina", "RWC-P dev", "SSVD test", "MIR-ST500 test"]
B, SEED = 10_000, 0
NO_VOCADITO = {"Tony"}
# transcPybe v2's other pitch trackers: ranked with every row in the table, left out of the neighbour tests
TRACKER_ROWS = ["transcPybe v2, PESTO", "transcPybe v2, pYIN"]
COMMON = ["vocadito", "Molina", "RWC-P dev"]                       # the datasets no system was trained on
LAST = ["STARS"]                                                   # listed last whatever its score
MARK = {"Phoneme-informed": "\\*", "MIR-ST500 model": "\\*", "YourMT3+": "\\*", "CTC-CE": "\\*", "Tony": " †",
        "STARS": " ‡"}
# The timing records behind each row: (system, pitch tracker, device the run was labelled with). A row's figure is
# 60 x the summed wall time / the summed audio time over its records.
GPU_PATH = {"Phoneme-informed": "phoneme-informed", "MIR-ST500 model": "mirst500", "CTC-CE": "ctc-ce",
            "YourMT3+": "yourmt3", "SOME": "some", "ROSVOT": "rosvot"}
CPU_ONLY = {"Tony": "tony", "GAME": "game", "Omnizart": "omnizart", "Kum et al.": "keums", "Basic Pitch": "basic-pitch",
            "Essentia": "essentia", "CREPE Notes": "crepe-notes", "aubio": "aubio"}


def timing_keys(row: str) -> dict:
    if row in GPU_PATH:
        return {"gpu": [(GPU_PATH[row], None, "gpu")], "cpu": [(GPU_PATH[row], None, "cpu")]}
    if row in CPU_ONLY:
        return {"gpu": [], "cpu": [(CPU_ONLY[row], None, "gpu")]}
    if row == "transcPybe v1":
        return {mode: [("ours-rules", "crepe-full", mode)] for mode in ("gpu", "cpu")}
    if row.startswith("transcPybe v2, "):
        fe = {"CREPE": "crepe-full", "PESTO": "pesto", "pYIN": "pyin"}[row.split(", ")[1]]
        return {mode: [("ours-acap", fe, mode), ("ours-pop", fe, mode)] for mode in ("gpu", "cpu")}
    return {"gpu": [], "cpu": []}


def seconds_per_minute(records: list) -> dict:
    acc = collections.defaultdict(lambda: [0.0, 0.0])
    for r in records:
        if r["part"] == "set" and r["status"] == "ok":
            k = (r["system"], r["front_end"], r["mode"])
            acc[k][0] += r["wall_s"]
            acc[k][1] += r["audio_s"]

    def figure(keys):
        if not keys or any(k not in acc for k in keys):
            return None
        return 60 * sum(acc[k][0] for k in keys) / sum(acc[k][1] for k in keys)

    return figure


def load():
    scores = json.load(open(HERE / "scores.json"))["datasets"]
    records = [json.loads(line) for line in open(HERE / "timing.jsonl") if line.strip()]
    return scores, records


def bootstrap(scores: dict):
    """Each row's per-dataset point means and resampled means (B x rows), with vocadito's annotators averaged."""
    rows = sorted(scores["Molina"])
    sets = {name: scores[name] for name in DATASETS if name != "vocadito"}
    a1, a2 = scores["vocadito A1"], scores["vocadito A2"]
    sets["vocadito"] = {r: {i: (a1[r][i] + a2[r][i]) / 2 for i in a1[r]} for r in rows}
    rng = np.random.default_rng(SEED)
    point, boot = {}, {}
    for name in DATASETS:
        items = sorted(sets[name][rows[0]])
        m = np.array([[sets[name][r][i] for r in rows] for i in items])           # recordings x rows
        point[name] = m.mean(axis=0)
        idx = rng.integers(0, len(items), size=(B, len(items)))
        boot[name] = m[idx].mean(axis=1)                                         # resamples x rows
    return rows, point, boot


def summaries(scores: dict) -> dict:
    rows, point, boot = bootstrap(scores)
    five, four = DATASETS, [n for n in DATASETS if n != "vocadito"]
    pt5, bt5 = sum(point[n] for n in five) / 5, sum(boot[n] for n in five) / 5
    pt4, bt4 = sum(point[n] for n in four) / 4, sum(boot[n] for n in four) / 4
    out = {}
    for k, r in enumerate(rows):
        pt, bt = (pt4, bt4) if r in NO_VOCADITO else (pt5, bt5)
        lo, hi = np.percentile(bt[:, k], [2.5, 97.5])
        cols = {c: sum(scores[c][r].values()) / len(scores[c][r]) for c in COLUMNS}
        voc = (cols["vocadito A1"] + cols["vocadito A2"]) / 2
        acap = ((cols["Molina"] + cols["SSVD test"]) / 2 if r in NO_VOCADITO
                else (voc + cols["Molina"] + cols["SSVD test"]) / 3)
        pop = (cols["RWC-P dev"] + cols["MIR-ST500 test"]) / 2
        out[r] = dict(columns=cols, acap=acap, pop=pop, mean=float(pt[k]), lo=float(lo), hi=float(hi))
    return out


def common_summaries(scores: dict) -> dict:
    """Each row's mean over COMMON, with its interval, from the same resamples as ``summaries``; Tony is left out."""
    rows, point, boot = bootstrap(scores)
    pt, bt = sum(point[n] for n in COMMON) / len(COMMON), sum(boot[n] for n in COMMON) / len(COMMON)
    out = {}
    for k, r in enumerate(rows):
        if r not in NO_VOCADITO:
            lo, hi = np.percentile(bt[:, k], [2.5, 97.5])
            out[r] = dict(mean=float(pt[k]), lo=float(lo), hi=float(hi))
    return out


def common_table(scores: dict, cite=lambda row: "") -> list:
    """The README's table: every row but Tony, by its mean over COMMON, with STARS last."""
    summary = common_summaries(scores)
    lines = ["| System | Mean | 95% CI |", "|---|---|---|"]
    for r in order(summary):
        s = summary[r]
        mark = MARK.get(r, "") if r in LAST else ""
        lines.append(f"| {r}{cite(r)}{mark} | {s['mean']:.3f} | [{s['lo']:.3f}, {s['hi']:.3f}] |")
    return lines


def order(summary: dict) -> list:
    """Every row by its mean, best first (Tony by its mean without vocadito), then LAST."""
    return sorted((r for r in summary if r not in LAST), key=lambda r: -summary[r]["mean"]) + LAST


def table(scores: dict, records: list, cite=lambda row: "") -> list:
    """The table's lines. ``cite`` gives a row's citation, such as " [4]", placed between its name and its mark."""
    summary, figure = summaries(scores), seconds_per_minute(records)
    lines = ["| System | " + " | ".join(COLUMNS) + " | A cappella | Pop | Five-set mean [95% CI] | GPU s/min | CPU s/min |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    fmt = lambda x: "–" if x is None else f"{x:.1f}"
    for r in order(summary):
        s, keys = summary[r], timing_keys(r)
        mean = f"**{s['mean']:.3f}**" + ("†" if r in NO_VOCADITO else "")
        cells = ([f"{s['columns'][c]:.3f}" for c in COLUMNS] + [f"{s['acap']:.3f}", f"{s['pop']:.3f}"]
                 + [f"{mean} [{s['lo']:.3f}, {s['hi']:.3f}]", fmt(figure(keys["gpu"])), fmt(figure(keys["cpu"]))])
        lines.append(f"| {r}{cite(r)}{MARK.get(r, '')} | " + " | ".join(cells) + " |")
    return lines


def neighbour_tests(scores: dict) -> list:
    rows, point, boot = bootstrap(scores)
    keep = [k for k, r in enumerate(rows) if r not in TRACKER_ROWS + LAST]
    five, four = DATASETS, [n for n in DATASETS if n != "vocadito"]
    pt5, bt5 = sum(point[n] for n in five) / 5, sum(boot[n] for n in five) / 5
    pt4, bt4 = sum(point[n] for n in four) / 4, sum(boot[n] for n in four) / 4
    mean = {rows[k]: (pt4 if rows[k] in NO_VOCADITO else pt5)[k] for k in keep}
    ranked = sorted(mean, key=lambda r: -mean[r])
    tests = []
    for x, y in zip(ranked, ranked[1:]):
        i, j = rows.index(x), rows.index(y)
        pt, bt = (pt4, bt4) if NO_VOCADITO & {x, y} else (pt5, bt5)
        d = bt[:, i] - bt[:, j]
        lo, hi = np.percentile(d, [2.5, 97.5])
        p = max(min(1.0, 2 * min(np.mean(d <= 0), np.mean(d >= 0))), 1 / B)
        tests.append(dict(pair=(x, y), diff=float(pt[i] - pt[j]), lo=float(lo), hi=float(hi), p=float(p),
                          datasets=4 if NO_VOCADITO & {x, y} else 5))
    running = 0.0                                                                # Holm, across all neighbour pairs
    for rank, k in enumerate(np.argsort([t["p"] for t in tests])):
        running = max(running, min(1.0, tests[k]["p"] * (len(tests) - rank)))
        tests[k]["holm"] = running
    return tests


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--common", action="store_true", help="print the README's table instead of the full one")
    ap.add_argument("--tests", action="store_true", help="also print the paired tests between neighbours")
    args = ap.parse_args(argv)
    scores, records = load()
    print("\n".join(common_table(scores) if args.common else table(scores, records)))
    if args.tests:
        print("\nNeighbours in the ranking (Holm-corrected across all pairs; * differs at 0.05):")
        for t in neighbour_tests(scores):
            x, y = t["pair"]
            print(f"  {x:22s} minus {y:22s} {t['diff']:+.4f} [{t['lo']:+.4f}, {t['hi']:+.4f}] "
                  f"({t['datasets']} datasets)  Holm p {t['holm']:.4f} {'*' if t['holm'] < 0.05 else 'level'}")


if __name__ == "__main__":
    main()
