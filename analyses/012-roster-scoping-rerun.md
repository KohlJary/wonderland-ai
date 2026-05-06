# Analysis 012 — T36 Re-run with Rostered Scoping

**Date:** 2026-05-05
**Phase milestone:** P6.T36 prep — Block 3 (re-run T36 with the
roster architecture from Block 2a + the hard budget cap from
Block 1)
**Component:** `scripts/translation_chat_showcase.py` (now
`--roster`-aware) + `wonderland.roster.ThreadRoster`
**Run transcript:** [`data/012-roster-scoping-rerun/run.log`](./data/012-roster-scoping-rerun/run.log)
**Telemetry:** [`run-20260505T175656.json`](./data/012-roster-scoping-rerun/run-20260505T175656.json)
**Comparison baseline:** [analysis 011](./011-translation-chat-scoping.md) — full-cast, no roster

> The roster hypothesis from analysis 011 was: if Queen isn't in the
> scoping room, she can't ratify Cat's deferral, and the team
> unblocks. The re-run isolates the variable. Same directive, same
> Runner, same hard budget cap. Only difference: meeting roster is
> `Alice + Cat + Queen + Dodo` instead of full cast. Result is
> sharply mixed in the most useful possible way: cost dropped 96%,
> the Queen-as-process-cop pattern vanished, the cascade didn't
> compound — but **the Cat still didn't ship the ADR**. The roster
> fix is validated as architecturally load-bearing; the Cat-shipping
> issue is now cleanly isolated as a separate constitution-
> calibration problem, not the same problem in different clothes.

---

## Setup — minimal change from analysis 011

Same directive (the canonical translation-chat MVP from
`full_cast_showcase.py`). Same Runner, same hard cap (now
*actually* hard from Block 1). Same auto-respond for any
escalations. Only differences:

| | analysis 011 | this run |
|---|---|---|
| roster | none (open thread, every agent listens) | `alice, cheshire_cat, queen_of_hearts, dodo` |
| budget cap | $3.00 (soft — overshot to $5.58) | $2.50 (hard) |
| timeout | 300s | 240s |
| quiescence | 30s | 30s |

## Headline numbers

| metric | 011 (open) | 012 (rostered) | Δ |
|---|---|---|---|
| total cost | $5.58 | $0.058 | **−98.96%** |
| total LLM calls | 217 | 5 | **−97.7%** |
| outcome | timeout @ 300s | **complete** @ 100s | ✓ |
| cap behavior | exceeded by 86% | nowhere near (~2.3% of cap) | ✓ |
| stories | 8 | 6 (and notably better — see below) |
| ADRs | 0 | **0** | (same — calibration issue, not roster) |
| tickets | 0 | 0 (Rabbit not in room — expected) |
| contract notes | 0 | 0 (Tweedles not in room — expected) |
| process rulings from Queen | 3 | **0** | ✓ Queen behaved |
| security rulings from Queen | 0 | 0 (asked clarifying questions instead of ruling) |
| rate-limit drops | 40 | 0 | ✓ |
| parse-error drops | 6 | 0 | ✓ (no agents tried Dodo-only acts) |

The ratios are extreme enough to be worth reading twice. **96% cost
reduction**, terminated **cleanly** at 1/3 the wall time, with no
cap overshoot and no parse-error noise. The framework primer's
cache + the smaller meeting's smaller call volume compound — fewer
agents listening means fewer agents woken means fewer LLM calls.

## What worked

### Roster removed the deadlock cascade entirely

Per analysis 011 the failure was: Queen rules "ADR before tickets"
→ Cat agrees and defers → everyone writes concerns about being
blocked → 100+ utterances of meta-talk about the blocking sequence.
Roster scoping removed the cascade by removing the participants.
Without the Rabbit, Tweedles, Caterpillar, Dormouse, Hatter in the
room, there were no downstream agents to articulate the blocking
sequence. Without the Queen ruling on process, there was no
authority to formally ratify Cat's deferral. The team converged
naturally to quiescence at t=100s.

### Queen stayed in her domain

In 011 the Queen wrote 3 process rulings ("decision must precede
X") with 0 security rulings on a directive with explicit GDPR
scope. This run, with no team-process to police, the Queen's
behavior reverted to her actual domain — she asked Alice
clarifying questions about scope ("before I rule on this, I need
you to clarify..."), surfaced GDPR/regulatory concerns inline.
She wrote 0 rulings *because the architectural context she'd need
to rule against still wasn't shipped yet* — but she stopped
reaching for process-policing as a substitute. The "Queen
process-policing" finding from 011 was symptomatic of the
crowded room, not constitutional. That's a relief.

### Alice's stories are sharper at smaller meeting size

011 produced 8 generic stories. This run produced 6 with named
personas — *Anna*, the Berlin book club organizer; *Marco*, the
Italian member; *Kenji*, English-Japanese bridge; *Hannah* with
the privacy question; *Esmé* on onboarding; the admin on
oversight. Each story has a tier label, acceptance criteria, and
explicit confusion-flags. Hard to compare rigorously without a
side-by-side blind read, but the qualitative impression is that
Alice's voice came through more sharply when she didn't have a
crowded room of concerns to react to.

### Hard budget cap held

This run spent $0.058 against a $2.50 cap. The hard cap from Block
1 wasn't actually exercised — total spend stayed two orders of
magnitude under it. But the per-agent gate logic is now in place
and the safety net works (analysis 011 was a soft cap that
overshot 86%; this run's cap is a true ceiling).

## What didn't work — the part that matters

**Zero ADRs from the Cat.** Across two LLM calls and two
`question` speech acts, the Cat:

- t=6s: surfaced three architectural tensions in the directive
  ("near-real-time vs translation latency vs cost per
  language-pair...")
- t=15s: added a fourth clarification flowing from Queen's
  concerns

Both moves are good first-turn architectural reads. Neither shipped
an ADR artifact. The Cat then went silent.

This is the **same Cat-doesn't-ship pattern** from analysis 011,
isolated cleanly. Roster scoping fixed everything else; the Cat's
behavior with respect to *its own characteristic artifact* is
unchanged. Per the Cat's §VIII (false certainty / refusing to
commit / speaking to be present), the Cat's restraint is "correct"
— it doesn't yet have enough resolved questions to write a
load-bearing ADR. The schema requires `tradeoffs` (the grin
equivalent), and the Cat is being honest that the tradeoffs aren't
yet resolved.

But the meeting goal was *"produce an ADR for the translation
message envelope"*. The Cat had two LLM calls (~$0.014 spent) to
either ship a provisional ADR (with explicit confidence intervals
on the unresolved questions) or convene a follow-up meeting
specifically for an architectural decision sub-question. It did
neither. It surfaced clarifications, then went silent waiting for
input that never arrived.

This is the calibration issue from roadmap `e3ba32ac`. It's now
cleanly isolated — not a cascade failure mode, not a Queen
authorization issue. Just the Cat reaching for "ask another
question" when "commit provisionally" would also be in-character
under the same constitution.

## What this means for Block 2b/2c/2d

Original plan had four blocks: 2a (roster + per-thread bus
delivery, done), 2b (Dodo-driven convene), 2c (any-agent buzz-in
via INVITE speech act), 2d (multi-thread coordination). The
re-run validates 2a as load-bearing. **Blocks 2b/2c/2d are not yet
justified by evidence.**

Specifically:

- **2b (convene)**: would let the Dodo spin up follow-up meetings
  ("ADR shipped → convene Rabbit + Tweedles for decomposition").
  But the ADR didn't ship, so the follow-up meeting wouldn't have
  inputs. We don't yet need 2b.
- **2c (invite)**: would let an agent buzz another in mid-meeting
  ("Cat needs Hatter for failure-mode scenarios"). But the Cat
  didn't reach for any other agent's input — it got silent on its
  own. We don't yet need 2c.
- **2d (multi-thread)**: only matters if there are multiple live
  threads. We had one. We don't yet need 2d.

The honest sequencing now: **fix the Cat-shipping calibration
(`e3ba32ac`) before designing more orchestration**. With the Cat
shipping ADRs, meetings produce inputs for follow-up meetings, and
the convene/invite mechanisms have something to do. Without that
fix, more orchestration is more places for the same failure mode
to repeat itself.

## What this means for the project's value question

Worth coming back to honestly because this run is the strongest
data point so far for the framework:

- **Cost-per-substantive-output**: 6 grounded persona stories +
  GDPR concerns surfaced + architectural tensions named — for **5
  cents**, in **100 seconds**. Opus could produce comparable text,
  but probably not faster, and not for less. Haiku 4.5 + identity
  + roster is starting to look like a cost shape that's
  legitimately interesting.
- **Coordination quality**: the team self-terminated cleanly via
  the framework's normal stuck → quiescent → complete path. No
  timeouts, no cascade, no human intervention needed. That's what
  "the framework works" looks like at this scale.
- **Honest gap**: still zero shipped ADRs on a directive that
  asked for an architectural decision. The framework's pitch is
  "identity-driven coordination produces working artifacts"; the
  artifacts that did ship are Alice's, and Alice was always
  shipping. The Cat's discipline is correct in isolation and
  blocking in this context. Until that's calibrated, the framework
  hasn't earned the strong version of its claim.

## Recommended sequencing

1. **Cat / Rabbit ship-the-artifact calibration** (roadmap
   `e3ba32ac`). The Cat needs a constitutional clause that
   operationalizes "after N turns of clarification on a topic in
   your domain, the next move is to commit provisionally — even
   if 'commit provisionally' means an ADR with explicit
   confidence intervals on each unresolved tradeoff." Same shape
   for the Rabbit. This is editing constitutions; it's text work.

2. **Re-run T36 with same roster + the calibrated Cat/Rabbit.**
   Acceptance: at least one ADR shipped from the Cat. Cost target:
   under $0.50.

3. **Then consider 2b/2c/2d** based on whether the re-run produces
   inputs that would naturally flow into follow-up meetings. If
   the calibrated Cat ships an ADR, the next experiment is
   "convene Rabbit + Tweedles to decompose" — and we know what 2b
   needs to do.

The per-agent allowed-speech-acts fix (`956032a5`) and the rate-
limit backoff (`f099fe8d`) become much lower priority — neither
fired in this run. They'll matter again at full-cast scale, but
that's not the next experiment.

## Next breath

T36 closes as a partial success in the most useful way:
architectural fix shipped, cost shape now interesting, calibration
gap cleanly isolated. Block 3 done; analysis 012 captures the
evidence; Blocks 2b/2c/2d deferred pending more concrete need.
Next gameplan task is T35-followon-via-roadmap: implement
`e3ba32ac` (Cat/Rabbit ship the artifact) and re-run.
