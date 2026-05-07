## Story 006: Understand how long the app has been tracking sessions

**Persona:** Marcus (same engineer as story 1), six months into using the app. Marcus wonders: when did I start using this? How long have I been tracking?

**Situation:**

Marcus opens the All-Time stats and wants context. Seeing '2,000 sessions' means nothing without knowing whether that's over 3 months or 3 years.

**Need:**

As Marcus, I want to see the date I first used the app, so that I can understand the time horizon of my all-time statistics.

**Acceptance:**
- The All-Time stats section shows 'Sessions tracked since: [date]' (e.g., 'Sessions tracked since: March 12, 2024')
- If data exists from before the app was installed (e.g., imported), the earliest date is shown

**Tier:** enrichment

**Confusion-flags:**
- This feels like a small detail, but for people who care about trends, context is crucial. I'm flagging it as enrichment rather than core because the app works fine without it — but it improves the experience for long-term users.
