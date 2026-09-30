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
from chunker import split_documents
from ingest import load_documents


def check(corpus: str | None = None, variant: str = "default") -> dict:
    """
    Compare every chunk in the index against its document's first line.

    Returns the count, the number carrying their title, and the chunks that
    don't — by chunk label, so a failure is something you can go and look at.
    """
    docs = load_documents(corpus)
    titles = {doc.source: doc.text.split("\n", 1)[0].strip() for doc in docs}

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
    title_only = []
    for text, meta in zip(stored["documents"], stored["metadatas"]):
        source = str(meta.get("source", "unknown"))
        label = f"{source}#{meta.get('index', 0)}"
        title = titles.get(source)
        if title is None:
            unknown.append(label)
        elif title not in text:
            missing.append(label)
        elif text.strip() == title:
            # Carrying the title is trivially true of a chunk that is nothing
            # but the title. Counted separately so the headline number can't be
            # inflated by chunks with no body in them.
            title_only.append(label)

    # A pass here means nothing if the index is older than the chunker. Compare
    # what's stored against what split_documents produces from the documents on
    # disk right now, so a stale index is reported rather than quietly counted.
    fresh = {f"{c.source}#{c.index}": c.text for c in split_documents(docs)}
    stale = sorted(set(stored["ids"]) ^ set(fresh)) + [
        i for i, text in zip(stored["ids"], stored["documents"])
        if i in fresh and fresh[i] != text
    ]

    total = len(stored["documents"])
    return {
        "collection": name,
        "total": total,
        "carrying": total - len(missing) - len(unknown),
        "missing": missing,
        "unknown": unknown,
        "documents": len(titles),
        "title_only": title_only,
        "stale": sorted(set(stale)),
        "fresh_total": len(fresh),
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

    print(
        f"Chunks that are nothing but a title line (trivial passes): "
        f"{len(report['title_only'])}"
    )

    if report["stale"]:
        print(
            f"\n⚠️  The index is out of step with chunker.py: "
            f"{len(report['stale'])} chunk(s) differ from what split_documents "
            f"produces now ({report['fresh_total']} chunks). Re-run "
            f"`python app.py index` — the count above is about an old index."
        )
        for label in report["stale"][:10]:
            print(f"  {label}")
    else:
        print(
            f"Index is current with chunker.py::split_documents "
            f"({report['fresh_total']} chunks, same ids and same text)."
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
