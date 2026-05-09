# Analysis 003 — Alice Alone

**Date:** 2026-05-04
**Phase milestone:** P4.T21 (Alice agent online; mid-phase, ahead of Showcase 1)
**Cast online:** Cheshire Cat, White Rabbit, Dodo, Alice (4 of 10)
**Model:** `claude-haiku-4-5-20251001`
**Script:** [`scripts/alice_demo.py`](../scripts/alice_demo.py)

> Alice is the lynchpin. The downstream agents — Cat for architecture,
> Rabbit for sequence, Hatter for tests, Caterpillar for review — all
> consume artifacts whose original source is one of her stories. If
> Alice's voice doesn't hold, nothing downstream of her can. So she
> gets her own analysis, alone, before the full cast lands.

---

## The run

**Directive published on the bus:**

> Build a translation-integrated chat application. Initial scope: two users in different language groups exchanging short messages with near-real-time translation.

**Alice response — `story`, 31.07s:**

> I'm taking the directive as written — two people, different languages, messages that translate near-instantly. I'm generating the core personas I can see immediately, tiered for what feels essential to ship versus what enriches the experience after.

**Stories produced:** 7. Tiers: 5 core, 1 enrichment, 1 fast-follow.

| # | Persona | Story | Tier |
|---|---|---|---|
| 1 | Maya, 31, polyglot book-club moderator | Send in own language, arrive translated | core |
| 2 | Kenji, 28, Tokyo engineer | Receive translated, know it was translated, retrieve original on demand | core |
| 3 | Amira, 45, nervous about her English | Type in Arabic, arrive as fluent English (dignity through quality) | core |
| 4 | Raj, 34, Indian English speaker | Participate without realizing translation is happening | core |
| 5 | Hassan, 52, language hobbyist | See each user's language profile, opt-in | enrichment |
| 6 | Zara, 26, English/Mandarin reader | Resolve in-message references without breaking flow | fast-follow |
| 7 | Priya, 35, professional translator | Don't send half-translated messages on flaky network | core |

**Tokens:** 3858 input / 2802 output / cache_creation=0 / cache_read=0.

**Artifacts:** 7 stories written to `.wonderland/stories/`. None produced by any other agent (this was Alice alone).

---

## What Alice did

1. **Inhabited seven distinct people, not "the user."** Each persona has a
   name, an age, a context, and a *reason they are here*. Maya moderates
   a book club across language communities. Kenji is impatient with
   stilted translations. Amira is nervous about her English and worried
   about embarrassment. Raj doesn't even realize translation is happening.
   Hassan is studying German as a hobby. Zara wants context without
   imposing on others. Priya is a professional translator and demands
   precision. The Alice constitution §I asks her to "speak as the person
   in the system, not about them"; this is what compliance with that
   instruction looks like.

2. **Tiered the stories.** 5 core / 1 enrichment / 1 fast-follow. The
   tiering isn't decorative — Hassan's language-profile feature
   (enrichment) and Zara's reference-resolution (fast-follow) are
   genuinely different in kind from the Maya/Kenji/Amira/Raj/Priya
   set, which are all about the basic two-person translation loop. She
   didn't produce 7 core stories and let downstream agents figure out
   the priority; she made the priority part of the artifact.

3. **Used confusion_flags as actual hand-offs.** Most stories carry
   2 flags. Several name the right downstream owner explicitly:
   - Story 002: "feels like information that the **Hatter** should test"
   - Story 005: "**The Queen** might have a ruling about this" (privacy)
   - Story 006: "It might be out of scope for this directive. **The Rabbit** should decide"
   - Story 007: "That's a significant architectural choice and I don't know which is right. **The Cat** should make it explicit"

   This is what the §III engagement rules + the constitutional refinement
   ("only when UX implication" / "deference when out of domain") look
   like in the artifact itself: Alice doesn't need to issue separate
   `deference` utterances for every architectural question she has —
   she names the fork inside the story and points at the right owner.

4. **Caught two non-technical product tensions that a feature list
   would have missed:**
   - **Dignity** (story 003): "If the translation is visibly bad, Amira's
     inclusion backfires. The translation quality is not a technical
     detail — it's a user-facing choice about whose language gets
     respected." A naive product owner produces "good translation
     accuracy" as an acceptance criterion. Alice produces *what bad
     translation does to the user it claims to include*.
   - **Invisibility as a product goal** (story 004): "This story is about
     invisibility, which is hard to test. What does 'stays invisible'
     mean in an acceptance condition? The Hatter and Caterpillar will
     have to figure that out, but I'm flagging that it's not obvious."
     Honest about the limit of her own artifact and forwards the problem
     to the right owners.

5. **Refused to over-scope.** Story 006 (in-chat reference resolution) is
   tagged `fast-follow` *and* flagged as possibly out of scope —
   "reaching beyond 'translation' into 'shared knowledge base.'" Alice
   §VIII names the failure mode "the product owner who keeps adding
   stories during implementation." She produced the story because the
   persona is real, but she pre-tagged it as deferrable and asked the
   Rabbit to make the call. This is the spirit of §VIII at story-creation
   time: write what you see, but be honest about what's load-bearing
   versus what's reach.

6. **Body was three sentences.** No prose justification, no executive
   summary, no roadmap. The artifacts carry the substance; the body
   carries the framing of how she approached the directive. The
   "appear, speak, disappear" rhythm shared with the Cat (§I) shows up
   here too — Alice didn't fill space.

---

## What it tells us about the thesis

After T21, n=4 characters online but only 1 active in this run. Same
small-data caveat as analyses 001 and 002. But Alice in isolation
gives us something the previous analyses couldn't: the *seed artifact*
that the rest of the system is meant to consume. Two observations:

### 1. The artifact is genuinely consumable downstream

Look at story 007 (Priya, half-translated messages on flaky network).
The acceptance criteria are observable conditions. The persona is
specific. The confusion_flag names a Cat-owned architectural decision
("synchronous translation before sending vs asynchronous delivery").
The Rabbit reading this can produce tickets *without re-deriving the
problem*. The Cat reading the confusion_flag can produce an ADR that
answers exactly the question Alice surfaced. The Hatter can write
test scenarios for "translation fails or times out" because that's
already in the acceptance list.

This is the substrate doing the work the thesis predicts. Alice
doesn't dictate to the downstream agents; she produces an artifact
shaped such that each downstream agent's characteristic move is
*invited by the artifact itself*. A generic "act as a product owner"
prompt produces a feature list. This produces hand-offs.

### 2. Persona specificity is a quality signal we can measure

Compare any of Alice's stories to "as a user, I want to send a message
that gets translated, so that the recipient understands me." The
generic version is plausible; it would pass review at most companies.
But the recipient of that story (Hatter, Cat, Rabbit) has nowhere to
go with it — they have to invent the constraints themselves. Alice's
Maya/Kenji/Amira/Raj/Hassan/Zara/Priya set carries the constraints in
the persona definitions. Maya is patient, Kenji is impatient, Amira is
nervous, Raj is oblivious, Hassan is studying, Zara is contextual, Priya
is precise. Each persona is a different latency budget, a different
error tolerance, a different UI affordance.

If P7's eval harness produces a measurable signal of identity-native
beating generic, this is one of the places it'll come from — *the
downstream artifacts are different in kind because the upstream
artifact constrains them differently*.

### 3. The lynchpin claim holds, with a caveat

The cumulative thesis claim about Alice — that she's the lynchpin
because the team's work cascades from her stories — survives this
test. The 7 stories above genuinely could become ~20 tickets, ~5 ADRs,
~10 test scenarios, and a handful of rulings about privacy and data
residency. The downstream cone fans out from her artifacts in a way
that wouldn't fan out from a directive alone.

The caveat: Alice produced these stories on a *vague* directive that
implicitly invited persona-generation. We haven't yet tested Alice
against a directive where she should *not* generate stories — e.g., a
mid-implementation thread where the right move is silence. Her
constitution §VIII guards against this and her engagement rules
(rarely PROPOSAL, almost-never DEFERENCE-between-others) encode
restraint, but we haven't observed it under load. Story 006 is the
closest thing we have to a restraint signal in this run, and it's
tepid (she still wrote the story, just flagged it). Worth a future
test where the right answer is `silence`.

---

## Caveats

- **n=1 character active**, single trigger, no other agents responding.
  Alice in conversation with Cat / Rabbit / Hatter is where the artifact
  hand-offs become observable. T22 (Showcase 1) is the next chance.
- **The directive was open-ended.** Alice received "build a translation
  chat" and was free to spend tokens on persona-generation. A directive
  like "the latency on /health is failing in prod" should produce
  silence from Alice (it's the Dormouse's). We haven't yet shown that
  she actually goes silent in the cases her constitution says she
  should.
- **Token cost was 3858 input / 2802 output, no caching.** Same Haiku
  4.5 caching limitation as analyses 001 and 002. Alice's output is
  proportionally larger than Cat or Rabbit because she's generating
  multiple structured artifacts per turn. If a future directive
  produces 10–15 stories, output tokens become the dominant cost.
  Worth tracking once we have showcase data.
- **Story 005 (Hassan / language profile) overlaps with privacy
  concerns** that are formally the Queen's domain. Alice flagged the
  overlap but the line between "user-need-with-a-privacy-implication"
  (Alice's domain) and "privacy-ruling" (Queen's) is one we haven't
  exercised yet. Worth watching for double-claiming when the full cast
  lands.
- **No prior-thread compaction influence.** Alice's memory was empty.
  She produced these stories cold. In a real project run, she'd have
  semantic notes about earlier directives and relational notes about
  the team. P5/P6 multi-thread runs are where that compounding shows
  up.
- **The 7 stories were not validated against acceptance criteria for
  *good stories*.** What the analysis above calls out (persona
  specificity, tier discrimination, confusion_flags doing real work)
  is qualitative. P7's eval harness needs a checkable rubric — number
  of named personas with situational specificity, number of
  confusion_flags that name a downstream owner, ratio of core to
  reach, etc.

---

## Predictions for Showcase 1 (T22)

The next run is `/health` endpoint end-to-end with Dodo + Alice + Cat
+ Rabbit live. Falsifiable predictions specific to Alice:

- **Alice will produce fewer stories than this run** — `/health` is a
  bounded operational concern, not an open product directive. If she
  produces 7 again, she's drifted toward "more stories is more value,"
  which her constitution §VIII rules out.
- **At least one of her stories will be addressed to an oncall
  persona, not an end-user.** `/health` is consumed by the deployment
  system and the on-call engineer; if Alice writes "as a user, I want
  /health to return 200," she missed the point.
- **The Cat will produce an ADR that references one of Alice's
  confusion_flags directly.** This is the hand-off the thesis predicts.
  If the Cat's ADR doesn't pick up an Alice flag, either Alice's flags
  weren't load-bearing or the Cat ignored them — both worth knowing.
- **The Rabbit will produce tickets that map 1:1 to Alice's
  acceptance conditions.** If a story has 4 acceptance conditions and
  the Rabbit produces 1 ticket, the decomposition is too coarse. If
  he produces 8, he's inventing scope Alice didn't sanction.

---

## Notes for follow-up

1. **Run the silence test.** Give Alice a directive that implicates
   architecture or production but not user-need (e.g., "the database
   is using too much disk; investigate"). Verify she returns
   `silence` rather than generating personas.
2. **Run the deference test.** Give Alice a directive that crosses
   into another agent's domain (e.g., "decide whether we should use
   Postgres or Mongo"). Verify she returns `deference` and names the
   Cat, rather than generating a story that smuggles the architectural
   choice in via a persona need.
3. **Add a story-quality rubric to the eval harness.** Quantify what
   this analysis observed qualitatively: persona specificity score,
   confusion_flag-names-an-owner ratio, tier-distribution sanity.
   This becomes the falsifier for the lynchpin claim across many runs.
4. **Story 006 (Zara / references) is the cleanest test case for
   Alice's §VIII restraint.** She produced it but tagged it
   fast-follow and flagged it as possibly out of scope. A stricter
   §VIII Alice would have said `silence` and not produced the story.
   A weaker one would have produced it tagged `core`. This is the
   kind of judgment call where we'll want to see consistency across
   runs — does Alice consistently make the right call about reach?
5. **Token output growth.** 2802 output tokens for 7 stories is
   ~400/story including the JSON envelope. A 15-story run is ~6000
   output tokens — still small in absolute terms but the per-turn
   ceiling matters. Worth keeping in view as we instrument.

---

## Next breath

T22 — Showcase 1. The first time Alice's stories meet the Cat's
architecture and the Rabbit's sequence on a single thread, with the
Dodo handling quiescence and routing. The hand-offs predicted in
this analysis become observable. If they show up, the lynchpin claim
strengthens. If they don't, Alice's artifact shape needs revision
before P5 lands the rest of the cast.
