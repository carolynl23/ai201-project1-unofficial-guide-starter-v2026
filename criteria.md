# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:** No document in this corpus reaches 800 characters — the
average is 317 — so a whole document fits inside one chunk and retrieving the
right document *is* retrieving the answer. Three of my questions ask about
subjects only one document covers (pass/fail rules, library hours, Aldridge
Hall's laundry prices) and a fourth, the Kestrel Commons wait time, is stated
identically in two documents, which gives retrieval two chances at it.

The fifth is the housing lottery question, and that's the one I expect to miss.
The fact I want — juniors and seniors are ordered by accumulated credit hours,
not drawn at random — shares almost no wording with the question, and "lottery"
and "housing" sit in a corpus holding twenty other housing documents, seven of
them laundry documents that are word-for-word identical apart from a price line.
Five of five would mean I'd written five easy questions.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:** All five, because naming a source isn't a retrieval
problem — every chunk carries its filename in metadata, so the source is
already in hand by the time the model is called and the prompt only has to
print it. Nothing about the corpus makes it hard. If this one fails it's a bug
in my prompt or in how I pass metadata through, not a close call, which is
exactly why a target of four would be letting myself off.

Note what this criterion does *not* claim: it counts that a source is named,
not that it's the right one. Criterion 5 is where I'd normally put that, but I
had a bigger gap to close — see below.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:** I'm writing this before Milestone 4, so I haven't
measured the two groups yet — the cutoff is still the starter's 0.6 and I'll
record the actual distances here when I set it. My reason for expecting 4 of 5
rather than 5 of 5 is the corpus: every document is one campus's student advice,
and my five out-of-scope questions (Mongolia, diesel engines, the 1994 World
Cup, ibuprofen, Rust) come from domains the corpus has no vocabulary for at all,
so I expect them to land far away. The one I'd bet on slipping through is the
ibuprofen question, because health_center.txt exists and is about a health
centre, walk-in hours and waits — close enough in topic words that it could sit
near whatever gap the other four leave.

---

## 4. Something about your chunks

Every chunk contains the first line of the document it came from — the line
that names the hall, the dining hall, or the course. All chunks, not a sample,
counted by a check over the indexed collection.

**Why this target:** The seven laundry documents are word-for-word identical
apart from their first line and their price line. "There are eight washers and
six dryers for the building, which is the wrong ratio" appears in all seven,
verbatim. Strip the title line off one of those chunks and there is no way —
for me reading it, or for an embedding — to tell Aldridge Hall's laundry from
Old Brewhouse's. The same holds for the other fourteen housing documents
and the twenty-seven course documents, which follow templates just as closely.

Right now this passes for free: no document in the corpus reaches 800
characters (the longest is 549, the average is 317), so the starter's
fixed-window chunker splits nothing and all 88 documents come out as 88 whole
chunks with their titles attached. It becomes a real constraint in Milestone 3,
where the obvious move on documents of two to five paragraphs is to split on
paragraph breaks — and that is precisely the change that would orphan a body
paragraph from its title. I want the criterion written down before I make that
change, not after.

---

## 5. The gate does not refuse questions the corpus can answer

None of my five test questions is stopped by the relevance gate. Zero false
refusals out of five, at whatever threshold I end up setting in Milestone 4.

**Why this target:** Criterion 3 can be passed by a system that is useless. Set
THRESHOLD to 0.0 and every out-of-corpus question is refused, 5 of 5, along with
every other question ever asked. Nothing above catches that, because criteria 1
and 2 are about retrieval and about the text of answers that do get produced,
and a refusal produces no answer to check. So the one number I care most about
getting right — the cutoff — is measured in only one direction.

This criterion measures the other direction, and the pair of them pins the
threshold from both sides: criterion 3 pushes it down, this pushes it up, and
Milestone 4 is the job of finding a value that satisfies both. Zero and not one,
because these five questions use the same words as the documents that answer
them ("Kestrel Commons", "Aldridge Hall", "pass/fail", "reading week"). A
question that shares its proper nouns with the document it comes from should not
be a borderline distance. If one of these is refused, the cutoff is in the wrong
place — and the honest failure mode is that the housing lottery question is both
the one criterion 1 expects to retrieve badly and the one most likely to be far
enough away to be refused, in which case I'd miss two criteria on one question.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
