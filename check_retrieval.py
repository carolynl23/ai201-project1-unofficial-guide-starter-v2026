#!/usr/bin/env python3
"""
Criterion 1: does retrieval put the answer in front of the model?

    python check_retrieval.py

`run_eval.py` records which *documents* came back for each question. That isn't
quite criterion 1. The chunker splits some documents into more than one chunk —
88 documents become 134 chunks — so a run log saying `study_library_hours.txt`
was retrieved doesn't say whether the chunk retrieved was the one with the
closing time in it. This checks the chunk text itself.

It checks the chunks the gate actually keeps (`gate.relevant`), not all top-k,
because those are the ones the model is given. A chunk retrieved and then
trimmed away didn't help answer anything.

The test is whether the `expects` phrase from questions.py appears in a kept
chunk. That phrase was chosen before any results existed, which is the point of
having written it down then.

No model calls — retrieval and a substring test.
"""

import argparse
import sys

import config
import gate
import questions as qs
from store import search


def check(corpus: str | None = None, variant: str = "default",
          top_k: int | None = None, threshold: float | None = None) -> list[dict]:
    """
    For each test question: which chunks were kept, and do any contain `expects`?

    One row per question. `found` is criterion 1 for that question.
    """
    top_k = top_k or config.TOP_K
    threshold = config.THRESHOLD if threshold is None else threshold

    rows = []
    for item in qs.answered():
        question, expects = item["question"], item["expects"]
        results = search(question, top_k=top_k, corpus=corpus, variant=variant)
        decision = gate.check(results, threshold=threshold)
        kept = gate.relevant(results, threshold=threshold)

        holding = [r for r in kept if expects.lower() in r.text.lower()]
        rows.append(
            {
                "question": question,
                "expects": expects,
                "kept": [(r.label, r.distance) for r in kept],
                "holding": [(r.label, r.distance) for r in holding],
                "found": bool(holding),
                "refused": not decision.passed,
                "best_distance": decision.best_distance,
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=None)
    parser.add_argument("--variant", default="default")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    rows = check(args.corpus, args.variant, args.top_k, args.threshold)
    if not rows:
        print("No questions in questions.py.", file=sys.stderr)
        sys.exit(1)

    for row in rows:
        print(f"\n{row['question']}")
        print(f"  expects: {row['expects']!r}")
        print(f"  best distance: {row['best_distance']:.4f} "
              f"({'REFUSED by gate' if row['refused'] else 'passed the gate'})")
        print(f"  chunks given to the model: "
              f"{', '.join(f'{label} at {d:.3f}' for label, d in row['kept'])}")
        if row["found"]:
            print(f"  ANSWER PRESENT in: "
                  f"{', '.join(f'{label} at {d:.3f}' for label, d in row['holding'])}")
        else:
            print("  ANSWER NOT PRESENT in any chunk the model was given")

    found = sum(r["found"] for r in rows)
    refused = sum(r["refused"] for r in rows)
    print(f"\nCriterion 1 — answer present in a retrieved chunk: {found} of {len(rows)}")
    print(f"Criterion 5 — answerable questions refused by the gate: {refused} of {len(rows)}")


if __name__ == "__main__":
    main()
