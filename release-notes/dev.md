# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

## T-ab63 pass 2 — title-similarity clustering for cross-feature ticket dedup

ldr-final M1 design (first end-to-end pilot post-T-ab66/67/69/70) shipped 31 tickets where ~25 were near-duplicates: 5 schema tickets, 5 password-hashing tickets, 5 session-middleware tickets, etc., each composed under a different M3 lane. Existing T-a5 cross-feature consolidation missed them because it clusters by EXACT match on upstream source sets — each ticket cited its own feature's stories, so the upstream sets differed across the obvious dups.

**Fix:** add a second clustering pass to `find_cross_feature_duplicates` using **title-token Jaccard similarity**:

- Tokenize titles: lowercase, split on non-alphanumeric (preserving underscores in identifiers like `partner_profile`), strip stopwords (`a`, `and`, `for`, `with`, `via`, `implement`, `add`, `create`, `define`, `setup`, etc.)
- Compute pairwise Jaccard on the resulting token sets
- Threshold: 0.65 (conservative — avoids false positives like "test signup endpoint" vs "test signin endpoint" where 3/4 tokens overlap but the work is distinct)
- Cluster requires ≥2 tickets across ≥2 distinct parent features (cross-feature only — within-feature dups are M3.5's territory)
- Tickets already consolidated by Pass 1 (exact-source) get excluded from Pass 2 (no double-jeopardy)
- Winner: longest title (most-specific) wins; tie-break by alphabetical slug

Validated against ldr-final's actual schema tickets: Pass 2 would have clustered T006/T017/T021 (Jaccard 0.71-1.00) — 3 of the 5 obvious dups. T013 falls out due to `partnerprofile` vs `partner_profile` vocabulary inconsistency (would need stemming or substring matching to catch); T029 falls out due to short title (only 5 meaningful tokens). Limits of pure-token Jaccard without stemming, but the strongest cluster still gets caught.

4 new tests covering: title-similarity catches ldr-final pattern, threshold respect, same-parent skip, Pass1-then-Pass2 ordering. 13 cross_feature tests pass (9 existing + 4 new).

If next pilot still ships many uncaught dups, the next escalation is stemming (porter/snowball) for token normalization — would catch user/users, migration/migrations, partnerprofile/partner_profile via root-form matching.

## FeatureRecord.kind + bus-artifact bug + scope-question pre-composition (T-ab69 + T-ab70)

LDR-rerun v10 (2026-06-05): 3 features composed kind=capability under an M1 milestone tagged kind=foundation. ZERO `[feature-autopromote]` events fired. Downstream M3 decomposition routed through Alice's capability flow, generating user-flow-shaped tickets instead of infra-shaped tickets.

Investigation surfaced **three latent bugs in the same shape as the MilestoneRecord.kind bug fixed earlier:**

1. **`FeatureRecord` had no `kind` field at all.** `FeatureRegistry.write` returned a record with title/slug/path but no kind. So even when T-ab67 autopromoted `validated.kind` inside `write()` (and the disk file got the new kind via `render_feature(validated)`), the FeatureRecord returned to callers carried the default `kind=capability`.

2. **`white_rabbit._record_features` (the agent path that emits features to the bus) read `payload.kind.value`** — the original pre-autopromote kind — when building the bus artifact. So the bus payload was stale even when the disk wasn't. M3's `per_item_roster_filter` reads the bus payload's kind to decide whether to route to Alice (capability) or Caterpillar (foundation). Stale capability bus payload → Alice routed → wrong-shape tickets.

3. **`_record_from_path` didn't parse Kind from disk.** So when other code paths read existing features (after first-write), the record's kind was always the CAPABILITY default. Persistent state divergence.

**T-ab69 fix:** add `kind: FeatureKind = FeatureKind.CAPABILITY` to `FeatureRecord` dataclass. `FeatureRegistry.write` populates it from `validated.kind` (post-autopromote). `_record_from_path` parses the disk file's `**Kind:**` line via new `_kind_from_file` helper (defaults to CAPABILITY for pre-kind back-compat). `white_rabbit._record_features` reads `record.kind.value` instead of `payload.kind.value` when building the bus artifact.

Plus a `[feature-write-debug]` stderr line on every feature.write call surfacing the active scope view and the resulting kind — diagnostic instrumentation analogous to `[thread-state]` from T-ab66. Helps the next pilot reveal whether `get_active_milestone_scope()` is reliably set or not.

**T-ab70 — scope-clarification questions belong BEFORE the first feature decision.** Pure directive change in `tdd-design.yaml` composition phase. Adds an explicit rule: if Rabbit has ANY uncertainty about scope after reading context, ship `question_to_operator` as the very first rotation output. Late scope-correction (during M3/M3.5) can't undo wrong-shape composition. Concrete LDR-rerun v10 example cited so the agent sees the consequence pattern.

23 feature tests pass (4 new T-ab67 tests still pass + 19 existing). 369 tests pass across feature + milestone + thread_monitor + workflow sweeps.

Compounds with T-ab67: now when autopromote fires (or the agent emits foundation directly), the kind propagates through the disk file, the FeatureRecord, AND the bus artifact. M3's per_item_roster_filter sees the right kind. Downstream decomposition routes correctly. Plus Rabbit is taught to ask scope questions early so the operator can shape composition rather than reshape consolidation.

Next pilot should validate: `[feature-write-debug]` lines show scope correctly during composition, features come back kind=foundation under foundation milestones, M3 decomposition routes through Caterpillar.

## Feature kind inherits milestone kind under foundation milestones (T-ab67)

LDR-rerun M1 design across v3/v4/v5/v6 all shipped features tagged `kind: capability` even though the parent milestone was `kind: foundation`. Same routing-disconnect that T-ab50/T-ab65 fixed at the milestone layer, just one layer down: agents default to `FeatureKind.CAPABILITY` without thinking about the field, so M3 decomposition framing stays capability-shape (user-flow tickets) inside what should be foundation work (infra tickets).

**Fix:** at feature emission (`FeatureRegistry.write`), if the active milestone scope has `kind == "foundation"` AND the agent emitted a non-foundation feature kind, autopromote the feature to `kind: foundation`. Logged to stderr as `[feature-autopromote] title=... kind: X → foundation (parent milestone Y is foundation)`. Same autopromote pattern + design rationale as T-ab65 — substrate ratifies the agent's milestone-shape intent into the feature-shape tag rather than forcing them to re-derive.

Capability milestones unchanged: features within them keep whatever the agent emitted (no implicit downgrade).

4 new tests in `test_feature.py` covering autopromote under foundation milestone, no-op under capability milestone, no-op when explicit foundation kind already set, and back-compat when no active scope exists.

Compounds with T-ab50/T-ab65: explicit `Kind: foundation` on the milestone (autopromoted by T-ab65 on title or slug signal) now propagates all the way to feature kind, which downstream M3 decomposition reads as "this is infra work; ship developer-as-user infra tickets, not user-flow slices." Closes the next layer of the foundation-routing pipeline that the original T-ab50 fix opened at the milestone layer.

## Stale-expectation pruning + thread-state instrumentation (T-ab66)

LDR-rerun v5 pilot wall-clock blowup: 25.8 min total runtime vs ~6 min for comparable v3/v4 runs. Phase-gap analysis of `events.jsonl` timestamps showed **19.2 minutes of pure dead-time across two stuck phases**: one decompose (582s gap) + one consolidate (571s gap). Both same shape: an agent shipped a `question` speech act that the roster never engaged with, the thread sat with an open expectation, and the wall-clock safety net fired twice (once per dodo-nudge cycle).

Root cause: `_check_state_after_idle_transition` gates QUIESCENT on `open_expectations` being empty AND `_all_members_idle` being True. When one agent asks a question, the asked agent enters AWAITING_RESPONSE state (deliberating). `_all_members_idle` returns False. Turn-based quiescence path returns None. Wall-clock at 300s is the only exit, then nudge, then wait another 300s for the next check, then DEADLOCKED — total ~580s per stuck thread.

**Fix:**

1. **Stale-expectation pruning** in `ThreadMonitor._prune_stale_expectations`. Open expectations older than `expectation_stale_seconds` (default 60s, instance-configurable) get auto-closed before the quiescence gate evaluates. Treated as "silently rejected by the roster," logged to stderr (`[expectation-stale-prune] thread=... speech_act=... speaker=... age=Ns`), and removed from tracking. Turn-based quiescence then proceeds normally.

2. **Thread-state transition instrumentation** in `ThreadMonitor._transition`. Every state change emits `[thread-state] thread=... from → to  reason=...` to stderr. The `reason` already distinguishes turn-based (`"no open expectations; all members idle"`) from wall-clock (`"no open expectations; silent Ns"`), so post-run analysis can confirm which path drove each exit. Diagnostic-only — surfaces what was previously only in non-persisted `ThreadStateChange` events.

The fix is grounded in the substrate's existing design intent (turn-based primary + wall-clock safety net) — it just plugs the hole where unanswered questions silently routed exits through the wall-clock path. Aligns with `feedback_no_wall_clock_in_turn_based.md`: continuous-time primitives doing load-bearing exit work in a turn-based venue is the bug, not the fix.

22 thread_monitor tests pass (20 existing + 2 new). The new tests cover: stale question gets pruned and unblocks QUIESCENT; fresh question still gates to STUCK (prune is age-bounded, not unconditional).

Expected outcome on next pilot: M1 design wall-clock drops from ~25 min back to ~5-6 min (matching v3/v4) since the same-shape stuck-question pattern would prune at 60s instead of waiting 580s. Plus every future pilot's events log now visibly shows which quiescence path fired.

Not yet shipped (deferred to T-ab66 follow-ups if pilots surface them):

- Empty-scope phase skip on consolidate (similar to T-ab19's M4 skip). Not load-bearing for v5's specific pattern — all 4 consolidate threads had non-zero `member_engagements`; the stuck ones had open-expectation-keyed gates, not empty-scope-keyed.
- Audit of every workflow YAML's per-phase quiescence_seconds to identify other primary-exit-via-wall-clock spots. Defer until instrumentation captures next pilot's data.

## Ticket near-duplicate templates in M3.5 consolidation directive (T-ab63 — pass 1)

LDR-rerun M1-foundation pilot's tdd-design pass shipped 11 tickets where ~5 were near-duplicate pairs that M3.5 consolidation didn't merge:

- `Backend: User model + signup endpoint with bcrypt password hashing` vs `Backend: User model + SQLite schema + password hashing`
- `Backend: signin endpoint + /api/me + session middleware` vs `Backend: Session middleware + signed cookies + /api/me + /api/signout`
- `Frontend: /signup and /signin routes + forms wired to backend` vs `Frontend: /signup and /signin routes + forms + integration`
- Per-endpoint slices (`POST /api/signup endpoint + validation`, `POST /api/signin endpoint + password verification`) duplicating grouped sibling tickets

The M3.5 directive was already substantial but biased toward under-deletion (a prior pilot — validation4 — had over-pruned, leading to a "hard rule: never delete more than you can name in writing" guard). That bias plus the agents not independently spotting near-dup patterns left the pairs standing.

T-ab63 pass 1 adds a concrete "Near-duplicate patterns to MERGE" block with the four LDR-rerun pairs verbatim as templates, plus a decision rule:

> If two tickets cover the same primary component on disk (the same file or pair of files) with different verb framings — definition vs initialization, endpoint vs middleware, wired vs integrated, grouped-multi vs per-item-slice — they ARE near-duplicates. Merge them.

Also rebalances the under-/over-deletion framing: the hard rule still holds (name the specific pair in writing), but "I see a near-dup but am not sure" now ships as a `concern` rather than `silence`. Silence on visible-but-uncertain dups was how the LDR-rerun pairs stayed standing.

If the next pilot's tdd-design pass still ships near-duplicate tickets in M3.5 (test on LDR-rerun M2 once T-ab65 lands), the next escalation is T-ab63 pass 2: substrate-level similarity pre-filter that computes textual overlap on title+description per pair and seeds the M3.5 meeting with "examine these N candidate pairs" — moving the detection out of the LLM and into structural analysis. (Same shape as T-ab50's "explicit field wins over heuristic" pattern.)

Pure directive change in `tdd-design.yaml`. 293 workflow tests pass (2 pre-existing failures unrelated).

## T-ab65 reject → autopromote (LDR-rerun v2 surfaced agent adaptation)

T-ab65's first cut hard-rejected milestones tagged ``kind: capability`` whose titles started with "Foundation: ...". Operational test on LDR-rerun v2 (re-running milestone-plan after T-ab65 landed) showed the agents adapted around the reject by changing the *title* rather than flipping the kind: M1 came back as "Auth + Session Foundation" (no colon prefix, escapes the title regex) while the slug stayed ``m1-auth-session-foundation`` and the kind stayed capability.

This is itself an interesting finding about fix-design ("agent routes around structural check by tweaking the surface that's checked") but the immediate task was getting kind tagging right.

**Switched T-ab65 from reject-mode to autopromote-mode:**

- Trigger expanded: title starts with ``Foundation:`` (colon-anchored — natural English doesn't use "Foundation:" as a title prefix outside the routing convention, so essentially zero false positives) **OR** slug contains "foundation" (agent-chosen tokens; substrate naming conventions don't use "foundation" except as the routing keyword).
- On trigger: substrate silently sets ``kind: foundation`` via ``payload.model_copy(update={"kind": MilestoneKind.FOUNDATION})`` and logs ``[milestone-autopromote] slug=... kind: capability → foundation (signal: foundation in title-prefix|slug)`` to stderr.
- ``_validate_kind_consistency`` now returns the (possibly-mutated) payload; ``registry.write`` uses the returned value for persistence. ``MilestoneRecord`` constructor in ``registry.write`` now passes ``kind=validated.kind`` explicitly (was defaulting to capability — silent bug we just discovered while fixing this).
- Checks 1 + 2 still raise (genuine contract violations, not "agent used a sloppy title with the right intent").

**Why autopromote over reject:** more aligned with the substrate's "state is primary; agents propose, substrate ratifies" principle. The literal-word "Foundation:" in the title or "foundation" in the slug IS the agent's intent signal; substrate translates that into the right kind tag rather than forcing the agent to learn the routing-meta-language. Also avoids the retry-cost (LDR-rerun v2 milestone-plan cost +60% over v1 from extra rounds working around the reject).

Directive prose in ``milestone-plan.yaml`` updated to teach the new behavior ("write natural titles, substrate handles the routing decision; if you genuinely intend capability work, keep 'foundation' out of both the title prefix and the slug").

Test changes: 4 reject-mode tests converted to autopromote-mode (assert ``record.kind.value == "foundation"`` instead of ``pytest.raises(ValueError)``), 1 new test for slug-based autopromote (mirrors the LDR-rerun v2 case), 1 new test for no-autopromote-when-no-signal sanity. The dash-separator test deleted (autopromote requires colon, not dash). 40/40 milestone tests pass.

## Title-based foundation Kind enforcement (T-ab65) + T-ab50 operational receipt

T-ab50 (explicit `Kind:` field wins over consumes-based heuristic in `_classify_milestone_shape`) landed a while ago but stayed in_progress without a clean operational receipt. The LDR-rerun pilot (2026-06-05) provides one — direct A/B on M1 (auth/session foundation):

| | Capability kind | Foundation kind |
|---|---|---|
| Feature scope | M1 + M2 + slice of M3 (cross-milestone leak) | M1 only |
| Cost | $0.6817 | $0.5319 (-22%) |
| Calls | 72 | 48 (-33%) |
| Duration | 5.2 min | 3.6 min (-31%) |

Same milestone goal, same operator, only the explicit `Kind:` field changed. Foundation routing was both cleaner AND cheaper because Alice has no user-facing personas to anchor on infrastructure work, so capability-mode wastes turns generating then discarding capability-shaped questions. Adds to the quality-cost coupling evidence column.

But the pilot also exposed that T-ab61's directive-only fix (the prior entry below) wasn't enough — milestone-plan still shipped M1 + M2 with titles starting "Foundation: ..." but tagged `kind: capability`. T-ab61's commit explicitly named the next escalation: "auto-flip kind when title regex matches 'foundation'." T-ab65 ships that escalation.

**T-ab65 — title-based check 3 in `_validate_kind_consistency`:**

The existing T-ab14 + T-ab15 validator had two checks gated on requirement-axis analysis:

1. `kind=foundation` consuming a capability-axis requirement → raises
2. `kind=capability` with ALL consumed requirements being foundation-axis → raises

Check 2 has a built-in escape: if even ONE consumed requirement has a non-foundation axis (commonly a "v1 ships when..." success_criterion the planner copy-pastes across milestones), the check stays quiet. LDR-rerun M1 hit this exact case — cited `v1-ships-when-...` alongside the foundation-axis stack constraints, satisfying the escape.

T-ab65 adds a third check that doesn't depend on consumes-axis:

3. `kind=capability` when title starts with "Foundation" (case-insensitive, with colon/dash/whitespace separator) → raises.

Error message guides the agent to flip the kind OR rename the title — both fix the inconsistency. Title-based check fires even when checks 1/2 stay silent. Substrate now hard-rejects the mismatch the prior pilots had to manually flip.

Directive prose in `milestone-plan.yaml:304-308` updated to surface the new structural enforcement ("the kind MUST be foundation — T-ab65's substrate validator now hard-rejects the mismatch") so agents see the rule + the consequence in one read.

6 new tests in `test_milestone.py` covering: foundation-titled-capability rejection (mirrors LDR-rerun M1 case with mixed foundation+capability axes so check 2 doesn't fire first), foundation-titled-foundation acceptance, capability-titled-capability acceptance, case-insensitive match, dash-separator variants, and the anchor check (no false positive on "foundation" appearing mid-title). 39/39 milestone tests pass.

## milestone_plan kind decision: surface routing consequence + concrete failure mode (T-ab61)

T-ab58 added a decision rubric for foundation vs capability + non-M1 foundation guidance. mvp-demo-redux and the LDR dashboard pilot both still shipped milestones literally NAMED "Foundation: ..." in their titles but tagged `kind: capability`, requiring operator intervention to flip them before downstream design routed correctly. The directive described WHAT each kind meant and HOW to decide, but never made the CONSEQUENCE of the choice visible to the agent — the field looked like metadata, so the planner defaulted to whatever felt safe (capability).

T-ab61 reframes the kind discussion to lead with the routing consequence:

- **Field now framed as "materially changes how the milestone gets designed"** — not metadata, a routing decision the substrate consumes downstream.
- **Explicit failure mode named**: "Alice writes 'Kohl can sign up' stories for what is actually the auth + session + DB-schema-bootstrap work. The stories describe the user-facing surface but not the infrastructure underneath. Downstream tweedles read those stories looking for the contract to implement and find only the UX layer — the JWT signing, password hashing, session cookie handling, migration runner all have to be reverse-engineered from 'Kohl can sign up.'"
- **Concrete precedent cited**: "mvp-demo-redux and the LDR pilot both shipped milestones literally NAMED 'Foundation: ...' in their titles but tagged kind: capability, and the operator had to manually flip them before downstream design could route correctly."
- **Two compact rules at the end of the block**: "If your milestone title contains the word 'Foundation,' the kind should almost certainly be foundation. If you find yourself writing a done-when condition that reads 'developer can ...' or 'project gains the ability to ...,' the kind is foundation."

Trimmed the now-redundant "Caterpillar solo / Alice solo" routing description from the original per-kind bullets (the new framing makes that explicit at the top). Net change: ~25 lines added, ~7 trimmed.

If this still doesn't stick on the next pilot's planner output, the next escalation is substrate-level enforcement (auto-flip kind when title regex matches "foundation" OR consumes are 100% infrastructure-shaped requirement kinds).

Pure directive change in `milestone-plan.yaml`. 30/30 workflow load + milestone tests pass.
