# Analysis 016 — Cat's Structural Deafness: When Engagement Filters Become Critical Path

**Date:** 2026-05-05
**Phase milestone:** P6.T36 — translation chat MVP enchilada, v3→v10 calibration arc
**Components touched:**
- `src/wonderland/agents/cheshire_cat.py` (STORY engagement rule + synthesis protocol)
- `src/wonderland/agents/tweedles.py` (sibling-question rule + INVITE constraint)
- `src/wonderland/agent.py` (engagement-state annotation)
- `src/wonderland/primer.py` (§IX Context as Breath)
- `src/wonderland/runner.py` (convene timestamp restamp)
- `tests/test_cheshire_cat.py` (test updated for new STORY behavior)
**Run transcripts:**
- [v7](./data/016-cat-story-deafness/v7/run.log) — pre-Tweedle-INVITE, M3 collapses
- [v8](./data/016-cat-story-deafness/v8/run.log) — INVITE constraint lands, M3 ships contracts
- [v9](./data/016-cat-story-deafness/v9/run.log) — Cat silent in M1, whole arc collapses
- [v10](./data/016-cat-story-deafness/v10/run.log) — Cat synthesis fix, every artifact lands
- [v10 wonderland artifacts](./data/016-cat-story-deafness/v10/wonderland-artifacts/) — full on-disk state
**Comparison baseline:** [analysis 015](./015-tweedles-ship-real-code.md) —
single-meeting tool-use proof; this analysis is the multi-meeting
arc that surrounds it.

> The translation-chat enchilada (5 meetings: scoping → decomposition →
> contract negotiation → implementation → review) refused to terminate
> end-to-end across v3-v9. v8 fixed Tweedle drafting via an INVITE
> constraint and produced the first contract notes in M3. v9 then
> collapsed when Cat didn't ship an ADR in M1 — surfacing that
> Cat's STORY engagement was filter-deaf to user-shaped stories.
> v10 broadens Cat's STORY engagement and adds synthesis protocol;
> every artifact type lands (4 stories, 3 ADRs, 6 tickets, 5 rulings,
> 2 agreed contract notes, 1 implementation declaration). The
> remaining bottleneck is implementation declaration → actual
> source on disk.

---

## The arc shape

Five meetings, sequenced through `Runner.convene` with seed
re-stamping (analysis 014's substrate). Per-meeting budget caps to
prevent any single meeting from starving downstream:

| # | Meeting | Roster | Goal |
|---|---|---|---|
| M1 | scoping | Alice + Cat + Queen + Dodo | stories + ADR + GDPR rulings |
| M2 | decomposition | Cat + Rabbit + Dodo | tickets from stories+ADR |
| M3 | contract-negotiation | Cat + Tweedles + Dodo | contract notes |
| M4 | implementation | Tweedles + Dodo (tools-on) | code on disk |
| M5 | review | Caterpillar + Tweedles + Dodo | findings |

Across v3–v7 the arc died in M3: Tweedles silent, no contracts
shipped, M4/M5 starved.

## v8: the Tweedle INVITE constraint

The v6 transcript revealed the M3 stall pattern: Tweedledum would
`INVITE` Cat for input on the contract; Cat would respond with a
Socratic question; Tweedledum wouldn't follow up; meeting quiesced.
The Cat was being Cat — riddles are character-true — but the
Cat-Socratic-deflect dynamic meant INVITE was working as a stall
vector inside contract negotiation.

Fix: protocol section in `tweedles.py` blocking INVITE during
contract drafting before the pair has shipped any contract notes
on the thread.

```python
# from src/wonderland/agents/tweedles.py
**But contract negotiation is the pair's work, not a consultation.**
Do *not* `invite` to originate a contract. The pair drafts; the
contract becomes concrete through your negotiation with your
sibling, not by deferring upstream. If the pair has shipped zero
contract notes on this thread, your next move is `contract_note`
(half-formed is fine, `state=proposed`), `question` to your
sibling, or `concern` — never `invite`. Once a draft exists,
collaborators can `concern` or `respond`; until then the work is
yours. The Cat in particular will Socratically probe rather than
answer when invited mid-draft (that's the Cat being Cat); don't
summon riddles you'll then have to wait through. Ship the draft
first.
```

v8 outcome: M3 produced 3 contract notes (1 propose + 2 respond).
First contracts in the entire arc. M5 reached `state=agreed` on 2.

## v9: the surprise collapse

Same code, fresh run, M1 produced stories but **no ADR**. Cat
went silent after a couple of clarifying questions. M2 still
decomposed (Rabbit engages on stories), but M3 collapsed: 2 LLM
calls, both Tweedles returned silence. They saw the
engagement-state annotation showing zero ADRs in team artifacts
and decided "no architectural anchor to draft against."

Cascade: Cat misses ADR → Tweedles can't anchor → contracts
don't ship → M4/M5 starve. The whole arc depends on Cat
shipping in M1.

## The diagnosis: Cat's STORY filter

`cheshire_cat.py:119` (pre-v10):

```python
selectively(SpeechAct.STORY, condition=architectural_primitive_in_story)
```

Where `architectural_primitive_in_story` matched body text against
a closed keyword set: `real-time, multi-tenant, offline,
cross-language`. Stories about user roles ("polyglot moderator,"
"deaf captioning user," "GDPR trustworthy data handling") didn't
trip the filter. Cat literally never received them as engagement
candidates — the rule filtered before deliberation.

The design intent was reasonable: Cat shouldn't wake on every UX
story; he's not the storyteller. But the side effect was
structural: **Cat could never synthesize an ADR across the
cumulative story picture** — only respond to a single story
containing one of four magic words, or to a concern/question with
architectural smell. When Alice's stories happened to use one of
the magic words (v8: "cross-language" appeared), Cat shipped.
When they didn't (v7, v9), Cat stayed silent and the arc died.

This isn't Cat being Cat — it's Cat being keyword-deaf. A real
Cheshire would read the cumulative picture: "you've described
four kinds of users with four different trust surfaces and three
data flows; the seam is X." That synthesis is exactly what was
unavailable.

## v10: the fix

Two coupled changes:

**Engagement rule** (`cheshire_cat.py:119`):

```python
# Wake on every Alice story; deliberate() decides whether the
# cumulative picture warrants synthesis.
selectively(SpeechAct.STORY, condition=speaker_is("alice"))
```

Cat now sees every Alice story. The `architectural_primitive_in_story`
helper is deleted entirely.

**Protocol guidance** (added to Cat's protocol after the
"don't ship redundant ADRs" paragraph):

```
**Synthesize across the cumulative story picture.** You receive every
Alice story, not just the ones with architectural keywords in the
body. A single user story rarely warrants an ADR — it's one user
flow, one slice of need. But when several stories accumulate (the
engagement state's `story×N` count for the thread tells you N), the
collective shape is itself architectural information. Multiple user
roles, multiple data flows, multiple trust surfaces — they imply
seams the team will have to pick. If the engagement state shows
`team artifacts: story×3` (or more) and `adr×0` on this thread,
the cumulative picture has been deferred and the team will drift
into implementation without an architectural anchor. That is a
load-bearing moment for you: read the stories together, name the
seam(s) they collectively imply, and ship a provisional ADR.
```

The split:
- **Filter** says "you should look" (every Alice story)
- **Engagement state** gives factual counts (`story×N, adr×0`)
- **Protocol** says "when you should ship" (cumulative threshold)

This is the same shape the Cat-shipping calibration (analysis 013)
already used: protocol that cites factual counts in the engagement
state. The keyword filter was the holdout; this brings STORY
engagement into the same paradigm.

## v10 outcome

Single run, ~$1.04 / $3.00 budget, 109 LLM calls.

**Per-meeting:**

| Meeting | Outcome | New artifacts | Cost |
|---|---|---|---|
| M1 | COMPLETE | 4 stories, 1 ADR, 3 rulings | ~$0.10 |
| M2 | COMPLETE | 6 tickets, 1 more ADR | ~$0.10 |
| M3 | MEETING_BUDGET | 16 contract notes, 1 implementation, 1 ADR refinement | ~$0.78 |
| M4 | COMPLETE | (contract-refinement only) | ~$0.05 |
| M5 | MEETING_BUDGET | 2 more rulings | ~$0.01 |

**On disk:**

```
stories/         4 files
architecture/    3 ADRs (data residency, hub-vs-mesh, mesh commitment)
tickets/         6 files
rulings/         5 files (Queen invited into M4, shipped 2 more)
contract-notes/  2 (state=agreed)
implementations/ 1 declaration
```

**What's missing:** zero source files on disk. The Tweedle in M3
shipped an `implementation` decision with metadata
("Polyglot message list with per-language translation rendering
[side=frontend]") but didn't call `write_file` to materialize the
source. The implementation registry got the artifact; the project
root got nothing.

## Why three ADRs is right

v10 produced more ADRs than prior runs — two in M1/M2 + one
refinement in M3. Worth checking this isn't over-shipping:

- **ADR-001** (M1): Translation processing location and data
  residency model under GDPR. Synthesized from Queen's GDPR
  concerns + the cross-language stories.
- **ADR-002** (M2): Translation service: bilingual hub vs polyglot
  mesh. Surfaced by the cumulative ticket picture in M2 — Rabbit's
  decomposition revealed the routing question.
- **ADR-003** (M3): Translation service architecture: commit to
  polyglot mesh model. Closes the open tradeoff in ADR-002 after
  M2's tickets implied the mesh path. This is a *follow-on
  commitment*, not a duplicate.

Three ADRs covering three distinct architectural decisions, each
cited by name in downstream contract notes and tickets. Cat
isn't over-shipping; he's keeping pace with the architectural
clarification as it develops.

## Other agents that engaged differently in v10

**Queen of Hearts**: 7 calls, 5 rulings shipped. She got invited
into M4 (Tweedle invitation, post-pair-shipped, allowed by the
new INVITE constraint) and shipped 2 additional encryption-scope
rulings during implementation — exactly the load-bearing
compliance ruling pattern her constitution names.

**Rabbit**: 3 calls, 6 tickets. With both the ADR-derived
architectural prerequisites and the story-derived user flows
visible, his decomposition was richer than v8's (8 tickets) only
because v10's stories were tighter; the *quality* improved
(every ticket has a clear source).

**Tweedles**: 47 (Tweedledum) + 42 (Tweedledee) calls.
Combined, almost half the run's call volume. They negotiated 16
contract-note operations across M3, reached `state=agreed` on
both contracts, and surfaced their own loop-detection (M4
tweedledum concern: "001 and 002 are already locked on disk").
The remaining gap is the implementation→`write_file` connection.

## What this run validates about the framework thesis

Three observations:

**1. Identity is load-bearing across meetings.** Cat being deaf
to user stories isn't a calibration bug fixable with prompt
tweaks — it's a structural property of his engagement rules.
Once corrected, the synthesis behavior emerges naturally from
the constitution + engagement state + protocol coupling. The
fix isn't "tell Cat to ship more"; it's "let Cat see the picture."

**2. Engagement state replaces keyword detection.** The previous
keyword filter pattern (`body_contains_any` for architectural
words) was an attempt to make Cat selective without giving him
the full team picture. The engagement-state annotation (added in
the v6→v7 transition, lifted from Tweedle to base agent) gives
every agent factual artifact counts. Once that exists,
keyword-filter conditions become unnecessary in most places —
the deliberate() step has the data to choose well.

**3. Failure modes propagate cleanly between agents.** v9
demonstrated a pure cascade: Cat silent → Tweedles silent →
Caterpillar silent. Each link respected its constitution
(Tweedles correctly declined to draft without an architectural
anchor; Caterpillar correctly declined to review nothing). The
cascade isn't a bug — it's the framework refusing to fabricate
work. Identifying which constitution-faithful behavior is the
critical-path bottleneck is the calibration task.

## What's next

The implementation→`write_file` gap. The Tweedle ships an
`implementation` decision with `implementations` payload; the
registry persists it; the LLM never reaches for `write_file` in
the same turn. Hypotheses to test:

1. The protocol doesn't make the implementation→write_file
   connection explicit — the LLM treats the artifact metadata as
   the deliverable.
2. The tools section is loaded but the `implementations` payload
   shape competes with `write_file` calls in the LLM's attention.
3. Tools-on Tweedles spend too many turns refining contracts (the
   M4 transcript showed both still doing contract-note work
   despite the convenor directive); a stronger
   negotiation→implementation transition signal is needed.

The natural next experiment is a focused single-meeting
implementation showcase (analysis 015's pattern) but with the
v10 contract notes as seed — does the Tweedle ship code when
contracts are unambiguously in scope and there's no negotiation
distraction? If yes, the gap is the M3→M4 transition; if no,
it's the implementation protocol itself.

## Files touched in this arc

```
src/wonderland/agent.py                       # engagement-state annotation
src/wonderland/agents/cheshire_cat.py         # STORY filter + synthesis protocol + adr=None validator
src/wonderland/agents/tweedles.py             # sibling-question rule + INVITE constraint
src/wonderland/primer.py                      # §IX Context as Breath
src/wonderland/runner.py                      # convene timestamp restamp
tests/test_cheshire_cat.py                    # STORY engagement test rewritten
tests/test_two_agent.py                       # ADR fixture for proposal validator
```

The bundle is one commit: every change here is part of the same
"make M1 produce a synthesizable architectural picture so M3 can
draft contracts so M4 can ship code" arc, and the v10 evidence
shows they compose.

---

## Followup: the implementation→write_file gap, diagnosed and fixed

After v10 shipped every artifact except actual source files, four
focused single-meeting diagnostics located the substrate cause and
fixed it. The fix was one flag and four places that respect it.

**v1 diagnostic** — structured CONTRACT_NOTE seeds (taken from v10's
on-disk artifacts) handed to Tweedles + Dodo, tools-on, with a
convenor directive saying "ship code, don't refine contracts." The
Tweedles ignored the directive entirely and went straight into
contract-respond mode: tweedledum proposed a new contract; tweedledee
INVITE'd Cat (which the new INVITE constraint allowed because the
pair had now shipped a contract); Cat answered Socratically; pair
looped on contract refinement indefinitely. Five contract_notes
shipped, zero implementation artifacts, zero files on disk.

**v2 diagnostic** — same setup, but seeds re-shaped as Cat PROPOSAL
prose (no structured contract_note artifacts). Tweedles got engaged
on the proposals but the engagement-state annotation showed zero
team artifacts (because prose seeds carry no artifact metadata).
With nothing to anchor against, both Tweedles returned silence
(5 LLM calls, $0.016, 30s to quiescence).

**The diagnosis.** The framework was treating seeded utterances and
fresh turns as the same kind of thing. v1 failed because seeded
contract_notes triggered the same engagement rules as live sibling
contract_notes. v2 failed because prose seeds didn't expose the
artifact counts the engagement state needs. Neither extreme gave
the agent the right picture: "the work that came before is
context, not negotiation surface; act on it."

**The fix:** add `is_seed: bool = False` to `Utterance`. Convene's
re-stamp sets it to True. Three places respect it:

1. `EngagementRules.categorize` short-circuits to ALMOST_NEVER for
   seeds. They remain visible in thread history and prompts; they
   just don't trigger fresh-turn engagement.
2. `_build_engagement_state` splits fresh vs seeded artifact
   counts. Output now reads:
   ```
   your prior turns on this thread: 0
   your artifacts shipped on this thread: none
   team artifacts shipped on this thread: none
   context from prior threads (seeded): contract_note×2, adr×2
   ```
   The agent can see "we already have these contracts" without
   thinking they're current-thread work needing response.
3. Existing engagement-state-driven shipping rules in protocols
   still cite the same field names; they just see the seeded
   counts in the new line, and the cumulative-synthesis logic
   continues to fire when needed.

**The second gap, surfaced by v3.** With `is_seed` filtering in
place, v3 produced zero LLM calls — the Tweedles correctly ignored
the seeds, but the Dodo convenor directive ALSO landed without
engagement. Cat, Alice, and Rabbit all have `always(DIRECTIVE)`
in their engagement rules; Tweedles didn't. In meetings without
those agents on roster (implementation-only meetings), the
directive was the only meeting-frame signal available, and nobody
was listening. Added `always(SpeechAct.DIRECTIVE)` to
`_tweedle_rules`.

**v4 result** — same structured CONTRACT_NOTE seed, both fixes
in place:

```
src/frontend/hooks/useTranslationStatus.ts (3168 bytes)
src/frontend/hooks/useUserLanguagePreference.ts (2341 bytes)
src/models/__init__.py (307 bytes)
src/models/enums.py (1307 bytes)
src/models/message.py (7614 bytes)
```

**14.7KB of contract-aware code shipped in 30 seconds for $0.10**.
Both Tweedles cited CN-001 and CN-002 by name in their docstrings.
Backend Python + frontend TypeScript both materialized.

The Tweedles chose `decision=silence` for their bus output (so no
`implementation` artifact metadata got declared), but the actual
work — the deliverable — landed on disk via the tools loop. This
exposes a design question worth resolving before the next full
arc: the implementation-artifact metadata duplicates information
that already exists in the working tree. A `git_status` /
`git_diff` tool surface for the Caterpillar would let the working
tree be the artifact directly. That's the next move.

## Files touched in the followup

```
src/wonderland/utterance.py             # is_seed field
src/wonderland/runner.py                # convene sets is_seed=True
src/wonderland/engagement.py            # categorize short-circuit
src/wonderland/agent.py                 # engagement-state splits fresh/seeded
src/wonderland/agents/tweedles.py       # always(DIRECTIVE) rule
tests/test_engagement.py                # seed short-circuit test
tests/test_tweedles.py                  # DIRECTIVE engagement assertion
```

The diagnostic transcripts (v1-v4 of `/tmp/test_t36_implementation*.py`)
are not committed — the substrate change in this followup makes
them obsolete. The full enchilada re-run after `git_status`/
`git_diff` tools land will produce the next analysis.
