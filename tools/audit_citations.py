#!/usr/bin/env python3
"""
Milestone 2 audit: every filename an answer cited — was it actually retrieved?

Criterion 2 only asks that an answer name a source document. This asks the
harder question sitting behind it, because a model that invents a plausible
filename passes criterion 2 while being worse than useless: is every file named
in an answer one that retrieval really returned for that question?

It reads a run log written by `run_eval.py::write_report` and compares the
filenames inside each answer against that entry's "Sources retrieved" line.

It also asks the tightened version of criterion 2 that Milestone 3 proposes: is
at least one cited file a document that actually contains the answer? A citation
can be real, retrieved, and still the wrong file of the five in the prompt.

    python tools/audit_citations.py results/run_2026-09-30_0158_before.md

No model calls and no retrieval — it reads the run log you already have.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import questions as qs  # noqa: E402

DEFAULT_LOG = "results/run_2026-09-30_0158_before.md"


def _documents_holding_answers() -> dict[str, set[str]]:
    """For each test question, the files whose text contains its `expects`."""
    folder = config.corpus_path()
    corpus = {
        path.name: path.read_text(encoding="utf-8").lower()
        for path in folder.iterdir()
        if path.suffix.lower() in {".txt", ".md"}
    }
    holding = {}
    for item in qs.answered():
        expects = item["expects"].lower()
        holding[item["question"]] = {
            name for name, text in corpus.items() if expects in text
        }
    return holding


def audit(path: str) -> dict:
    """Compare cited filenames against retrieved ones, per answer."""
    text = Path(path).read_text(encoding="utf-8")
    section = text.split("## Real output", 1)[1]
    blocks = re.split(r"\n### ", section)[1:]

    holding = _documents_holding_answers()

    checked = 0
    no_source = []
    invented = []
    wrong_file = []

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

        # The tightened criterion: did it cite a file that holds the answer?
        question = heading.rsplit(" — run", 1)[0]
        answer_files = holding.get(question)
        if answer_files and cited and not (cited & answer_files):
            wrong_file.append((heading, sorted(cited), sorted(answer_files)))

    return {
        "path": path,
        "checked": checked,
        "no_source": no_source,
        "invented": invented,
        "wrong_file": wrong_file,
    }


def main():
    report = audit(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG)
    print(f"Auditing {report['path']}\n")

    for heading in report["no_source"]:
        print(f"NAMED NO SOURCE: {heading}")
    for heading, ghosts in report["invented"]:
        print(f"CITED BUT NOT RETRIEVED: {', '.join(ghosts)}  in: {heading}")

    for heading, cited, answer_files in report["wrong_file"]:
        print(f"CITED THE WRONG FILE: named {', '.join(cited)}, "
              f"answer is in {', '.join(answer_files)}  in: {heading}")

    print(f"{report['checked']} answers checked")
    print(f"answers naming no source (criterion 2 as written): "
          f"{len(report['no_source'])}")
    print(f"answers citing a file retrieval did not return: "
          f"{len(report['invented'])}")
    print(f"answers whose cited files exclude the document holding the answer "
          f"(criterion 2 tightened): {len(report['wrong_file'])}")

    if report["no_source"] or report["invented"] or report["wrong_file"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
