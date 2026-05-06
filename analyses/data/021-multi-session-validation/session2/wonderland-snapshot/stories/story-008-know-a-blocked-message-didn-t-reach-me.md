## Story 008: Know a blocked message didn't reach me

**Persona:** Marco, 42, an Italian project manager using the chat to coordinate with English-speaking contractors across Europe. He's been blocked by someone he worked with briefly. He sends a message expecting a response and gets nothing back.

**Situation:**

Marco sends a message to someone and neither receives a delivery confirmation nor gets a response. He's confused about whether the person is online, ignoring him, or something else.

**Need:**

As Marco, I want to know whether my messages are reaching the other person or being blocked, so that I don't spend time waiting for a response that will never come.

**Acceptance:**
- When Marco sends a message to someone who has blocked him, he does not receive a 'delivered' signal (or receives an explicit 'message blocked' signal — UX TBD)
- Marco understands from the UI that his message did not reach the recipient

**Tier:** core

**Confusion-flags:**
- This is the flip side of Sarah's block: how does the blocked person experience it? Does Marco see 'message failed to send (reason: blocked)' or does his message just vanish? Does Marco find out he's blocked, or does he remain confused? The spec says 'out of scope: blocking notifications,' which I read as 'don't send a notification to Marco saying he's been blocked.' But it might mean 'don't tell Marco anything about being blocked in the UI either' — in which case his message just fails and he never knows why. I need the Tweedles and Queen to clarify this.
- The GDPR angle: is a 'blocked' state itself a piece of personal data that Europe's data subjects have the right to know about? Or is the blocking itself a privacy feature that should be opaque to the blocked person?
