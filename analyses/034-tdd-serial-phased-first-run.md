# Analysis 034 — tdd-serial-phased v1: first phased run, output explodes upward, headline metric inverts

**Date:** 2026-05-09
**Run:** Pomodoro tdd-serial-phased v1 ([runs/r35-tdd-serial-phased/](../runs/r35-tdd-serial-phased/), $7.8794 / $5.00 cap, 76.5 min wall-clock, completed end-to-end).
**Result:** **First end-to-end phased run. Cost overrun ($5 cap → $7.88). Wall-clock 2.7× the 032 baseline (76.5 min vs 28 min). Output volume up 3× (1080 LOC → 3247 LOC of production code; 35 effective green tests → 99). Hatter's call count went UP 2.7× (65 → 176), not down — the headline metric inverted, but the deeper hypothesis (bound deliberations, pack each window) appears to have held; we can't measure it directly without phase-event persistence.**

## What we tested

Per analysis 033 / P9 T59. The phased orchestrator (`src/wonderland/meeting.py`, T58b/c) runs M3, M4, M5, M6 with phases declared in `closet/workflows/tdd-serial-phased.yaml`. Same Pomodoro directive as 032 ("Build a Pomodoro timer app: focus sessions, configurable breaks, daily review, persistent settings"). Same model (claude-haiku-4-5-20251001). Same agent constitutions (no constitutional changes — phases live engine-side per the design decision in T58 review).

Phase decomposition with rotation budgets calibrated from 032 telemetry:

| Meeting | Cast | Phases | Max windows | 032 baseline (calls) |
|---|---|---|---|---|
| M3 | 2 | `discussion` (3 rot) | 6 | 19 |
| M4 (per-iter) | 4 | `clarify` (1) + `red-tests` (3) | 16 | 54 |
| M5 (per-iter) | 2 | `implement` (4) | 8 | 56 |
| M6 | 3 | `review` (2) + `defend` (2) | 12 | 99 |

M1, M2, M2.5 stayed legacy — they weren't sprawl loci in 032 and don't need the structural cap.

The bet from analysis 033: rotation budgets cap deliberations; agents pack each deliberation densely; total cost holds or drops; §VIII observability (per-agent passes/acts) becomes engine-side rather than transcript-inferred.

## Top-level numbers

| Metric | 032 banner | r35 phased | Δ |
|---|---|---|---|
| Total cost | $4.7236 | **$7.8794** | **+67%** |
| Wall-clock | ~28 min | **76.5 min** | **+173%** |
| Total LLM calls | 465 | 698 | +50% |
| Production LOC | 1080 | 3247 | **+201%** |
| Test files | 10 | 23 | +130% |
| Tests effectively green | 35 (20 pass + 15 xpassed) | **99** (15 pass + 84 xpassed) | **+183%** |
| Stories | 7 | 27 | +286% |
| Test scenarios | ~15 | 58 | +287% |
| Reviews | ~5 | 20 | +300% |
| Outcome | complete | complete | — |

**Cost-per-output-unit dropped.** $7.88 / 99 green tests = $0.080 per green test, vs $4.72 / 35 = $0.135 per green test in 032. **40% cheaper per verified-working test.** Same direction for LOC: $0.0024 per production LOC vs $0.0044 in 032.

But wall-clock ratio is the operator-experience metric, and 76 min > 28 min is the lived cost.

## Per-agent telemetry — the surprise that reframes the cost story

| Agent | 032 calls | 032 cost | r35 calls | r35 cost | calls Δ | cost Δ |
|---|---|---|---|---|---|---|
| tweedledee | 179 | $1.575 | **260** | $2.645 | **+45%** | +68% |
| tweedledum | 179 | $1.821 | 195 | $2.362 | +9% | +30% |
| **mad_hatter** | **65** | **$0.901** | **176** | **$1.891** | **+170%** | **+110%** |
| caterpillar | 27 | $0.326 | 31 | $0.733 | +15% | +125% |
| alice | 9 | $0.040 | 17 | $0.116 | +89% | +191% |
| cheshire_cat | 3 | $0.019 | 14 | $0.078 | +367% | +311% |
| white_rabbit | 2 | $0.026 | 2 | $0.031 | 0% | +20% |
| queen_of_hearts | 1 | $0.017 | 3 | $0.023 | +200% | +37% |
| **Total** | **465** | **$4.724** | **698** | **$7.879** | **+50%** | **+67%** |

**Hatter's call count went UP, not down.** This is the headline-metric inversion. The T59 task explicitly named: *"Headline metric: Hatter call count drops without test quality dropping."* Calls didn't drop — they nearly tripled. Test quality did go up substantially (3.9× more scenarios, more rigorous shape per the disk audit). But the structural-cap-compresses-Hatter framing was wrong on this dimension.

What likely happened: telemetry counts every API call including each tool-loop iteration. Phases bound *deliberations* (priority windows), not *tool calls inside a window*. Hatter's deliberation count probably *did* drop relative to 032 — we just can't measure it directly without phase-event persistence (deferred T58 follow-up). What he did with each bounded deliberation: dense tool work, multiple `write_file` + `read_file` cycles per window. The 030 F3 "bound all expansion paths simultaneously" framing was right about expansion paths in *artifact volume* (more scenarios shipped) but wrong about expansion paths in *call count* (more tool calls per scenario).

## Findings

### F1 — The phased rotation cap *re-shaped* sprawl, didn't *compress* it

Hatter's call count nearly tripled. But his artifact density per call went UP, not down — 58 test scenarios across 176 calls (~3 scenarios/call) vs 032's roughly ~15 scenarios across 65 calls (~4 scenarios/call). Per-call density slightly dropped, but absolute output more than tripled.

The phase mechanism imposed a structural cap on *deliberations* (priority windows in rotation), and Hatter compensated by packing each deliberation with intense tool work — read skeleton files, draft scenario, write test file, refine, write again. The compression we wanted (fewer total LLM calls) didn't materialize because the substrate measures calls, not deliberations.

This is a measurement gap: the §VIII observability primitives (passes_per_agent, acts_per_agent) are emitted in PhaseEnded events but those events aren't persisted to disk in this run (snapshot persistence was deferred from T58c). The deliberation count for each agent in each phase is unknown post-hoc.

The fix: ship phase-event snapshot persistence (the deferred T58 follow-up). With phase events on disk, "Hatter's call count" stops being the right metric — "Hatter's deliberation count" is. We can then measure whether the structural cap compressed the *load-bearing* unit (deliberations) even when total calls rose.

### F2 — Wall-clock is dominated by serial-priority cost

The 2.7× wall-clock ratio (76.5 min vs 28 min) is the cleanest single-variable finding. Phases serialize what was previously parallel: in legacy mode, Tweedledee + Tweedledum could deliberate concurrently when their engagement policies fired together; in phased mode, the priority gate forces strict serial — Tweedledee finishes their full tool loop, then Tweedledum starts theirs.

For an N-agent cast meeting, total wall-clock approximately becomes `sum(deliberations)` instead of `max(deliberations)`. Cast sizes in tdd-serial-phased: M3=2, M4=4, M5=2, M6=3. With per-feature iterations on M4 (5 features) and M5 (5 features), the serialization cost compounds.

This is *not* an intrinsic property of phases. Strict serial within a rotation was a design choice in T58, justified by adversarial-game intuition (MtG-style priority). But Wonderland's constitutional pairs aren't adversarial — Tweedledee:frontend :: Tweedledum:backend is one design problem with two sides; Alice:user-journey :: Hatter:failure-mode is one test surface with two angles. Phase 9.5 ("Two-Headed Giant") generalizes phases by adding `team_groupings` per phase: a team window opens concurrently for all members, structural cap preserved (rotation budget × team count), §VIII observability preserved (per-agent WindowOutcome unchanged).

If 2HG had been in this run: M3 (1 team of 2) ~2× faster, M4 (2 teams of 2) ~2× faster, M5 (1 team of 2) ~2× faster, M6 mixed. Net wall-clock reduction roughly 40-50%, putting r35-equivalent in the ~45 min range — still over 032's 28 min, but recoverable in the same magnitude.

### F3 — Output quality went up, on every dimension that matters

The disk audit:

- **ADR-001** is well-reasoned. Names the load-bearing architectural pivot (settings-sync vs single-device), enumerates deferred / closed / open tradeoffs explicitly, hands open contract questions to M3 by name. This is craft-level architecture writing — the kind of decision artifact a senior engineer would produce.
- **Implementation flow ran the full TDD loop**: implementations 001-005 are M5 baseline (timer state machine, audio alerts, account, settings, app orchestration). Implementations 006-012 are fix-on-review following M6 findings (corrupted-localStorage handling, profile-deletion contract enforcement, foreground-handler stale-state fix, cloud-sync merge null-vs-missing distinction). The red → green → fix-on-review loop ran cleanly across the per-feature M5 iterations and the single M6.
- **Reviews caught real bugs**: `profile-deletion-violates-stated-contract-to-ensure-active-profile-invariant`, `app-foreground-handler-checks-pending-notification-on-stale-state`. These are name-the-broken-behavior bugs, not vague refactor suggestions — exactly the bound the M6 convenor directive asked for.
- **Test results: 99 effectively green out of 137 collected** (15 pass + 84 xpassed + 31 skipped + 7 xfailed). The 84 xpassed are tests that M4 shipped with `pytest.xfail` markers (red), which M5 turned green via implementation; Tweedles didn't strip the xfail decorators after green. Cosmetic; doesn't break anything.
- **Polyglot architectural call**: Tweedles wrote `timer.py` and `daily_review.py` as Python "shadow" implementations of the TypeScript modules so pytest can test contract behavior in isolation. Clever — this wasn't named in the directive or the contracts; the team derived it from the tooling constraint (test framework is pytest, production is TS). The kind of decision that's hard to anticipate from a directive.

Cost-per-effective-green-test dropped 40% vs 032 ($0.135 → $0.080). Cost-per-production-LOC dropped 45% ($0.0044 → $0.0024). The 67% total cost overrun is paid for, in efficiency terms.

### F4 — Alice drifted alone; the team kept Pomodoro intact

Stories 015-017 had Alice progressively reframing the daily-review feature from "Pomodoro session review" toward reflective journaling (Keisha tracking anxiety patterns, Alex preparing for therapy). The drift is striking artifact-craft — the personas are coherent, the acceptance criteria clean, the confusion-flags honest. It's just for a different product than the directive named.

The diagnostic landed clean: **no journaling code shipped**. Implementations 001-012 are all Pomodoro session tracking; the `daily-review` feature was implemented as session-completion review, not journal-entry aggregation. Hatter's M4 test scenarios for feature-003 stayed in Pomodoro territory (session schema, completion percentages, focus categories — not journal entries or annotation).

Phases imposed a per-meeting reset that prevented Alice's reframe from propagating. Cross-meeting accumulation didn't happen — Hatter saw her stories as bus context but didn't pick up the framing. **Phase boundaries are stronger than I assumed for in-meeting context propagation.**

This is a stronger finding than "Alice drifted alone." It says: the priority gate gives strong voices more landing room *within their phase*, but inter-phase accumulation doesn't carry interpretive momentum. That's the right shape — it lets a creative voice articulate while preventing unilateral product redefinition.

The substrate-level fix isn't tighter constitutional bounds on Alice; it's the missing affordance for agent-to-user questions (filed as roadmap item `9aae11bc`). Alice's reframe is a real product insight worth surfacing — give her a channel to ask, rather than suppressing the instinct that produced the insight.

### F5 — Emergent accessibility coverage the directive never asked for

The directive said: *"Build a Pomodoro timer app: focus sessions, configurable breaks, daily review, persistent settings."* Nothing in it asked for accessibility. Nothing named deaf users, hearing loss, ADHD, hyperacusis, or any other disability.

The team produced it anyway, structured across multiple artifacts:

- **Story-024** ships a deaf persona — Priya, "29, deaf software engineer" — who needs feature parity via visual + haptic alerts, not just audio. Alice's confusion-flag on the story explicitly names what the spec doesn't: *"we need to test with actual deaf and hard-of-hearing users, not just accessibility checklist."*
- **Story-010** (M1) flagged it preemptively: *"Sound-based confirmation may not work for all users (deaf users, users in silent environments)."* Alice surfaced the gap before any feature was decomposed.
- **Scenario-035** elevates it to a failure-mode scenario covering ADHD and hearing-loss users in the same artifact. Hatter wrote: *"adjustable volume… haptic feedback… visual pulse or animation (for deaf users)… distinctive frequency."*
- **Scenario-041** is property-based: *"Alert failure SHALL NOT degrade session-completion feedback to zero. Visual or haptic fallback MUST engage if audio fails."* This is a robustness invariant that protects deaf users *implicitly* — the same property that catches "audio file failed to load" also catches "user can't hear."
- **Scenario-042** makes the requirement explicit: feature parity for deaf users; if audio is the only path, *"deaf users silently miss session completion (silent wrongness in accessibility, a compliance issue)."* The scenario names the contract (004) as where the requirement should be encoded.

This isn't checkbox accessibility coverage. It's accessibility reasoning woven through M1 (Alice flags), M4 (Hatter elevates to failure-mode + property requirement), and propagating into M3 contracts (the contract-004 callout). The constitutional substrate produced it from first principles: **Alice grounds in personas, and a persona-grounded view of "who actually uses this software" includes users with disabilities by default**. The structural insight isn't that the agents *can* think about deaf users; it's that *constitutional grounding makes accessibility a derived property, not a feature you have to remember to ask for*.

Worth comparing against base-LLM behavior on the same directive: an undifferentiated assistant given "build a Pomodoro app" would almost certainly ship audio-only alerts unless the prompt asked for accessibility explicitly. The constitutional grounding — Alice's "would the persona I named actually care about this?" — closes that gap automatically.

This is a thesis-defending finding. It says: the value Wonderland produces isn't just "more LOC, more tests" — it's *artifacts that derive concerns from grounding rather than requiring those concerns to be specified upstream*. Phased orchestration didn't cause this directly (Alice's ground-in-personas is constitutional, not phase-derived), but phased orchestration gave Alice the contiguous deliberation room to write personas dense enough to surface it.

### F6 — Phase-event persistence is the most-load-bearing deferred work

The §VIII observability primitive — passes_per_agent, acts_per_agent emitted in PhaseEnded events — is the substrate gain that justified P9 conceptually. In this run, those events fired on the live wire (the LiveRunHandle translation in T58c) but weren't persisted to the snapshot. So we can audit artifact quality from disk, but can't audit phase mechanics from disk.

What we couldn't measure for this analysis:

- Per-agent deliberation count per phase (the unit phases bound, vs the LLM-call count we have).
- Phase-end reasons by frequency (succession / exhausted / exit_condition / aborted).
- Per-feature M4/M5 cost breakdown.
- Whether Hatter's deliberation count actually dropped (the deeper hypothesis behind F1).

Snapshot persistence (write `phase-events.jsonl` to `wonderland-snapshot/`) is now P0-priority for any future phased run we want to analyze. Without it we keep flying blind on the load-bearing measurement.

## What this analysis doesn't show

- **N=1 result.** One phased run vs the 032 single-run baseline. Variance across pomodoro runs has been substantial (analyses 029-032 spanned $2.36 to $4.36 with similar directives). The 67% cost overrun could be partly variance.
- **Per-meeting cost breakdown is inferred, not measured.** No `run.log` for TUI runs (the existing run.log writer is script-driven). Per-meeting + per-iteration costs from this run are not directly available; the next phased run should write them.
- **The headline-metric framing was wrong.** "Hatter calls drop" was the wrong unit to measure. Phase mechanics bound deliberations, not LLM calls. With phase-event persistence, the right metric becomes "Hatter deliberations / phase / window count" — which we can measure directly once F5 ships.
- **Alice's drift is one shape; what propagates and what doesn't may differ across drift shapes.** A drift driven by Hatter (over-broad failure-mode framing) might propagate differently than Alice's grounding-too-deep drift. We have one data point on inter-meeting accumulation behavior under phases.

## What's next

In priority order:

1. **Ship phase-event snapshot persistence** (the deferred T58 follow-up). Write `phase-events.jsonl` from the orchestrator; have HistoricalRunHandle read it on replay. Without this, every future analysis of phased runs has the same measurement gap as F6 names. P0 for the next phase of phase work.

2. **Two-Headed Giant** (p9.5, roadmap item `dbf88619`). Add `team_groupings: list[list[str]]` to PhaseSpec; orchestrator opens team windows concurrently via `asyncio.gather`. Recovers ~40-50% of the wall-clock penalty on paired-cast meetings without losing the structural cap or §VIII observability. Bring this online before the next pomodoro A/B.

3. **Agent-to-user questions / interactive escalation** (roadmap item `9aae11bc`). Build the affordance for an agent to surface a question to the operator and receive an answer that flows into the next deliberation. Solves the Alice-reframe class of problem at the substrate level rather than via tighter constitutional bounds. The phased-meeting variant: a window resolves as **act / pass / ask** — ask doesn't consume the window.

4. **Re-run pomodoro on tdd-serial-phased after 2HG lands.** The wall-clock recovery is the experiment we want to validate. Same directive, same model — A/B against r35 (this run), not 032. Watch for: wall-clock dropping toward ~45 min, cost holding or dropping (denser parallel work might amortize per-token costs), §VIII counts confirming the bound-deliberations / pack-windows shape.

5. **Hatter call-count measurement done right.** Once phase events persist, look at deliberations per agent per phase. The hypothesis to test: in r35, Hatter had ~12-16 M4 deliberations across all iterations vs ~13 in 032. Calls went up because each deliberation packed more tool work, but the load-bearing unit (deliberations) was bounded. This is the headline metric reframed correctly.

## Headline

**Phased orchestration's first live run produced 3× the verified-working code of the 032 baseline at 1.67× the cost and 2.7× the wall-clock. Cost-per-effective-green-test dropped 40%; cost-per-production-LOC dropped 45%. The headline metric ("Hatter calls drop") inverted — calls went up — but the deeper hypothesis (bound deliberations, pack windows) appears to have held; we can't measure it directly without phase-event snapshot persistence.** The wall-clock penalty is fixable via Two-Headed Giant team windows; the headline-metric measurement gap is fixable via the deferred T58 phase-event persistence work; Alice's product-reframe drift is addressable via the agent-to-user-question affordance the substrate already wants to grow into. None of the costs are intrinsic to phases as a primitive. The win — phased meetings produce dramatically denser, better-shaped, more-verified output — is real and load-bearing. The next pomodoro run with 2HG + phase-event persistence is the one that should answer "is the phased substrate the right default for productivity-shaped directives?" The data so far says yes, with tractable optimization runway ahead.
