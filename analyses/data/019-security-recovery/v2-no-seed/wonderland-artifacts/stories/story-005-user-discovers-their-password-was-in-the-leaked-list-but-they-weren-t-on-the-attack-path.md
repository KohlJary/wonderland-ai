## Story 005: User discovers their password was in the leaked list but they weren't on the attack path

**Persona:** Yuki, 28, freelance translator, casual user of the platform. She hasn't logged in in three weeks. The credential-stuffing attack iterates through a leaked list that includes her email + password combination.

**Situation:**

Three weeks from now, Yuki gets a security notice email saying her account was targeted in a credential-stuffing attack. Her password is on the leaked list, but the attacker never tried her account (random chance; the list was long, the attack short). She's alarmed. She doesn't know if her account was compromised, what to do, or whether to trust the system.

**Need:**

As Yuki, I want clarity on what actually happened to my account, assurance that my data is safe, and a clear next action — whether that's changing my password, enabling 2FA, or monitoring for fraud.

**Acceptance:**
- Yuki receives a notification that her credentials appear in a known-leaked list, with the date and source of the breach clearly stated
- The notification explicitly states whether her account was targeted in the attack (attempted login) or only at risk (credentials in the list but not attempted)
- Yuki is offered a one-click password reset flow that doesn't require knowing her current password
- Yuki is strongly encouraged (but not forced) to enable 2FA, with a simple on-ramp
- The notification includes a 'learn more' link explaining what data was exposed in the original breach (if known)

**Tier:** core

**Confusion-flags:**
- We don't yet know the full scope of the leaked data that included Yuki's password. Does her email + password alone tell us what else was in that breach? The Queen's ruling on disclosure obligations is relevant here.
- How much detail do we give Yuki about the original breach vs. this attack? Too much detail invites panic; too little looks like a cover-up. The tone matters and I'm not sure where to land.
- Yuki is a casual user and may not know what 2FA is. Encouraging it requires explaining it in a way that doesn't feel like jargon or blame for not having done it earlier.
