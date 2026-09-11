"""Note-level benchmarking for transcription systems.

Gives a defensible answer to "how good is this", with confidence intervals and
enough provenance that a number can be reproduced later. Nothing here knows how
any particular transcriber works: a system is scored either from a directory of
notes it already wrote, or through a small adapter.

    from transcription_benchmarking import pair_dataset, run_benchmark, format_result

    pairing = pair_dataset("vocadito/audio", "vocadito/annotations")
    result = run_benchmark(pairing, estimates=pair_estimates(pairing.items, "midi"))
    print(format_result(result))
"""

from .annotations import Annotation, load_annotation
from .dataset import Item, Pairing, dataset_digest, pair_dataset, pair_estimates
from .metrics import Aggregate, ItemScore, PRF, aggregate_scores, score_item
from .runner import BenchmarkResult, Provenance, format_result, run_benchmark
from .transcribers import Note, Transcriber, available, load

__all__ = [
    "Annotation", "load_annotation",
    "Item", "Pairing", "pair_dataset", "pair_estimates", "dataset_digest",
    "PRF", "ItemScore", "Aggregate", "score_item", "aggregate_scores",
    "BenchmarkResult", "Provenance", "run_benchmark", "format_result",
    "Note", "Transcriber", "available", "load",
]
