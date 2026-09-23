# The Unofficial Guide

**Name:** <!-- ← put your name here -->
**Corpus:** `campus_life` — 88 posts of student advice about one invented campus.

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This is a question-answering system over `campus_life`, a corpus of 88 short
posts — around 28,000 characters in total — in which students write down the
things about one invented campus that nobody tells you at orientation. The
documents are dining hall write-ups, dorm-by-dorm notes on laundry and noise,
course pages for nine classes, and administrative explainers on the things
students work out from each other: the pass/fail deadline, how the housing
lottery is really ordered, what the printing quota actually buys.

Ask it a specific question about that campus — *how late can I declare a course
pass/fail*, *what do the laundry machines in Aldridge Hall cost*, *what time
does the library close during reading week* — and it retrieves the passages
most likely to hold the answer, answers from those passages only, and names the
file it used. It is not a chatbot with opinions about the campus. Every claim it
makes should be traceable to a document, and where it can't be, the system is
built to say so.

That last part is the half that took the work. Two layers decide when not to
answer. A relevance gate compares the closest retrieved chunk against a measured
cutoff and refuses outright when nothing is close enough, before any model call
happens — which is how questions about diesel engines and the 1994 World Cup get
turned away for free. Questions the gate can't catch, because they are *about*
this campus but not covered by these documents — a hall that doesn't exist, the
opening hours of a gym nobody wrote about — reach the model with real documents
attached, and a grounding instruction is what stops it answering from what it
already knows. Both layers return the same sentence: *I don't have enough
information about that.*

## Chunking Strategy

**Chunk size:** 250 body characters maximum, 90 minimum, produced by
`chunker.py::split_documents`. "Body" means the text under the title line — the
title is repeated into every chunk and doesn't count against the budget. Real
output: 134 chunks from 88 documents, 217 characters on average, shortest 103,
longest 397.

**Overlap:** none. The title line is repeated instead.

The starter's 800-character window made 88 chunks out of 88 documents — it
never cut anything, because the longest document in `campus_life` is 549
characters and the average is 317. That isn't a bug, it's the finding: for these
documents, one post already is one chunk. The question is whether that's right,
and for about half of them it isn't. Kestrel Commons is one paragraph about
queues and stir-fry and a second about opening hours and the price of a swipe.
As a single chunk it matches a question about hours weakly and a question about
queues weakly. So: **split on paragraph breaks**, which in this corpus are where
the thoughts change.

Paragraph splitting alone would have been worse than what I started with. There
are 183 body paragraphs and 99 of them are under 120 characters — splitting on
every break turns half the index into fragments like *"Expect 4 hours a week
outside class."* So paragraphs are **packed**: they accumulate until the body
passes 250, and anything left under the floor merges back into the chunk before
it instead of being emitted alone. 250 because the median paragraph is 112
characters, so 250 holds the common two-short-paragraph case together while
still cutting a document that holds two separate thoughts. No paragraph is ever
cut open — the longest one in the corpus is 373 characters, and there is a hard
ceiling of 600 above which a paragraph would be split on sentence boundaries,
which never fires here.

**Overlap is zero, and that's a change from the starter's 120.** Overlap exists
to heal a cut that lands mid-sentence. My chunker only cuts at paragraph breaks,
so there is no cut to heal, and character overlap would drag a half-sentence
from the next paragraph onto the end of every chunk. What neighbouring chunks
share instead is the title line, because that is the context that actually goes
missing when you split one of these documents.

**The title line on every chunk is the part I'd defend hardest.** The seven
laundry documents are word-for-word identical apart from their first line and
one price line — *"There are eight washers and six dryers for the building,
which is the wrong ratio"* appears in all seven, verbatim. Take the second
paragraph of one of them on its own and nothing in the text says which building
it is. Not for a reader, and not for an embedding. The same is true of the 21
housing documents and the 27 course documents, which follow templates just as
closely.

**I changed my mind once, and the first version was wrong in an instructive
way.** I set the floor at 120 characters, ran it, and Kestrel Commons came out
whole — the exact document I'd written the splitter for. Its second paragraph is
101 characters, under the floor, so the "no orphan tails" rule glued it back on.
The floor was doing the opposite of its job: it was meant to stop fragments, and
instead it was swallowing complete thoughts. *"Hours are 7:00am to 9:00pm
weekdays, 9:00am to 8:00pm weekends. Costs one meal swipe, or $12.50 cash."* is
two complete sentences and answers a real question. Reading the paragraphs by
length showed the line sits lower than I guessed: under 60 characters they're
one-liners with no retrievable signal alone, and by 90 they're reliably two full
sentences. The floor moved to 90 and the corpus went from 111 chunks to 134.

There was also a measurement bug behind it. I was counting a group's length as
the sum of its paragraphs plus two characters per paragraph for the blank-line
join, which over-counts a single-paragraph group by two — a 119-character
paragraph measured as 121 and cleared a 120 floor it should have failed. The
length is now computed from the joined string, the thing actually being stored.

## Sample Chunks

### Chunk 1 — A document that came apart — the queue half

`source: dining_kestrel_commons.txt#0` · `produced by: chunker.py::split_documents`

```
Kestrel Commons

I'm a junior and I've done this twice now. Wait times: 20 to 25 minutes between 12:15 and 1:00, under 5 minutes before 11:45. The thing worth going for is the stir-fry station, made to order. The thing to know is that the salad bar wilts after 1:30.
```

### Chunk 2 — The other half of the same document

`source: dining_kestrel_commons.txt#1` · `produced by: chunker.py::split_documents`

```
Kestrel Commons

Hours are 7:00am to 9:00pm weekdays, 9:00am to 8:00pm weekends. Costs one meal swipe, or $12.50 cash.
```

### Chunk 3 — Why the title line is repeated

`source: housing_aldridge_hall_laundry.txt#0` · `produced by: chunker.py::split_documents`

```
Laundry in Aldridge Hall

Machines take $1.75 wash, $1.50 dry, card only. There are eight washers and six dryers for the building, which is the wrong ratio and means the dryers back up on Sunday evenings.
```

### Chunk 4 — A one-line paragraph packed with its neighbour

`source: course_econ_101.txt#0` · `produced by: chunker.py::split_documents`

```
ECON 101 Introduction to Economics

Took this last spring. Format is large lecture, 300 people, with small discussion sections. Assessment: two midterms and a final, all multiple choice. Curved, and generously.

Expect 4 hours a week outside class.
```

### Chunk 5 — A document left whole

`source: admin_housing_lottery.txt#0` · `produced by: chunker.py::split_documents`

```
On the housing lottery

The housing lottery is not random in the way most people assume. Rising sophomores get a number drawn at random, but juniors and seniors are ordered by accumulated credit hours first, and only tie-break randomly. That means a senior who took summer courses reliably beats a senior who didn't. Numbers come out the second week of March and selection runs over four evenings.
```

## Sample Answer

**Question:** How late in the semester can I declare a course pass/fail?

**Answer:**

```
  (best distance 0.206, cutoff 0.6)

You can declare a course pass/fail as late as week eight, after you've seen
your midterm.

Source: admin_pass_fail_option.txt

Sources retrieved: admin_add_drop_deadline.txt, admin_declaring_a_major.txt,
admin_graduation_requirements.txt, admin_pass_fail_option.txt,
advising_registration.txt
```

And the same system asked something it has no business answering, refused
before any model call was made:

```
$ python app.py ask "How do I change the oil in a diesel engine?"
  (best distance 0.923, cutoff 0.6)

I don't have enough information about that.

0 model calls this session
```

**My relevance cutoff:** **0.60**

| Question | In corpus? | Best distance |
|---|---|---|
| How is lottery order decided for juniors and seniors in the housing lottery? | yes | 0.2011 |
| How late in the semester can I declare a course pass/fail? | yes | 0.2058 |
| How long is the wait at Kestrel Commons between 12:15 and 1:00? | yes | 0.2129 |
| What time does the library close during reading week? | yes | 0.2192 |
| What do the laundry machines in Aldridge Hall cost, and how do you pay? | yes | 0.2446 |
| What is the capital of Mongolia? | no | 0.8246 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.8477 |
| How do I write a for loop in Rust? | no | 0.8768 |
| Who won the 1994 World Cup? | no | 0.8859 |
| How do I change the oil in a diesel engine? | no | 0.9231 |

Two groups, 0.201–0.245 and 0.825–0.923, with a gap 0.58 wide. Every cutoff
between 0.3 and 0.8 scores the same on this table, which is the problem with
it: **the gap is a measure of how easy I made both halves.** My five questions
use the corpus's own proper nouns — "Kestrel Commons", "Aldridge Hall",
"reading week" — and the out-of-scope five are from other planets. Nothing in
those ten numbers told me where to put the cutoff, so I went looking for the
middle.

| Probe | Best distance |
|---|---|
| "which building has somewhere quiet to work late at night" (covered) | 0.3384 |
| "when should I do my laundry to avoid waiting for a dryer" (covered) | 0.3790 |
| "What are the dorm rooms like in Ashford Hall?" (**no such hall**) | 0.4046 |
| "What time does the campus gym open?" (**not covered**) | 0.4214 |
| "is it worth eating lunch early to skip the queue" (covered) | 0.4823 |
| "can I still drop a class after seeing my midterm grade" (covered) | 0.5246 |
| "How much is tuition next year?" (**not covered**) | 0.5594 |
| "How do I sign up for intramural sports?" (**not covered**) | 0.6357 |

These two groups overlap, and they overlap in the wrong direction: a question
about a hall that does not exist (0.405) comes back *closer* than a real
question about dropping a class (0.525). **No cutoff separates them.** A
distance is a measure of topical similarity, and "campus housing, invented
building" is topically identical to "campus housing, real building".

So 0.60 is chosen against the covered questions, not the uncovered ones. It
clears the worst real paraphrase I found, 0.525, with enough room that a
clumsier phrasing of a question I can answer still gets answered. It sits below
the nearest uncovered campus question I found, 0.636. And it refuses all five
OUT_OF_SCOPE questions, which sit 0.22 above it, before a single model call.

What I get wrong at 0.60: the Ashford Hall question, the gym question and the
tuition question all pass the gate. They have to — anything low enough to stop
them refuses real questions first. Those are the grounding instruction's job,
and it does catch them; all three are refused at the second layer, which is
what that layer is for. What I'd get wrong at 0.45 is worse and quieter: I'd
refuse "can I still drop a class after seeing my midterm grade" while the
answer sat in the index.

**Two other retrieval decisions, both measured:**

*top_k stays at 5.* All five test questions put the answering chunk at rank 1,
so k=3 would have passed the same tests. I kept 5 because the second and third
chunks carry corroboration where one document is written up twice — the Kestrel
Commons question retrieves both the original post and the follow-up thread.

*But not all five chunks reach the model.* The cost of k=5 is noise on narrow
questions: the housing lottery question retrieves one chunk at 0.20 and four
between 0.71 and 0.79, and those four are parking permits and grade appeals.
Rather than lower k and lose the corroboration, `gate.relevant()` drops chunks
further than the cutoff before the prompt is assembled. Narrow question, one
chunk in the prompt; broad question, all five. Same number governs both, so
there's no second threshold to keep in step.

**The grounding instruction, and what I changed.** The starter's version held
up better than I expected. I tried to make it drift — asked about a hall that
doesn't exist with five real halls in the prompt, asked about the campus gym
when the nearest document is the shuttle timetable, asked about Kestrel Commons
at dinner when the corpus only covers lunch — and it refused all three without
being asked twice. I found no substitution to fix.

What I did change was the wording of refusals. The starter says "say you don't
have enough information", and the model did, in a different sentence every
time: *"I don't have enough information to answer your question, as Ashford
Hall is not mentioned..."*, *"I do not have enough information to answer what
time the campus gym opens."* None of them matched `gate.REFUSAL`, the sentence
the gate returns on its own path. The same outcome looked like two different
things depending on which layer produced it, and counting refusals meant
reading them one by one. The instruction now asks for that exact sentence, and
all four near-miss questions return it verbatim. I also added a rule naming the
substitution risk — don't answer about Aldridge when asked about Ashford — which
is precautionary rather than a fix, because this corpus is built from
near-identical templates and that is the specific way it would fail.

## How I Used AI

I used Claude Code throughout, and the two moments below are the ones where
what came back was not what went in.

**1. The chunker's minimum size, which was set to the wrong number and hid a
bug underneath it.** I asked for a chunker built from the measurements I'd
taken off the corpus: split on paragraph breaks, pack the short paragraphs
together, put the document's title line on every chunk, and never emit anything
under a 120-character floor. What came back did all four and passed every check
I could put to it — 111 chunks, nothing under the floor, nothing cut
mid-sentence, every chunk carrying its title. It was still wrong, and the
checks were never going to show it. Kestrel Commons came out as a single chunk,
and Kestrel Commons is the exact document the splitter existed for: one
paragraph about queues, one about opening hours and the price of a swipe. Its
second paragraph is 101 characters, under the floor, so the "no orphan tails"
rule glued it back onto the first. The floor was supposed to stop fragments and
was swallowing complete thoughts instead.

What I changed: I went back to the paragraph lengths rather than picking
another round number. Under 60 characters they're one-liners with no
retrievable signal alone — *"Expect 4 hours a week outside class."* — and by 90
they're reliably two complete sentences. The floor moved to 90 and the corpus
went from 111 chunks to 134. Chasing it also turned up a real bug in the code
that came back: a group's length was being computed as the sum of its
paragraphs plus two characters each for the blank-line join, which over-counts
a group of one, so a 119-character paragraph measured as 121 and cleared a
120-character floor it should have failed.

**2. A test question whose `expects` string would have scored a wrong answer as
correct.** I asked for five test questions specific enough to have right
answers, each with a short phrase a correct answer would have to contain.
One came back as *"How many washers and dryers are there in Aldridge Hall?"*,
expecting `eight washers`. Read on its own that looks fine, and it is exactly
the kind of question I'd have written myself.

What I changed: checking the phrase against the corpus before trusting it
showed that all seven laundry documents contain *"eight washers and six dryers
for the building"* word for word — the buildings differ only in their title
line and one price line. An answer about Old Brewhouse would have contained
`eight washers` and scored as correct, so the question would have been
measuring nothing. The only detail unique to Aldridge is that its machines are
card only, where the others are app-based, coin-only, or both. The question
became *"What do the laundry machines in Aldridge Hall cost, and how do you pay
for them?"* expecting `card only`, which now fails if retrieval brings back the
wrong building. Retrieval does get it right — Aldridge at 0.245, the
near-identical Old Brewhouse at 0.351 — but the test can now tell the
difference, which it couldn't before.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
