"""
The relevance gate.

This runs *before* the model does. It looks at how close the best retrieved
chunk actually is, and if nothing came back close enough it refuses the
question outright.

Why this exists as its own step, rather than just asking the model nicely to
admit when it doesn't know: if you only ask nicely, it will sometimes ignore
you and write something confident and wrong. Those answers are much harder to
catch than obvious errors. Deciding in your own code when there's nothing worth
answering from is more reliable than hoping.

You keep the polite instruction too — it's in generate.py — but as a second
layer. The gate catches the clear misses; the prompt catches the near ones.
"""

import re
from dataclasses import dataclass, field

import config
from store import Result

REFUSAL = "I don't have enough information about that."


@dataclass
class GateDecision:
    passed: bool
    best_distance: float
    threshold: float
    missing_entities: tuple[str, ...] = field(default_factory=tuple)

    @property
    def explanation(self) -> str:
        if self.missing_entities:
            named = ", ".join(repr(e) for e in self.missing_entities)
            return (
                f"best distance {self.best_distance:.3f} is under the "
                f"{self.threshold} cutoff, but nothing retrieved mentions "
                f"{named} — refusing"
            )
        if self.passed:
            return (
                f"best distance {self.best_distance:.3f} "
                f"is under the {self.threshold} cutoff"
            )
        return (
            f"best distance {self.best_distance:.3f} "
            f"is over the {self.threshold} cutoff — refusing"
        )


def relevant(results: list[Result], threshold: float | None = None) -> list[Result]:
    """
    Trim the retrieved chunks down to the ones actually close to the question.

    `check` above decides whether to answer at all, using the best chunk. This
    decides which of the rest are worth putting in front of the model, using
    the same cutoff, so there is still only one number to keep in step.

    It exists because top_k is a fixed number and relevance isn't. The housing
    lottery question retrieves one chunk at 0.20 and four between 0.71 and
    0.79 — the four are the closest thing the corpus has to a question it
    can't otherwise match, and putting them in the prompt invites the model to
    answer out of parking permits. A broad question keeps all five.

    Never returns empty: if `check` passed, the chunk it passed on is kept.
    """
    threshold = config.THRESHOLD if threshold is None else threshold
    kept = [r for r in results if r.distance < threshold]
    if not kept and results:
        kept = [min(results, key=lambda r: r.distance)]
    return kept


_WORD = re.compile(r"\b[A-Za-z][A-Za-z']+\b")


def unnamed_entities(
    question: str | None,
    results: list[Result],
    threshold: float | None = None,
) -> tuple[str, ...]:
    """
    Names the question uses that nothing retrieved actually mentions.

    This is the second thing the gate looks at, and it exists because a distance
    cannot express "on topic but not covered". A question about a hall that does
    not exist is topically identical to one about a hall that does — campus,
    housing, dorm rooms, one proper noun — so "What are the dorm rooms like in
    Ashford Hall?" comes back at 0.405, closer than "can I still drop a class
    after seeing my midterm grade" at 0.525, which the corpus answers. No value
    of THRESHOLD separates those two; see the note above THRESHOLD in config.py.

    A capitalised name is the one part of such a question that can be checked
    directly: if I ask about Ashford Hall and every chunk retrieved is about
    Aldridge, Calder and Innisfree, the grounding cannot answer me no matter how
    close it scores. That is also the substitution risk this corpus is built to
    produce — seven laundry documents identical apart from their title line.

    Deliberately narrow:

    - It only looks at capitalised words, because a lowercase noun the corpus
      never uses is indistinguishable from a lowercase noun that just isn't in
      the answering document. Measured, not assumed: "lunch", "close", "eating"
      and "seeing" are all absent from this corpus, and all four come from
      questions it answers, so refusing on those would refuse real questions.
      That is why the gym and tuition questions still get through.
    - It skips the first word, so "What", "How" and "Who" aren't treated as
      names. A question opening on a proper noun loses that name too, which
      costs a check rather than causing a wrong one.
    - It asks only about the chunks the gate would actually hand over, so a name
      present in the corpus but missed by retrieval is caught as well.

    Returns the missing names in the order asked. Empty tuple means nothing to
    object to, including when no question was passed.
    """
    if not question or not config.GATE_REQUIRE_NAMED_ENTITIES:
        return ()

    kept = relevant(results, threshold=threshold)
    grounding = " ".join(r.text for r in kept).lower()

    names = [w for w in _WORD.findall(question)[1:] if w[0].isupper()]
    missing = [w for w in names if w.lower() not in grounding]
    return tuple(dict.fromkeys(missing))


def check(
    results: list[Result],
    threshold: float | None = None,
    question: str | None = None,
) -> GateDecision:
    """
    Decide whether the retrieved chunks are close enough to answer from.

    Remember: LOWER distance is better. A question passes when its best chunk
    is *under* the threshold **and** the chunks retrieved mention the names the
    question used — see `unnamed_entities`.

    `question` is optional so that a caller with nothing but distances still
    works, but every caller in this project passes it. A gate that decided one
    way in the app and another way in the eval would make the run log evidence
    about a system nobody uses.
    """
    threshold = config.THRESHOLD if threshold is None else threshold

    if not results:
        return GateDecision(passed=False, best_distance=1.0, threshold=threshold)

    best = min(r.distance for r in results)
    if best >= threshold:
        return GateDecision(passed=False, best_distance=best, threshold=threshold)

    missing = unnamed_entities(question, results, threshold)
    return GateDecision(
        passed=not missing,
        best_distance=best,
        threshold=threshold,
        missing_entities=missing,
    )
