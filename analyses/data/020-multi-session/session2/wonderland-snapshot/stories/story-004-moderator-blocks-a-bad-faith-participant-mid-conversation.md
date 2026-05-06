## Story 004: Moderator blocks a bad-faith participant mid-conversation

**Persona:** Maya, 34, polyglot community moderator. She runs a cross-language tech discussion group. A participant started good-faith, then escalated to hostility in a thread with three other members.

**Situation:**

Maya is mid-conversation with Klaus, Yuki, and a fourth person (David). David's messages started collegial, then became hostile. Maya does not want to see David's messages, and she does not want David to see hers. The conversation has a 2-hour history.

**Need:**

As Maya, I want to block David so that I stop seeing his messages and he cannot see my future messages, without disrupting my ongoing conversation with Klaus and Yuki.

**Acceptance:**
- Maya can issue a block action on David from the conversation UI (not a settings page — she's in the thread where she needs to act)
- After blocking, the conversation view shows the conversation history without David's messages (they are hidden, not deleted)
- David's future messages to this conversation do not arrive for Maya
- David cannot see Maya's messages sent after the block (messages sent before the block are visible to David — the block does not retroactively erase history)
- Klaus and Yuki continue to see the full conversation with both Maya and David, unless they also block David independently

**Tier:** core

**Confusion-flags:**
- The conversation object itself—does it split? Does David see a different version of the conversation than Maya? Or does David still see the conversation but his view excludes Maya's messages? These are different blocking models and the story doesn't specify which.
- Timing: when Maya blocks David, do David's messages-in-flight (sent but not yet received) still arrive to Maya? Or does the block apply retroactively to pending translations?
- UI: where does the block action live? Is it a button next to David's message, or a menu on the conversation header? The acceptance criteria don't specify and the UX depends on this.
