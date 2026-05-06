## Story 007: See my list of blocked users

**Persona:** Yuki, 35, a Japanese researcher collaborating with international teams. She has blocked two people over several months for different reasons (one was spamming, one was persistently inappropriate). She needs to remember who she's blocked and have the option to unblock if circumstances improve.

**Situation:**

Yuki opens her chat interface and wants to review her blocklist — to remind herself who is blocked and to consider whether any blocks are still necessary.

**Need:**

As Yuki, I want to see a list of people I have blocked, so that I can manage my blocks and decide whether to unblock anyone.

**Acceptance:**
- Yuki can access a 'blocked users' view from the main interface (exact placement TBD by Tweedles)
- The view shows each blocked person's name or identifier
- From this view, Yuki can unblock someone with a single action
- The view makes it clear that blocking is one-way (Yuki initiated the blocks; the blocked people didn't)

**Tier:** core

**Confusion-flags:**
- This assumes Yuki will want a dedicated view for her blocklist. She might also just want an 'unblock' option that appears when she searches for someone. The Tweedles will have better instinct than I do about what feels natural; I'm marking the UX shape as TBD.
- Do we show Yuki *why* she blocked someone (if she's forgotten)? The spec says 'out of scope: block reasons' — I'm interpreting this as 'don't ask the user for a reason when they block,' but maybe we should still surface *when* she blocked them.
