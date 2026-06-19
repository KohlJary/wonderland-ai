# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

- **Milestone planning sizes by scope, not a fixed count.** The milestone-plan directive used to tell the planner to "target 3-7 milestones," which biased it toward over-bundling — on a content-heavy app it would cram auth + several entity types + media + draft/publish into one fat foundation milestone to hit the number, then the design phase's composition meeting would over-produce stories and starve on budget before shipping features. The directive now anchors on granularity (each milestone is one coherent, independently-shippable slice; split a fat foundation into auth / entity-substrate / relational-entity slices) and lets the count follow the work, with a soft ~3-12 sanity range instead of a hard target.
