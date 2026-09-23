"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _split_long_paragraph(block: str, limit: int) -> list[str]:
    """
    Break one oversized paragraph on sentence boundaries, never mid-sentence.

    This does not fire on campus_life — the longest body paragraph in the
    corpus is 373 characters and the ceiling is 600. It exists so that one
    unusually long document can't put a 2,000-character wall into the index.
    """
    sentences = re.split(r"(?<=[.!?])\s+", block)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > limit:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split on paragraph breaks, pack small paragraphs together, and give every
    chunk the document's title line.

    Written for campus_life: 88 short posts, 178 to 549 characters, each one a
    title line followed by one to four paragraphs. Three things follow from
    reading them.

    A paragraph is the unit of thought here, so a paragraph break is where a
    cut belongs. The starter cut at 800 characters, which on these documents
    meant it never cut at all — every post went into the index whole, including
    the ones holding two unrelated thoughts. Kestrel Commons has one paragraph
    about queues and stir-fry and another about opening hours and the price of
    a swipe; as one chunk it matches a question about hours weakly and a
    question about queues weakly.

    But most paragraphs are too small to stand alone — 99 of 183 are under 120
    characters — so paragraph splitting on its own trades one problem for a
    worse one. Hence packing: paragraphs accumulate until the body passes
    CHUNK_MAX_BODY, and a leftover under CHUNK_MIN_BODY goes back onto the
    chunk before it rather than becoming a fragment.

    And the title line goes on every chunk, which matters more in this corpus
    than any of the size numbers. Seven laundry documents are word-for-word
    identical apart from their first line and one price line: "There are eight
    washers and six dryers for the building" appears in all seven, verbatim.
    Take the second paragraph of one of them on its own and nothing in the text
    says which building it is — not for a reader, not for an embedding. The
    title is what makes the chunk answerable, so it is repeated into each one.
    """
    chunks: list[Chunk] = []

    for doc in documents:
        blocks = [b.strip() for b in doc.text.split("\n\n") if b.strip()]
        if not blocks:
            continue

        title, body_blocks = blocks[0], blocks[1:]
        if not body_blocks:
            # A title and nothing under it. Keep it; don't invent content.
            body_blocks = [title]

        # Only genuinely oversized paragraphs get opened up.
        expanded: list[str] = []
        for block in body_blocks:
            if len(block) > config.CHUNK_HARD_MAX:
                expanded.extend(_split_long_paragraph(block, config.CHUNK_MAX_BODY))
            else:
                expanded.append(block)

        # Pack paragraphs into groups, respecting the floor over the ceiling:
        # going over CHUNK_MAX_BODY is better than emitting a fragment.
        def body_length(group: list[str]) -> int:
            """What the group will actually measure once joined."""
            return len("\n\n".join(group))

        groups: list[list[str]] = []
        current: list[str] = []
        for block in expanded:
            fits = body_length(current + [block]) <= config.CHUNK_MAX_BODY
            if current and not fits and body_length(current) >= config.CHUNK_MIN_BODY:
                groups.append(current)
                current = []
            current.append(block)
        if current:
            if groups and body_length(current) < config.CHUNK_MIN_BODY:
                groups[-1].extend(current)     # no orphan tails
            else:
                groups.append(current)

        for index, group in enumerate(groups):
            body = "\n\n".join(group)
            text = body if body == title else f"{title}\n\n{body}"
            chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
