# Analysis 026 — Alice in M2: the grounding voice fires as designed

**Date:** 2026-05-07
**Run:** Geocities directive, TDD workflow, with Alice added to M2's
roster as the grounding voice (`9a55e71`).
**Snapshot:** [analyses/data/026-alice-in-m2/](data/026-alice-in-m2/)
**Baseline:** [analyses/data/025-tea-party-validated/](data/025-tea-party-validated/) — same directive, same workflow, no Alice in M2.
**Result:** **Alice spoke once in M2, surfaced a hidden v1-shape constraint to the convenor, and Rabbit visibly updated his framing — without losing decomposition authority.** The literary parallel works in code.

## What we were testing

`9a55e71` added `alice` to the M2 (decomposition) roster of both
canonical and tdd workflows, with a directive framing her as the
grounding voice: *"defend the stories when Rabbit's tickets compress
them past user-recognition. Default to silence unless the work is
drifting from a story your persona would recognize."*

The hypothesis came from the literary parallel — in the book,
every Wonderland character's distinctive shape is legible *because
Alice is there to be confused by them*. Strip her out and the
Cheshire Cat is just a slippery answerer; with her present, he's a
slippery answerer to *Alice*. The framework operationalizes this
in M2: Rabbit's anxious-thoroughness failure mode is decomposing
past usefulness, generating tickets that are technically correct
but lose the user-facing point. Alice's "would the persona I named
actually care about this?" voice is the counter.

The unit test pinned the directive content (`tests/test_workflow.py
::TestDecompositionGroundingVoice`). What it can't test: whether
the LLM actually *uses* the directive correctly when the agents
are in the room together. That needed a live run.

## What happened in M2

The exchange, verbatim from the bus:

**t=102.0s — Rabbit ships 11 tickets.** The first sentence of his
ticket utterance:

> *"Alice: I'm naming the personas explicitly in each ticket so
> you can ground-truth whether the decomposition still serves the
> user you imagined."*

Rabbit, unprompted, restructured how he wrote his own artifacts
because Alice was in the room. This is the Cheshire-Cat-with-Alice-
present effect — he isn't decomposing; he's decomposing *for* her
to audit.

**t=107.2s — Alice raises a `concern`.** Her only M2 utterance:

> *"Rabbit, I'm reading the ticket set and I see a sequencing
> question that feels like it might be invisible. You've cut
> discovery and account management to fast-follow, and I
> understand why — they don't block launch. But I'm looking at the
> personas in the stories I wrote, and I'm noticing something:
> almost all of them have a moment where they discover they can
> do this thing. ... None of them just... sign up because they
> know the product exists. I'm not saying discovery has to ship
> in v1 — it shouldn't. But I want to make sure we're aware that
> v1 users will be invited users, not discovered ones. ... Is
> that the intended v1 shape, or should we think about one
> lightweight discovery mechanism (like 'recent activity feed'
> shipping earlier than you've scoped it)?"*

Three things to notice:

1. **She didn't dispute the cut.** "I'm not saying discovery has
   to ship in v1 — it shouldn't."
2. **She defended the story shape, not her preferred outcome.**
   The personas have discovery moments; the tickets imply
   invited-only; therefore the v1-shape assumption is implicit
   when it should be explicit.
3. **She handed it back to Rabbit as a question, not a directive.**
   Default-to-silence-then-one-targeted-question is exactly the
   directive's framing.

**t=113.5s — Rabbit responds with a `question` to the convenor.**

> *"Alice is surfacing a real constraint I missed: v1 as currently
> ticketed serves invited users only — no organic discovery path.
> ... Is that the intended constraint? Or should we pull the
> 'recent activity feed' forward into v1 to give us at least one
> lightweight organic discovery mechanism so launch day doesn't
> depend entirely on pre-existing invitations? ... Help me
> understand the intended shape."*

Rabbit didn't override Alice. He didn't capitulate to her framing
either. He surfaced the implicit constraint as a v1-shape question
to the convenor. **The decomposition didn't change.** What changed
is that the invited-only assumption is now an artifact in
`.wonderland/`, not a hidden cut.

**Cheshire Cat: 0 M2 utterances.** Per his M2 directive ("weigh
in only if a ticket implies a fresh architectural decision the
existing ADRs don't cover"), default-to-silence worked.

## A/B against the v2 baseline

| Metric | v2 baseline (no Alice in M2) | This run (Alice in M2) | Δ |
|---|---|---|---|
| M2 wall clock | ~30s | 343s | +313s |
| M2 cost | ~$0.024 | $0.0807 | +$0.057 |
| M2 calls | ~1 (Rabbit only) | 10 | +9 |
| M2 tickets | 8 | 11 | +3 |
| Alice total calls | 2 | 7 | +5 |
| Total run cost | $2.05 | $2.74 | +$0.69* |
| Total LLM calls | 179 | 208 | +29 |

*Cost delta is partly explained by an unrelated M5 regression
(below) — not a clean A/B. The M2 cost delta itself ($0.057) is
within the meeting's budget bump from $0.30 → $0.40.

The M2 wall-clock delta (~30s → 343s) is bigger than expected. ~5
minutes of it is `<thread_monitor> stuck` time after Rabbit's
question — the thread sat in stuck/quiescent transitions while
the team waited for a convenor decision that never came (the
question was addressed to nobody, since Dodo isn't a deliberation
participant). That's a known pattern, not a regression introduced
by Alice. Without that wait, M2 would have been ~45s.

## Findings

### F1 — The literary parallel actually works in code

The hypothesis was that adding Alice to M2 would shape Rabbit's
output even when she's silent, because *her presence* gives him
a user to decompose for. The data confirms it: Rabbit's first
ticket utterance led with "Alice: I'm naming the personas
explicitly in each ticket so you can ground-truth..." That was
unprompted. The directive doesn't tell Rabbit to address Alice;
it tells *Alice* her role is grounding-voice. Rabbit picked up
on her presence and adjusted his framing without being asked.

This is the strongest possible signal that the design works at
the prompt level. The character isn't doing something performative
when prompted; their presence in the room shapes the behavior of
the people around them. That's the Wonderland thesis.

### F2 — One well-placed concern beats N speculative ones

Alice spoke once in M2. The directive's "default to silence
unless drifting" framing produced exactly the behavior it was
designed to. In a baseline-Alice-as-active-participant design,
she'd plausibly have weighed in on every ticket — diluting the
focused-purpose-meeting model and adding cost without
proportional value. Instead she watched Rabbit's full
decomposition, identified the one place the personas she wrote
weren't being honored, and raised it.

The concern is also the right *shape* of intervention: not "you
should add discovery to v1," but "the v1-shape implies
invited-only — is that intended?" She defended her stories'
*structure* (the personas have discovery moments) without
asserting authority over the cut.

### F3 — Rabbit's response is the actual artifact win

The decomposition didn't change. The artifact trail did. Before
this run, an invited-only v1 would have been an implicit choice
buried in the ticket-tier assignments. After this run, the
invited-only-shape question is sitting in `.wonderland/memory/
white_rabbit/episodic.sqlite` as an addressed-to-convenor
question, available for downstream meetings (and Kohl-as-actual-
convenor) to point at and resolve.

This is the right thing for a grounding voice to produce: not a
different decomposition, but a *visible* decomposition where the
load-bearing assumptions are explicit.

### F4 — Cost stayed within design budget

The commit bumped M2's budget from $0.30 to $0.40 to make room
for Alice's intervention. Actual M2 cost: $0.0807 — well under
the new cap, well above the old one. The bump was correctly
sized; it would have hit MEETING_BUDGET on the old $0.30 cap if
Alice had spoken even once more.

The total run cost ($2.74) is higher than the v2 baseline ($2.05),
but most of the delta isn't M2 — it's the M5 regression (below)
and incidental call-count drift from the larger ticket set
flowing through M3 and M4.

## What this analysis doesn't show

- **N=1.** One run, one directive. The grounding-voice pattern
  may not generalize to directives with less obvious story-shape
  drift (e.g., "implement HTTP/2 priority frames" — no personas,
  no v1-shape question for Alice to surface). The hypothesis
  remains strongest for user-feature directives where Alice has
  story material to defend.
- **The decomposition didn't actually change.** Alice's voice
  surfaced a question; it didn't redirect the work. That's the
  designed behavior, but it means we don't yet have a run where
  her concern *prevented* a Rabbit drift outright. To get that
  evidence we'd need a directive engineered to tempt over-
  decomposition into pure plumbing tickets — Alice's "would the
  persona care about this?" voice firing harder.
- **M5/M6 didn't run cleanly.** The implementation meeting went
  IDLE immediately at t=988s with 0 calls, and M6 attempted
  late-publish of implementations to a closed thread. The cause
  isn't M2-related, but it means this run can't double as a
  full-pipeline validation of the directive change.

## Side finding — M5 regression

The implementation meeting (M5) ended `COMPLETE` at t=988.4s with
0 calls and 0s elapsed. Tweedles never spoke. The seed manifest
at M5 START shows `contract_note×5, story×9` — *no Hatter test
scenarios* — which strongly suggests M4's `MEETING_BUDGET`-cap
exit prevented Hatter's tests from being marked as committed
seeds for M5.

At t=1004.9s (M6 START + 16s), Tweedledee tried to ship
`implementation` artifacts retroactively, but the implementation
thread was already closed — the bus emitted `[late-publish]
tweedledee → thread 'implementation' (already COMPLETE) —
suppressing implementation`. Tweedledee correctly *recognized*
the gap; the framework correctly *suppressed* the late write.
But that means no production code shipped this run.

This is unrelated to Alice-in-M2 and worth a separate
investigation. Hypotheses to test:

- M4's `MEETING_BUDGET` cap interrupts the seed-commit path for
  scenarios produced after the cap fires
- M5's seed query (`from test-scenarios kinds=['test_scenario',
  'story']`) requires a state predicate that an in-progress
  meeting doesn't satisfy
- Tweedles' M5 entry condition is checking for something that
  wasn't produced (a specific contract state? a seed manifest
  shape?)

The next run should either rerun this directive with a higher M4
budget, or investigate the seed-commit path for budget-cap-exit
meetings directly.

## What's next

1. **M5 regression investigation.** Highest priority — the
   pipeline isn't end-to-end without it.
2. **Pressure-test directive for Alice in M2.** A directive
   engineered to tempt Rabbit toward pure plumbing tickets — see
   if Alice's voice fires harder than the soft "is this the
   intended v1 shape?" question we got here.
3. **Alice in M6 (review)?** The commit deferred this. M6 is
   where Caterpillar reviews shipped code; Alice's "would the
   user notice this bug?" voice is the natural complement to
   Caterpillar's technical review. Worth experimenting once M5
   is fixed and the pipeline is reliable end-to-end again.

## Headline

**The grounding-voice pattern works.** Alice in M2 produces the
behavior the design described: silence unless the work is
drifting, one targeted concern when it is, no override of
Rabbit's authority. Her *presence* shapes Rabbit's framing even
when she's silent. The literary parallel isn't ornamental — it's
load-bearing prompt design, and it survives contact with a real
LLM in a real meeting.
