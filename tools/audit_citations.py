#!/usr/bin/env python3
"""
Milestone 2 audit: every filename an answer cited — was it actually retrieved?

Criterion 2 only asks that an answer name a source document. This asks the
harder question sitting behind it, because a model that invents a plausible
filename passes criterion 2 while being worse than useless: is every file named
in an answer one that retrieval really returned for that question?

It reads a run log written by `run_eval.py::write_report` and compares the
filenames inside each answer against that entry's "Sources retrieved" line.

    python tools/audit_citations.py results/run_2026-09-30_0158_before.md

No model calls and no retrieval — it reads the run log you already have.
"""

import re
import sys
from pathlib import Path

DEFAULT_LOG = "results/run_2026-09-30_0158_before.md"


def audit(path: str) -> dict:
    """Compare cited filenames against retrieved ones, per answer."""
    text = Path(path).read_text(encoding="utf-8")
    section = text.split("## Real output", 1)[1]
    blocks = re.split(r"\n### ", section)[1:]

    checked = 0
    no_source = []
    invented = []

    for block in blocks:
        heading = block.split("\n", 1)[0]
        found = re.search(r"- Sources retrieved: (.*)", block)
        if not found:
            continue
        retrieved = set(re.findall(r"[\w./-]+\.txt", found.group(1)))
        answer = block.split("```", 2)[1]
        cited = set(re.findall(r"[\w./-]+\.txt", answer))

        checked += 1
        if not cited:
            no_source.append(heading)
        ghosts = cited - retrieved
        if ghosts:
            invented.append((heading, sorted(ghosts)))

    return {
        "path": path,
        "checked": checked,
        "no_source": no_source,
        "invented": invented,
    }


def main():
    report = audit(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG)
    print(f"Auditing {report['path']}\n")

    for heading in report["no_source"]:
        print(f"NAMED NO SOURCE: {heading}")
    for heading, ghosts in report["invented"]:
        print(f"CITED BUT NOT RETRIEVED: {', '.join(ghosts)}  in: {heading}")

    print(f"{report['checked']} answers checked")
    print(f"answers naming no source: {len(report['no_source'])}")
    print(f"answers citing a file retrieval did not return: {len(report['invented'])}")

    if report["no_source"] or report["invented"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
