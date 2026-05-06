## Story 007: Legitimate office worker discovers they are rate-limited during credential-stuffing attack originating from adjacent network segment

**Persona:** Jordan, 28, software engineer at a mid-size tech company. 200+ people on the corporate network share an egress IP for security scanning and bulk operations. Today, an attacker targets the service from the same IP range.

**Situation:**

Jordan is mid-sprint, reviewing code, when they realize their session timed out. They refresh and attempt to log in to check a production metric. The /login endpoint rejects them with 'too many attempts from your IP.' They have no idea anyone else on the network was attacking anything. They think their credential is compromised.

**Need:**

As Jordan, I want to know *why* I'm locked out and be able to regain access without waiting 30 minutes or calling support, so that I can resume work without panic or friction.

**Acceptance:**
- Error message tells Jordan the lockout is due to IP-level rate-limiting, not account-level lockout
- Error message suggests either 'wait 30 min' or 'use a different network' or 'contact support' as explicit paths forward
- Jordan can use mobile hotspot or home network to log in from a different IP without hitting the shared-IP rate limit
- If Jordan does call support, they get a fast track: 'shared IP detected, account is secure, rate limit will lift in X minutes'

**Tier:** core

**Confusion-flags:**
- The rate-limit is an attack defense, but it hurts the people it's supposed to protect. This feels like a false recovery.
- If we're locking out entire office networks, how many legitimate users does one attack take offline? Is that acceptable risk or a bug in the defense itself?
- The 30-minute window is arbitrary. How did we pick it? Does it matter to Jordan?
