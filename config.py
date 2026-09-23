"""
Settings for The Unofficial Guide.

Everything you're likely to change lives here, at the top, on purpose.
You'll edit THRESHOLD in Milestone 4 and the chunking numbers in Milestone 3.

Anything you set in your .env file wins over the defaults here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


# ─── The corpus you're working with ──────────────────────────────────────────
# Change this to switch corpora, or pass --corpus on the command line.
# Options are the folder names inside corpora/. See corpora/README.md.

CORPUS = os.getenv("AI201_CORPUS", "campus_life")


# ─── Chunking (Milestone 3) ──────────────────────────────────────────────────
# These two belong to `fallback_split` — the starter's fixed-window chunker.
# They are left at the original values on purpose: fallback_split is what I
# compare my own chunker against, so it has to keep behaving the way it did.
# On campus_life an 800-character window splits nothing (longest document: 549).

CHUNK_SIZE = 800        # characters per chunk       (fallback_split only)
CHUNK_OVERLAP = 120     # characters shared between neighbouring chunks (ditto)

# These are mine, used by `split_documents`. The unit is body characters —
# the title line every chunk carries is not counted, since it is repeated
# rather than being content the chunk is spending its budget on.
#
# Why 250: the median body paragraph in campus_life is 112 characters and the
# longest is 373, so 250 packs the common case of two short paragraphs into one
# chunk while still cutting a document that holds two genuinely separate
# thoughts (Kestrel Commons: crowd advice, then hours and prices).
#
# Why a 90 floor: I set this at 120 first and it was wrong — it swallowed the
# split it was supposed to protect. Kestrel Commons is a 249-character
# paragraph about queues followed by a 101-character one about hours and
# prices; the floor pushed the second back onto the first and the document came
# out whole, which is the thing I changed the chunker to stop doing. Reading
# the paragraphs by length, the line sits lower than I guessed: the ten blocks
# under 60 characters are one-liners ("Expect 4 hours a week outside class.")
# that carry no retrievable signal alone, while by 90 characters a paragraph is
# reliably two complete sentences. Below the floor a paragraph merges with its
# neighbour rather than being emitted alone.
#
# Why no overlap at all: the fixed-window chunker needs overlap because it cuts
# mid-sentence and the overlap heals the cut. Mine cuts only at paragraph
# breaks, so there is no cut to heal — and character overlap would drag a
# half-sentence from the next paragraph into every chunk. What neighbouring
# chunks share instead is the title line, which is the context that actually
# goes missing when you split one of these documents.

CHUNK_MAX_BODY = 250    # start a new chunk once the body passes this
CHUNK_MIN_BODY = 90     # never emit a chunk with less body than this
CHUNK_HARD_MAX = 600    # only above this is a single paragraph split internally


# ─── Retrieval (Milestone 4) ─────────────────────────────────────────────────

TOP_K = 5               # how many chunks to pull back per question

# The relevance gate. If the best chunk is further away than this, the system
# refuses to answer instead of handing the model thin material.
#
# LOWER IS BETTER: 0.3 is a close match, 0.9 is unrelated.
#
# 0.6 is a reasonable starting point, not a right answer. Milestone 4 has you
# measure your own two groups of distances and put the cutoff in the gap.
# Most corpora land somewhere between 0.45 and 0.75.
THRESHOLD = 0.6


# ─── Models ──────────────────────────────────────────────────────────────────
# Embeddings run on your own machine and cost no API quota.
# Only generation calls out to a service.

# This is the model Chroma bundles, and leaving it alone is the fast path: it
# downloads about 80 MB from Chroma's own CDN and needs nothing else installed.
#
# Setting it to any other name — unit 2's "try a second embedding model"
# stretch option — switches to loading that model from Hugging Face instead,
# which needs `pip install 'sentence-transformers>=3.4,<3.5'` first. store.py
# says so with a real error message rather than a stack trace if you forget.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MODEL = os.getenv("AI201_MODEL", "gemini-3.5-flash-lite")


# ─── Rate limiting and quota guards ──────────────────────────────────────────
# You should not need to touch these. They exist so that a runaway loop costs
# you a warning instead of your whole day's allowance.

REQUESTS_PER_MINUTE = 30       # outgoing calls the limiter will allow per minute
SESSION_REQUEST_BUDGET = 300   # stop and warn rather than draining the daily quota
MAX_RETRIES = 4                # on 429 / resource-exhausted, with backoff

CACHE_ENABLED = os.getenv("AI201_CACHE", "1") != "0"
CACHE_DIR = ROOT / ".cache"


# ─── Paths ───────────────────────────────────────────────────────────────────

CORPORA_DIR = ROOT / "corpora"
CHROMA_DIR = ROOT / "chroma_db"
RESULTS_DIR = ROOT / "results"


def corpus_path(name: str | None = None) -> Path:
    """Folder holding the documents for a corpus."""
    return CORPORA_DIR / (name or CORPUS) / "documents"


def collection_name(name: str | None = None, variant: str = "default") -> str:
    """
    Name of the vector-store collection for a corpus.

    `variant` lets you index the same corpus two different ways and query both
    without deleting anything — you'll want that in unit 2 when you compare
    chunking strategies.

    Chroma is fussy about collection names: 3 to 63 characters, starting and
    ending with a letter or digit, and nothing but letters, digits, underscores
    and hyphens in between. If you bring your own corpus and name the folder
    something Chroma won't accept, this cleans it up rather than failing.
    """
    import re

    raw = f"{name or CORPUS}__{variant}"
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "-", raw)
    cleaned = cleaned.strip("_-")          # must start and end alphanumeric
    if not cleaned or not cleaned[0].isalnum():
        cleaned = f"c{cleaned}"
    if not cleaned[-1].isalnum():
        cleaned = f"{cleaned}0"
    return cleaned[:63].rstrip("_-") or "collection"
