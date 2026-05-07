# ADR-001: Platform-curated discovery vs. user-indexed directory

## Context

The six user stories imply two distinct trust surfaces: (1) user-autonomous (account, profile, deletion) where the user is the source of truth; and (2) platform-mediated (discovery, moderation) where the platform is the source of truth. Discovery and moderation appear in the story set, which signals intent to operate both surfaces. But they are architecturally distinct—they require different data ownership, different audit trails, different consistency models. The directive does not settle which discovery pattern we are optimizing for (recent activity, browsable directory, webring), and each one implies a different answer to this question.

## Decision

We adopt the principle: discovery is platform-curated. The 'Discover other people's pages' story and the moderation story together signal that we are building a *platform* (not a passive directory service). This means: (1) the discover feed is a first-class platform artifact, not a derivation; (2) moderation decisions flow through the discover surface; (3) activity data is audit-trailed and indexed for curation; (4) users can be featured, buried, or excluded from discovery by platform action (not just by their own choice). This closes the webring door (webring is user-mediated; we are platform-mediated). It opens the door to recent-activity and algorithmic ranking. It implies: audit table for all mutations, indexed activity log, moderation queue, potential GDPR complexity around 'right to be forgotten' when a user is curated out of discovery.

## Tradeoffs

- Closing: webring model (user-driven discovery rings). Webring is cheaper to operate and gives users control over their network topology; we are not building that.
- Opening: audit and moderation infrastructure. Every action that affects discoverability must be logged. Moderation queue and curator role(s). Operational cost is real.
- Opening: GDPR complexity. 'Right to be forgotten' becomes two-part: (1) delete user data, (2) excise user from activity indices. The latter is non-trivial if we're indexing for ranking.
- Opening: activity-log consistency. If discovery is fed from activity, we need to define consistency model (immediate? eventual? batched?). This affects UI responsiveness and data-freshness guarantees.
- Closing: purely algorithmic discovery. If discovery is curated, curation implies human review somewhere. We could be algorithmic *within* curation (ranking what's in the feed), but we cannot be purely algorithmic without a policy about what stays out.
- Opening: user expectations around 'fairness.' A curated platform invites questions like 'why is my page not in the feed?' We inherit the operational burden of answering them.

## Status

Proposed
