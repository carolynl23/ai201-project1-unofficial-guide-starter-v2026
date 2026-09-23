"""
Your test questions.

Milestone 2 asks you to write five questions your system should be able to
answer from your corpus, specific enough to have a right answer.

  ✗ "What are good dining halls?"          — no right answer
  ✓ "What do students say about wait times at Commons during lunch?"

Fill in `QUESTIONS` below. `expects` is a word or short phrase you'd expect a
correct answer to contain — you'll use it in unit 2 when you build a scorer,
and having written it now means you decided what "correct" meant before you saw
any results.

`OUT_OF_SCOPE` holds five questions your documents clearly don't cover. You
need these in Milestone 4 to find where your relevance cutoff belongs, and
again in unit 2, where `run_eval.py` runs them through the gate and writes what
happened into your run log — that's the evidence for criterion 3.

Swap them for your own if you like. Keep five of them either way: criterion 3
names a target of "4 of 5", and four of three is not a thing.
"""

QUESTIONS = [
    # Two documents cover this one (dining_kestrel_commons.txt and its
    # followup), and both give the same figure — this is the easy one.
    {
        "question": "How long is the wait at Kestrel Commons between 12:15 and 1:00?",
        "expects": "20 to 25 minutes",
    },
    # admin_pass_fail_option.txt only. The deadline is the part the document
    # says "nobody mentions", so nothing else in the corpus repeats it.
    {
        "question": "How late in the semester can I declare a course pass/fail?",
        "expects": "week eight",
    },
    # housing_aldridge_hall_laundry.txt. Seven buildings have near-identical
    # laundry documents — every one of them says "eight washers and six
    # dryers", and only the payment line differs. "card only" is Aldridge's
    # alone, so this expects fails if retrieval brings back the wrong hall.
    {
        "question": "What do the laundry machines in Aldridge Hall cost, and how do you pay for them?",
        "expects": "card only",
    },
    # study_library_hours.txt. The reading-week hours are shorter than term
    # hours, which is the counterintuitive part.
    {
        "question": "What time does the library close during reading week?",
        "expects": "10pm",
    },
    # admin_housing_lottery.txt only, and the word "lottery" pulls against
    # eight other housing documents. This is the one I expect to be hard.
    {
        "question": "How is lottery order decided for juniors and seniors in the housing lottery?",
        "expects": "credit hours",
    },
]

# Questions from a different world entirely. Your gate should refuse all five.
#
# There are five of these because criterion 3 in criteria.md names a target of
# "at least 4 of 5" — you need five things to try before you can report 4 of 5.
# `run_eval.py` runs these through retrieval and the gate on every eval and
# records what happened, so criterion 3 has evidence in the run log alongside
# the others. They cost no model calls: a refusal never reaches the model.
OUT_OF_SCOPE = [
    "What is the capital of Mongolia?",
    "How do I change the oil in a diesel engine?",
    "Who won the 1994 World Cup?",
    "What is the recommended dosage of ibuprofen for a headache?",
    "How do I write a for loop in Rust?",
]


def answered() -> list[dict]:
    """The questions you've actually filled in."""
    return [q for q in QUESTIONS if q.get("question", "").strip()]
