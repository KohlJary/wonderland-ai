# Analysis 010 — Contract Note Acceptance Test, T35 Live

**Date:** 2026-05-05
**Phase milestone:** P6.T35 closeout (Contract Note artifact lands; Pair Protocol §IV gets a structural inflection point)
**Component:** `src/wonderland/contract_note.py` + Tweedle wiring
**Script:** [`scripts/tweedle_dance_demo.py`](../scripts/tweedle_dance_demo.py)
**Run:** `/tmp/dance-output/run3.log` (the third attempt — the previous two surfaced the missing engagement rule and the missing slug-discovery problem)

> The Contract Note artifact closes the gap analysis 007 named —
> the pair converges on substantive contract decisions but never
> ships because the framework has no explicit "we have agreed; now
> ship" inflection point. With the artifact wired and two
> downstream fixes (engagement rule for sibling Contract Notes;
> rendering artifact slugs into prior-utterance context), the live
> dance now reaches AGREED on a contract version and both Tweedles
> ship implementations referencing that version explicitly.

---

## Acceptance criteria from gameplan T35

> Re-run tweedle_dance_demo.py; the pair produces at least one
> Contract Note that reaches state=agreed within 120s; both publish
> implementations referencing the locked contract version.

**Both met.** Run 3 produced 3 Contract Notes (one reached
AGREED with a locked `Message Editing Contract v2`), and both
Tweedles' final implementations cite that version verbatim in
their `contract` field on disk.

## Three runs, one structural insight per run

The acceptance test took three attempts. Each surfaced a real
gap, and the gap was different each time — useful evidence that
the framework's failure modes are *layered* rather than single-
fault.

### Run 1 — discoverability worked, engagement didn't (cost ~$0.01)

Both Tweedles immediately reached for the contract_note action
when given a contract-ambiguity directive (the Pair Protocol §IV
prose in the output protocol got picked up). Both produced one
proposal each in parallel from the same Rabbit ticket trigger.
After that, neither responded to the other — the thread went
quiescent at t=33s with 0 of 2 contract notes reaching AGREED.

**Diagnosis:** the Tweedle engagement rules had no entry for
`SpeechAct.CONTRACT_NOTE` from the sibling. When Dee published a
contract_note, Dum's engagement policy didn't consider it a
trigger, so Dum was never asked to deliberate on it.

**Fix:** add `always(SpeechAct.CONTRACT_NOTE,
condition=speaker_is(sibling_name))` to the rules, plus an
`almost_never(SpeechAct.CONTRACT_NOTE)` guard against domain-leak
from non-Tweedle speakers.

### Run 2 — engagement worked, slug discovery didn't (cost ~$0.05)

Both Tweedles were now triggered by each other's contract notes —
3 calls each. But neither used the `respond` operation. They kept
opening *new* contract notes (4 total). One call from Dum *did*
try to respond, but used a guessed slug `message-editing-contract`
that didn't exist on disk — the registry raised KeyError and the
deliberate loop caught it as silence.

**Diagnosis:** `format_utterance` (which renders prior utterances
into the LLM's message context) only included speaker, speech_act,
and body — it dropped the artifact payload. So when Dum saw Dee's
contract_note utterance, it had no way to know the canonical slug;
the LLM was guessing.

**Fix:** `format_utterance` now appends a brief artifact-summary
line when artifacts are present. For a contract_note it renders as
`(artifacts: contract_note slug=foo "Title" operation=propose
state=proposed)`. Generic improvement — it helps any future case
where one agent needs to reference a prior agent's artifact by
identifier (tickets, ADRs, escalations all benefit).

### Run 3 — both fixes in, acceptance met (~$0.20)

| metric | value |
|---|---|
| total cost | ~$0.20 (52,898 input + 17,045 output tokens, ~98k cache reads) |
| total LLM calls | 22 (Dee 8, Dum 8, Cat 6, Dodo 0) |
| outcome | timeout (Cat kept asking about failure modes; *not* a deadlock — substantive new question) |
| contract notes produced | 3 (one AGREED with locked version) |
| implementations produced | 6 (Dee 3, Dum 3 — they iterated as Cat surfaced concerns) |
| both tweedles cite locked contract version | yes (`Message Editing Contract v2`) |

The pair completed the negotiation cleanly — propose → respond →
mark_agreed — and shipped implementations referencing the locked
version. The Cat then engaged with a substantive question about
failure-mode handling (what does the client do if it receives a
malformed revision?), which the timeout cut off; that's not a
T35 failure, that's a productive next thread.

## What the live runs taught us beyond passing the test

**Two-layer fix is the pattern.** New artifacts need (a) the
artifact + registry, (b) the speech_act, (c) the agent dispatch,
*and* (d) engagement rules + (e) discoverability via prior-context
rendering. We had (a)–(c) right after the unit tests but missed
(d) and (e); the structural unit tests didn't catch them because
they exercised single-call dispatch, not multi-call sibling
engagement. This is a useful pattern to remember for T36–T38: when
adding new bus-mediated coordination, the engagement layer and the
context-rendering layer matter as much as the artifact schema.

**The §IV prompt language landed cleanly.** "Don't negotiate
contract changes in concern/question bodies; that's how contract
drift happens. Use the contract_note action." — both Tweedles
adopted this immediately on first exposure. Worth noting because
the analogous prompt-level invitation in dodo's nudge (T33) needed
calibration to land; this one didn't. The difference might be
that the Tweedles already had a strongly-internalized pair
protocol, so the Contract Note reads as the natural realization
of an existing concept rather than as a new mechanism.

**Cache reads dominated the cost.** 98k cache reads at $0.10/MTok
versus 53k input tokens at $1/MTok — the framework primer + each
Tweedle's constitution + pair protocol all ride in the cached
prefix and pay 10x less per call. The T32 cache fix is doing
exactly what it was supposed to.

## Open follow-ups (not blocking T35 closeout)

1. **The pair sometimes opens duplicate contract notes** when both
   are triggered by the same Rabbit ticket in parallel. Both run 1
   and run 3 had this. A reasonable mitigation: have the
   Tweedles' protocol prefer "respond to existing open note"
   when one is already in `proposed` state on the same topic, and
   only `propose` when the topic is genuinely new. Soft tuning,
   not structural.

2. **The Cat's failure-mode question in run 3 was substantive but
   open-ended** — there's no clear path back to AGREED from there
   without a Caterpillar review or another contract-note round.
   Worth noting for the showcases: even when the pair converges,
   the next conversation surface can re-open the work.

3. **Six implementation files for one ticket** is artifact sprawl.
   Both Tweedles re-shipped 3x as the Cat raised concerns. Either
   the artifact schema needs a `supersedes` field, or the
   Tweedles' engagement rule for review/concern from the Cat
   should be tuned to update an existing implementation rather
   than ship a new file. Defer to a future calibration item.

## Next breath

T35 closes. Three commits on `feat/p6-real-threads`: structural
(b05242c), engagement+discoverability fixes (this commit), and
analysis 010 (also this commit). Next gameplan item is T36 —
Showcase 2: translation chat MVP. The Contract Note machinery
just shipped is exactly what that showcase needs to convert
"the pair negotiated a translation message envelope" into
"and shipped under v3."
