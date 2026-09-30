#!/usr/bin/env python3
"""
Where the cutoff actually sits: all three groups of question on one axis.

    python check_boundary.py

Milestone 2 left me with five MET verdicts and a suspicion. Every criterion I
wrote is measured either on the five test questions (0.20–0.25) or the five
OUT_OF_SCOPE questions (0.83–0.92), and the cutoff is at 0.60 with nothing near
it. That makes all five criteria easy for the same reason, so this puts the
near-boundary probes from Milestone 4 back through the current index next to
both groups, sorted by distance, with what the gate does to each.

The probes are the ones in the Milestone 4 section of README.md, labelled there
as covered or not covered. They aren't in questions.py because they aren't test
questions — `covered` ones should be answered, `uncovered` ones should not, and
no criterion of mine currently governs either.

No model calls: retrieval and the gate only.
"""

import argparse

import config
import gate
import questions as qs
from store import search

# From the probe table in README.md, Milestone 4. "covered" means the corpus can
# answer it; "uncovered" means it can't, and the gate ought to refuse.
PROBES = [
    ("which building has somewhere quiet to work late at night", "covered"),
    ("when should I do my laundry to avoid waiting for a dryer", "covered"),
    ("What are the dorm rooms like in Ashford Hall?", "uncovered"),
    ("What time does the campus gym open?", "uncovered"),
    ("is it worth eating lunch early to skip the queue", "covered"),
    ("can I still drop a class after seeing my midterm grade", "covered"),
    ("How much is tuition next year?", "uncovered"),
    ("How do I sign up for intramural sports?", "uncovered"),
]


def measure(corpus=None, variant="default", top_k=None, threshold=None) -> list[dict]:
    """Every question I have, with its best distance and the gate's decision."""
    top_k = top_k or config.TOP_K
    threshold = config.THRESHOLD if threshold is None else threshold

    groups = (
        [(item["question"], "test question", True) for item in qs.answered()]
        + [(q, "probe", label == "covered") for q, label in PROBES]
        + [(q, "out of scope", False) for q in getattr(qs, "OUT_OF_SCOPE", [])]
    )

    rows = []
    for question, group, should_answer in groups:
        results = search(question, top_k=top_k, corpus=corpus, variant=variant)
        decision = gate.check(results, threshold=threshold)
        group = f"{group} ({'covered' if should_answer else 'uncovered'})"
        rows.append(
            {
                "question": question,
                "group": group,
                "best_distance": decision.best_distance,
                "answered": decision.passed,
                "should_answer": should_answer,
                "correct": decision.passed == should_answer,
            }
        )
    return sorted(rows, key=lambda r: r["best_distance"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=None)
    parser.add_argument("--variant", default="default")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    threshold = config.THRESHOLD if args.threshold is None else args.threshold
    rows = measure(args.corpus, args.variant, args.top_k, threshold)

    print(f"cutoff {threshold}, sorted by distance. "
          f"'wrong' = the gate did the opposite of what the question deserves.\n")
    print(f"{'dist':>6}  {'gate':<8} {'':<6} {'group':<26} question")
    crossed = False
    for row in rows:
        if not crossed and row["best_distance"] > threshold:
            print(f"{'':>6}  {'':<8} {'':<6} {'':<26} ── cutoff {threshold} ──")
            crossed = True
        print(f"{row['best_distance']:>6.3f}  "
              f"{'answers' if row['answered'] else 'refuses':<8} "
              f"{'' if row['correct'] else 'wrong':<6} "
              f"{row['group']:<26} {row['question'][:52]}")

    wrong = [r for r in rows if not r["correct"]]
    covered = [r for r in rows if r["should_answer"]]
    uncovered = [r for r in rows if not r["should_answer"]]
    print(f"\ncovered questions, distance range:   "
          f"{min(r['best_distance'] for r in covered):.3f} – "
          f"{max(r['best_distance'] for r in covered):.3f}")
    print(f"uncovered questions, distance range: "
          f"{min(r['best_distance'] for r in uncovered):.3f} – "
          f"{max(r['best_distance'] for r in uncovered):.3f}")
    print(f"the gate is wrong about {len(wrong)} of {len(rows)}, all of them "
          f"uncovered questions it answers:")
    for row in wrong:
        print(f"  {row['best_distance']:.3f}  {row['question']}")


if __name__ == "__main__":
    main()
