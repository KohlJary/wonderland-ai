# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

## Headline — Diagrams: a structural build-tracker (P21)

Wonderland now keeps a living map of what's **built** vs **pending**. Ophanic layout diagrams (UI component trees + DB schema) thread through the whole lifecycle — drawn at planning, linked to tickets at design, built against at implementation, and verified at review. The failure class where a component ships as a file but never gets wired into the running app is now structurally catchable.

### New

- **Diagram stack at planning.** `milestone_plan` lays the app's structure down as `.oph` diagrams — layer-separated (ui / db), with durable GUID-identified nodes that survive component renames. Viewable + navigable in the TUI.
- **Node ↔ ticket auto-linking.** Design links each diagram node to the ticket(s) that build it; the node climbs `unlinked → pending → in_progress → built` as work lands. The Diagrams pane reads as a live build-progress map. (Validated across three milestones; every link backed by feature-attached work.)
- **Cross-author diagram dedup.** When two agents draw the same surface under different names (Rabbit's `dashboard` vs Alice's `dashboard-page`), the substrate folds them by node-set containment — the ticket surface-signature dedup, one layer up. Dropped nodes are reported, never silently lost.
- **Build-against-contract.** Tweedles now get the milestone's diagrams at implement time + a directive to wire each component into its parent — not ship an orphaned file and call it green.
- **Wiring-diff review tool (`verify_wiring`).** Reverse-adapts the built React (which component renders/imports which) and diffs it against the intended diagram, reporting every node as `wired` / `orphaned` / `missing`. `orphaned` (built but never mounted) is the hollow-build catcher. Run by Caterpillar as the first step of M8 review; milestone-scoped so a review only sees its own surfaces.
- **TUI reorg.** New Structure / Diagrams tabbed view; Diagrams as a master-detail list (pick a diagram → see its `.oph` + per-node build status). Runs / Run-detail moved into drill-downs.

## Fixes

- **Agents stop going silent on big projects.** The frontend Tweedle that shipped placeholder UIs and Caterpillar's "gets quieter the further along you are" silence were the same bug: the tool loop ran reads and writes against one shared cap, so an agent reading deep through a dependency chain (or a growing file tree at review time) exhausted the cap on reads alone and returned nothing — which downstream reads as silence and auto-approves. Now reads and writes get **separate budgets**, so exploration can't starve the turns an agent needs to actually commit, and a convergence nudge + recovery call keep silence-on-exhaustion off the table.
- **Re-reading a file is free.** A per-loop read cache serves identical reads from memory and doesn't charge them against the read budget, so the budget tracks unique files touched rather than total read calls — the thing that grows with project size. Writing a file invalidates its cached read (plus directory/grep listings), so a re-read after a write never serves stale content.
- **Aborted tickets no longer pollute the implementation queue.** Design-time dedup culls a duplicate ticket by marking it `aborted`, but the lifecycle was reading `aborted` as live `in_progress` work — so freshly-designed features looked mid-implementation and got queued prematurely. `aborted` is now treated as dead everywhere: excluded from the feature-state rollup, never iterated for implementation, hidden from the feature tree.
- **Queued work survives stale citations.** A feature whose story citations went stale across design re-runs was being silently dropped from the implement lane — "no tickets to work" despite visibly-queued tickets. The phantom-citation filter now keeps any feature/ticket that has live (queued / in-progress) work, regardless of upstream citation health.
- **Sharper, real-data-calibrated node↔ticket matching.** DB-vocabulary synonyms (`UsersTable` matches a "schema / migrations" ticket); 4-char component nouns now match (Time / News cards); navigation-reference stripping ("…redirect to sign-in" doesn't count as building sign-in); orphan tickets (no feature parent) excluded so the tracker mirrors the feature tree.
- **Cross-milestone scope tightening.** Ticket reattribution (T-ab78) now gates on surface signature, so an M4 news-card ticket can't get fuzzy-matched into the M3 weather feature; the diagram seed and the wiring-diff are both milestone-scoped, so a milestone's design/review isn't buried in other milestones' surfaces.
- **Doc correctness.** Corrected a stale comment claiming M8 request-changes aborts tickets — it actually marks the originals done and synthesizes queued follow-up tickets from the findings, so nothing is stranded.
