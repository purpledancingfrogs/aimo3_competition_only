# cross-model-convergence-benchmark/analysis/convergence_metric.py

import argparse
import json
from pathlib import Path
from itertools import combinations


def tokenize(text: str):
    return [t for t in text.lower().split() if t.strip()]


def jaccard(a, b):
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if sa | sb else 0.0


def load_texts(root: Path):
    texts = []
    for p in root.rglob("*.txt"):
        texts.append(p.read_text(encoding="utf-8"))
    return texts


def main(inputs: str, out: str):
    texts = load_texts(Path(inputs))
    pairs = list(combinations(texts, 2))

    scores = [jaccard(tokenize(a), tokenize(b)) for a, b in pairs]

    result = {
        "pairs": len(scores),
        "jaccard_mean": sum(scores) / len(scores) if scores else 0.0,
    }

    Path(out).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    main(args.inputs, args.out)
