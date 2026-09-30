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
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Every chunk carries its document's title line | all chunks | 134/134 | 134/134 | 134/134 | MET |
| 5. Gate does not refuse questions the corpus can answer | 0 refused of 5 | 0/5 | 0/5 | 0/5 | MET |

Three runs of `python run_eval.py --label before`, caching off, corpus
`campus_life`, top-k 5, cutoff 0.60. The run it produced is
`results/run_2026-09-30_0158_before.md`; an earlier pass,
`results/run_2026-09-30_0149_before.md`, is committed too and agrees with it on
every distance and every verdict. There is no `scorer.py` yet, so the Run
columns in those files are blank and the counts above are my own reading of the
fifteen answers.

**Four of these five criteria don't move between runs, and that's a property of
the system rather than a shortcut.** Only criterion 2 is measured on generated
text. Criterion 3 is a comparison against a fixed number, criterion 4 is a
property of the index, and criteria 1 and 5 are decided by retrieval, which
returned byte-identical distances on all three runs and again on the 01:49 pass
— 0.2129, 0.2058, 0.2446, 0.2192, 0.2011, the same five numbers every time. So
the one column that could have varied is criterion 2, and it came out 5/5 three
times: all fifteen answers named a file.

Criterion 1 needed a check the run log can't give me. The run log names the
*documents* retrieved, but my chunker splits 88 documents into 134 chunks, so
"`study_library_hours.txt` was retrieved" doesn't establish that the chunk
retrieved was the one with the closing time in it. As it happens, reading the
document names would have given the same 5/5 — but that was luck rather than
evidence, and `check_retrieval.py` shows why it isn't safe to rely on next time:
for two questions the chunk carrying the answer is not the top-ranked chunk of
its own document. `dining_kestrel_commons.txt` is retrieved twice over, as
`#1` at 0.281 without the wait time in it and as `#0` at 0.426 with it, and the
`card only` line comes back in `housing_aldridge_hall.txt#1` rather than in that
file's first chunk. The run log prints one document name in both cases. Any
change to the chunking would move which chunk that is, so a document-level
reading could report a pass on a chunk that doesn't hold the answer.

The miss I predicted in `criteria.md` didn't happen. I wrote that the housing
lottery question would be the one criterion 1 failed on, and instead it is the
closest match of the five, at 0.2011. I have left the prediction where it is and
will diagnose it under Milestone 3 rather than editing it now.

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

### Real output

All of it is from the same set of runs, 2026-09-30. Full files:
`results/run_2026-09-30_0158_before.md` (the three runs) and
`results/checks_2026-09-30_before.txt` (the two checks).

**Criterion 1 — retrieved chunk contains the answer.** Produced by
`check_retrieval.py::check`, over chunks from `chunker.py::split_documents`
retrieved by `store.py::search` and trimmed by `gate.py::relevant`. Two of the
five questions, including the one where the chunk index matters:

```
What do the laundry machines in Aldridge Hall cost, and how do you pay for them?
  expects: 'card only'
  best distance: 0.2446 (passed the gate)
  chunks given to the model: housing_aldridge_hall_laundry.txt#0 at 0.245, housing_aldridge_hall.txt#1 at 0.307, housing_old_brewhouse_laundry.txt#0 at 0.351, housing_old_brewhouse.txt#1 at 0.372, housing_innisfree_hall_laundry.txt#0 at 0.385
  ANSWER PRESENT in: housing_aldridge_hall_laundry.txt#0 at 0.245, housing_aldridge_hall.txt#1 at 0.307

How is lottery order decided for juniors and seniors in the housing lottery?
  expects: 'credit hours'
  best distance: 0.2011 (passed the gate)
  chunks given to the model: admin_housing_lottery.txt#0 at 0.201
  ANSWER PRESENT in: admin_housing_lottery.txt#0 at 0.201

Criterion 1 — answer present in a retrieved chunk: 5 of 5
```

Note the second one: the gate kept a single chunk out of the five retrieved. The
other four came back between 0.71 and 0.79 and `gate.py::relevant` trimmed them,
so the model answered from one chunk.

**Criterion 2 — every answer names a source.** Produced by
`generate.py::answer_from_chunks`, logged by `run_eval.py::write_report` into
`results/run_2026-09-30_0158_before.md`. The housing lottery question on three
separate runs, to show what does and doesn't vary between them — the distance
and source lines are the run log's, the fenced text is the answer as produced:

Run 1 — best distance 0.2011 (passed the gate), sources retrieved
`admin_housing_lottery.txt`:

```
Juniors and seniors are ordered by accumulated credit hours first, and only tie-broken randomly.

Source: admin_housing_lottery.txt
```

Run 2 — best distance 0.2011 (passed the gate), sources retrieved
`admin_housing_lottery.txt`:

```
For juniors and seniors, lottery order is determined by accumulated credit hours first, with a random tie-break used only when necessary.

Source: admin_housing_lottery.txt
```

Run 3 — best distance 0.2011 (passed the gate), sources retrieved
`admin_housing_lottery.txt`:

```
Juniors and seniors are ordered by accumulated credit hours first, and only tie-broken randomly.

Source: admin_housing_lottery.txt
```

The wording moves between runs and the cited file does not. Across all fifteen
answers the citation format varied — `Source: x.txt` on its own line, `(Source:
x.txt and y.txt)`, or a bare `(x.txt)` at the end of the sentence — but every
one of the fifteen named at least one real file from the corpus, which is what
the criterion asks. It does not ask that the citation be the right file, and I
did not count that here; see the note at the end of criterion 2 in `criteria.md`.

**Criterion 3 — the gate stops out-of-corpus questions.** Produced by
`run_eval.py::check_out_of_scope`, deciding with `gate.py::check` at cutoff
0.60. One deterministic pass, which is why the same number is in all three run
columns:

```
| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.825 | refused |
| How do I change the oil in a diesel engine? | 0.923 | refused |
| Who won the 1994 World Cup? | 0.886 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.848 | refused |
| How do I write a for loop in Rust? | 0.877 | refused |
```

Each of those returns `I don't have enough information about that.` from
`gate.py`, and costs no model call, because a refused question never reaches
`generate.py`. The ibuprofen question is the one I expected to slip through,
because `health_center.txt` is in the corpus; it came back at 0.848, which is the
nearest of the five out-of-corpus questions bar Mongolia — so my reasoning was
roughly right and it still wasn't a close call.

**Criterion 4 — every chunk carries its document's title line.** Produced by
`check_titles.py::check`, which reads the indexed collection back out of Chroma
rather than re-chunking the documents, so it measures what the system is
actually searching:

```
Collection: campus_life__default
Documents on disk: 88
Chunks indexed: 134
Chunks containing their document's title line: 134 of 134
Chunks that are nothing but a title line (trivial passes): 0
Index is current with chunker.py::split_documents (134 chunks, same ids and same text).

All indexed chunks carry their title line.
```

The last two lines were added in Milestone 2, when I went looking for ways this
number could be true and worthless: a chunk that is only a title carries its
title by definition, and a count taken over an index older than the chunker is a
count about code I no longer run. Neither applies here.

This is the criterion that stopped being free. In unit 1 the starter's
fixed-window chunker cut nothing and all 88 documents went in whole, so their
titles were attached by definition. The paragraph-packing chunker in
`chunker.py::split_documents` produces 134 chunks from those 88 documents — 46
chunks that are not the start of their file — and each one has the title line
prepended deliberately.

**Criterion 5 — the gate does not refuse questions the corpus can answer.**
Produced by `gate.py::check`, reported by both `run_eval.py::main` and
`check_retrieval.py::check`:

```
How long is the wait at Kestrel Commons between 12:15 and 1:00?
  best distance: 0.2129 (passed the gate)
How late in the semester can I declare a course pass/fail?
  best distance: 0.2058 (passed the gate)
What do the laundry machines in Aldridge Hall cost, and how do you pay for them?
  best distance: 0.2446 (passed the gate)
What time does the library close during reading week?
  best distance: 0.2192 (passed the gate)
How is lottery order decided for juniors and seniors in the housing lottery?
  best distance: 0.2011 (passed the gate)

Criterion 5 — answerable questions refused by the gate: 0 of 5
```

(The `expects` and chunk lines between each pair are cut for length — the full
output is in `results/checks_2026-09-30_before.txt`.)

The five answerable questions sit between 0.201 and 0.245; the five
out-of-corpus ones between 0.825 and 0.923. The cutoff of 0.60 sits inside a gap
0.58 wide with nothing in it, which is why neither criterion 3 nor criterion 5
is close: within these runs the narrowest margin between the cutoff and any
distance is 0.225, the Mongolia question. Unit 1 found tighter ones by going
looking for them — a paraphrase of an answerable question at 0.525 and an
uncovered campus question at 0.636 — so the gap is this clean only for the ten
questions in this run log.

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer, 4 of 5 | MET | 5 of 5 on all three runs. I didn't take the `expects` substring's word for it — I opened all five source documents and read the sentence the chunk was matching on, so the count is "the chunk holds the answer", not "the chunk holds the phrase". |
| 2 | Every answer names a source, 5 of 5 | MET | All 15 answers named at least one file. The citation format wandered between runs and the file never did, and `tools/audit_citations.py` confirms no answer cited a file that retrieval hadn't returned for that question — so none of the 15 passed on an invented filename. |
| 3 | Gate stops out-of-corpus questions, 4 of 5 | MET | 5 of 5 refused at 0.825–0.923 against a 0.60 cutoff. The run log only proves `gate.py::check` said no, so I re-asked all five through `app.py ask` and got the exact wording the criterion names, at 0 model calls. |
| 4 | Every chunk carries its document's title line, all chunks | MET | 134 of 134, counted over the indexed collection rather than a re-chunk. The number would be worthless on a stale index, so `check_titles.py` now also compares stored ids and text against `split_documents`, and they match. |
| 5 | No test question refused by the gate, 0 of 5 | MET | 0 refused; the five sit at 0.201–0.245 against a 0.60 cutoff, so none was near the line. But see below — this is the verdict I trust least, and the reason isn't the number. |

No criterion was revised. I went looking for one — a criterion that turned out
unmeasurable would have been worth more to me than a fifth MET — and none of the
five had that problem. All five said something checkable, and I checked them the
way they were written.

### Arguing the other side

Five METs is the shape of a run log that flattered itself, so I tried to break
each verdict rather than confirm it. The output is in
`results/verdict_checks_2026-09-30.txt`. Four of the five attacks failed:

- **Criterion 1: the `expects` phrase isn't the answer.** `10pm` appearing in a
  chunk doesn't mean that chunk says the library closes at 10pm during reading
  week — it could be term hours, with reading week elsewhere. This was the
  attack I expected to land, because `study_library_hours.txt` holds both
  numbers. It says *"Open until 2am during term, until 10pm during reading
  week"* — same sentence, and reading week is the one attached to 10pm. All five
  survived reading: the pass/fail chunk says *"you can declare it as late as
  week eight"*, the laundry chunk *"$1.75 wash, $1.50 dry, card only"*, the
  lottery chunk *"juniors and seniors are ordered by accumulated credit hours
  first"*. No question passed criterion 1 on a phrase that appeared for the
  wrong reason.
- **Criterion 2: a named source could be a fabricated filename.** Criterion 2 as
  written would count `dining_kestrel_hall.txt` — a file that doesn't exist — as
  naming a source. `tools/audit_citations.py::audit` found 0 of 15 citing
  anything retrieval hadn't returned. The criterion is weaker than I'd write it
  today, but the system doesn't exploit the weakness.
- **Criterion 3: I measured the gate, not the system.** The criterion says the
  *system* returns "I don't have enough information about that", and
  `run_eval.py::check_out_of_scope` only records a boolean. Re-asking all five
  through `app.py ask` produced that string exactly, five times.
- **Criterion 4: the check could be passing on a stale index.** `check_titles.py`
  read Chroma, and nothing said Chroma matched the current chunker — if the
  index were left over from the fixed-window chunker, 134 of 134 would be a fact
  about code I no longer run. It matches: same 134 ids, same text, and no chunk
  is title-only, so nothing passed by being nothing but its title.

**The fifth attack lands, and I'm recording it as a weakness rather than a
miss.** Criterion 5 asks whether the gate wrongly refuses questions the corpus
can answer, and my five test questions are the easiest possible way to ask that.
Each one shares its proper nouns with the document that answers it — "Kestrel
Commons", "Aldridge Hall", "pass/fail", "reading week" — which is why they land
at 0.201 to 0.245 and why the criterion says zero and not one. So 0 of 5 is real
but it is measured at the easy end of the range, and my own Milestone 4 numbers
say where the hard end is: the worst paraphrase I could write of a question the
corpus answers came in at 0.525. That is 0.075 from the cutoff, not 0.355. A
paraphrase set rather than a proper-noun set is what would actually put
criterion 5 at risk, and criterion 5 as written doesn't require one.

That is a gap in the criterion, not a misreading of the result, so the verdict
stays MET and the fix is a new measurement — five paraphrased questions that
never touched the threshold. Milestone 5, not here.

Criterion 1's target has the same shape of problem. 4 of 5 was set expecting the
housing lottery question to fail, and it came back the *closest* match of the
five at 0.2011 — so the target held with a question to spare, and a target that
survives the one question it was written around is looser than it looked. That's
Milestone 3's problem, not a revision: the criterion measured what it said.

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

I missed nothing. Five of five MET, and three of the five were not close: 5 of 5
against a target of 4, 134 of 134, 0 refusals out of 5.

So the honest question isn't which stage failed. It's whether five targets that
all held say anything about the system, and going through them one at a time the
answer is no. **My five criteria were set low in one way, for one reason, and it
is a property of the question set rather than of five separate targets.**

### The pattern: every criterion is measured at the ends, never in the middle

`check_boundary.py::measure` puts all eighteen questions I have on one axis —
the five test questions, the eight near-boundary probes from Milestone 4, and
the five out-of-scope questions — sorted by distance, with what the gate does to
each. Full output in `results/boundary_2026-09-30.txt`:

```
  dist  gate            group                      question
 0.201  answers         test question (covered)    How is lottery order decided for juniors and seniors
 0.206  answers         test question (covered)    How late in the semester can I declare a course pass
 0.213  answers         test question (covered)    How long is the wait at Kestrel Commons between 12:1
 0.219  answers         test question (covered)    What time does the library close during reading week
 0.245  answers         test question (covered)    What do the laundry machines in Aldridge Hall cost,
 0.338  answers         probe (covered)            which building has somewhere quiet to work late at n
 0.379  answers         probe (covered)            when should I do my laundry to avoid waiting for a d
 0.405  answers  wrong  probe (uncovered)          What are the dorm rooms like in Ashford Hall?
 0.421  answers  wrong  probe (uncovered)          What time does the campus gym open?
 0.482  answers         probe (covered)            is it worth eating lunch early to skip the queue
 0.525  answers         probe (covered)            can I still drop a class after seeing my midterm gra
 0.559  answers  wrong  probe (uncovered)          How much is tuition next year?
                                                   ── cutoff 0.6 ──
 0.636  refuses         probe (uncovered)          How do I sign up for intramural sports?
 0.825  refuses         out of scope (uncovered)   What is the capital of Mongolia?
 0.848  refuses         out of scope (uncovered)   What is the recommended dosage of ibuprofen for a he
 0.877  refuses         out of scope (uncovered)   How do I write a for loop in Rust?
 0.886  refuses         out of scope (uncovered)   Who won the 1994 World Cup?
 0.923  refuses         out of scope (uncovered)   How do I change the oil in a diesel engine?

covered questions, distance range:   0.201 – 0.525
uncovered questions, distance range: 0.405 – 0.923
the gate is wrong about 3 of 18, all of them uncovered questions it answers:
  0.405  What are the dorm rooms like in Ashford Hall?
  0.421  What time does the campus gym open?
  0.559  How much is tuition next year?
```

Read the third column. **Every question any of my five criteria is measured on
is one of the ten at the two ends of that list.** The five test questions occupy
0.201 to 0.245; the five out-of-scope questions occupy 0.825 to 0.923. The eight
questions in between — the region where covered and uncovered actually overlap,
0.405 to 0.525 — are governed by no criterion I wrote. That is why all five held,
and it is one fact about my test set rather than five facts about my targets.

The three the gate gets wrong are all in that middle, and all the same kind of
wrong: an uncovered question it answers. Not one of them is reachable by any
criterion I have. Criterion 3 asks about out-of-corpus questions and tests it
with Mongolia and diesel engines; criterion 5 asks about answerable questions and
tests it with five that share proper nouns with their documents. Neither can see
a question about a hall that doesn't exist.

### The stage, and the mechanism

**Embedding, surfacing at retrieval.** Not a bug — a limit I built a criterion
around without noticing. A cosine distance measures topical similarity and
nothing else, so *"What are the dorm rooms like in Ashford Hall?"* is
topically indistinguishable from the same question about Aldridge: campus,
housing, dorm rooms, one proper noun. The index has twenty-one housing documents
and the invented hall lands at 0.405, closer than *"can I still drop a class
after seeing my midterm grade"* at 0.525, which the corpus genuinely answers.

The gate is a single scalar compared against a single number. "On topic but not
covered" is not a distance, so no value of `THRESHOLD` expresses it — which is
what my unit 1 notes already said ("no cutoff separates them") and what
criterion 3 then quietly stopped testing by pinning itself to five questions
from other planets. The generation stage is what actually catches these: unit 1
found all three refused by the grounding instruction in `generate.py`. So the
system has a second layer doing the work, and **no criterion of mine measures
that layer at all** — the one place the mechanism lives is the one place I never
put a number.

### Were the targets set low, and which would I tighten

Yes — four of the five, and only criterion 4 comes out of this clean. I can put
numbers on how much slack each was carrying.

| Criterion | As written | What the system actually does | Slack |
|---|---|---|---|
| 1. Answer in retrieved chunks | 4 of 5, anywhere in the kept chunks | 5 of 5, and at **rank 1** every time (`check_retrieval.py`, ranks 1,1,1,1,1) | Two ways: one question of headroom, and four ranks |
| 2. Answer names a source | any source, 5 of 5 | 15 of 15 name a file, all retrieved, and all 15 cite a file that **contains** the answer (`tools/audit_citations.py`) | Counts naming, not correctness |
| 3. Gate stops uncovered questions | 4 of 5, on `OUT_OF_SCOPE` | 5 of 5 there — and **1 of 4** on uncovered questions about this campus | The sample, entirely |
| 4. Chunks carry title line | all chunks | 134 of 134, 0 trivial passes, index current | None — this one is honest |
| 5. No answerable question refused | 0 of 5, proper-noun questions | 0 of 5, and 0 of 4 on harder paraphrases too, though 0.525 leaves only 0.075 | The sample |

**The one I would tighten is criterion 3, and I would change its question set
rather than its number.** New version:

> When I ask a question about this campus that my documents don't cover, the
> system returns "I don't have enough information about that" for at least 4 of
> 5 — measured on five questions that are on-topic and uncovered, not five from
> unrelated domains.

That is the tightening worth having because **it is the only one that fails
today.** Of the four on-topic uncovered questions I have, the gate stops exactly one:
Ashford Hall at 0.405, the gym at 0.421 and tuition at 0.559 all pass it, and
only intramural sports at 0.636 is refused. I need a fifth before I can state it
as "of 5", but 1 of 4 against a target of 4 of 5 is a MISS by any rounding — and
a MISS that points at something real rather than at a number I chose badly.

The other two tightenings I'd make are worth less, because both already pass:
criterion 1 becomes "the **top-ranked** kept chunk contains the answer, 4 of 5"
(currently 5 of 5), and criterion 2 becomes "every answer names a source
document that **contains** the answer it gave" (currently 15 of 15). Neither
would have caught anything this unit. They are regression guards for Milestone
4's change, not new challenges — if a chunking change pushes an answer from rank
1 to rank 4, criterion 1 as written still passes and I never hear about it.

**I have not revised anything in `criteria.md`, and I don't think I should.** A
criterion that measured what it said, on the set it named, and came out MET is
not broken; it's easy. The rule I was given is that a target I merely beat stays
where it is, and criterion 3 named its five questions explicitly, so 5 of 5
stands as the answer to the question I actually asked. What I've found is that I
asked an easy question — which belongs here in the diagnosis, where it can drive
the improvement, rather than rewritten into last unit's file where it would look
like I'd known all along.

One honest complication, since criterion 3 is the one I'm calling easy: its
*words* are broader than its question set. "A question my documents clearly
don't cover" describes Ashford Hall — there is no Ashford Hall — and the system
answers that one. `criteria.md` pins the criterion to the five in `OUT_OF_SCOPE`,
so MET is the correct verdict for it as written. But a reader going by the
sentence alone would reach the opposite verdict, and they would be pointing at
the more useful truth.

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
