#!/usr/bin/env python3
"""
Criterion 4: every indexed chunk carries its document's title line.

    python check_titles.py

`run_eval.py` measures the criteria that depend on asking a question. This one
doesn't: it's a property of what went into the index, so it's checked by
reading the collection back out and comparing every stored chunk against the
first line of the file it came from.

It reads the indexed chunks rather than re-chunking the documents on the spot.
Re-running `split_documents` here would test the chunker; the criterion is
about what the system is actually searching, which is whatever is in Chroma.

No model calls, and no embedding either — `collection.get` returns the stored
text directly.
"""

import argparse
import sys

import config
import store
from ingest import load_documents


def check(corpus: str | None = None, variant: str = "default") -> dict:
    """
    Compare every chunk in the index against its document's first line.

    Returns the count, the number carrying their title, and the chunks that
    don't — by chunk label, so a failure is something you can go and look at.
    """
    titles = {
        doc.source: doc.text.split("\n", 1)[0].strip()
        for doc in load_documents(corpus)
    }

    name = config.collection_name(corpus, variant)
    try:
        collection = store._client().get_collection(name)
    except Exception as exc:
        raise RuntimeError(
            f"No index called '{name}'. Run `python app.py index` first."
        ) from exc

    stored = collection.get(include=["documents", "metadatas"])

    missing = []
    unknown = []
    for text, meta in zip(stored["documents"], stored["metadatas"]):
        source = str(meta.get("source", "unknown"))
        label = f"{source}#{meta.get('index', 0)}"
        title = titles.get(source)
        if title is None:
            unknown.append(label)
        elif title not in text:
            missing.append(label)

    total = len(stored["documents"])
    return {
        "collection": name,
        "total": total,
        "carrying": total - len(missing) - len(unknown),
        "missing": missing,
        "unknown": unknown,
        "documents": len(titles),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default=None)
    parser.add_argument("--variant", default="default")
    args = parser.parse_args()

    report = check(args.corpus, args.variant)

    print(f"Collection: {report['collection']}")
    print(f"Documents on disk: {report['documents']}")
    print(f"Chunks indexed: {report['total']}")
    print(
        f"Chunks containing their document's title line: "
        f"{report['carrying']} of {report['total']}"
    )

    if report["unknown"]:
        print(f"\nChunks whose source file is no longer on disk ({len(report['unknown'])}):")
        for label in report["unknown"]:
            print(f"  {label}")

    if report["missing"]:
        print(f"\nChunks missing their title line ({len(report['missing'])}):")
        for label in report["missing"]:
            print(f"  {label}")
        sys.exit(1)

    print("\nAll indexed chunks carry their title line.")


if __name__ == "__main__":
    main()
