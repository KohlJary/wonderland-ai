## Story 004: Legitimate user on shared IP discovers they are collateral-locked during attack

**Persona:** Marcus, 42, senior engineer at a mid-size fintech firm. His office building shares a Class-C subnet with a startup in the same complex. He's mid-workday, needing to pull up his account to verify a transaction for a client.

**Situation:**

Marcus tries to log in from his office desk during the credential-stuffing attack. The attacker's traffic originates from a different /24 within the same Class-C, but rate-limiting keyed on Class-B catches both. His login fails. He has done nothing wrong; the system has mistaken his legitimate attempt for part of an attack.

**Need:**

As Marcus, I want to know immediately that this is a temporary system-wide issue (not my credentials failing), and I want a clear path to regain access within minutes — either through a support channel that doesn't require the system I'm locked out of, or through a challenge that proves I own the account.

**Acceptance:**
- Error message explicitly states 'too many login attempts from your IP' (not 'invalid credentials'), differentiating this from auth failure
- User is offered a frictionless unlock path (SMS challenge to phone on file, security question, or support escalation with <2min response time)
- If user chooses SMS challenge, they receive it and can unlock within 30 seconds
- If user contacts support, they do not need to be in the account system to prove they own it (phone number, email, identity verification questions)

**Tier:** core

**Confusion-flags:**
- How do we prevent rate-limit false-positives from crushing legitimate users in shared-IP environments? Simple IP-based rate-limiting is crude. We may need to layer IP + User-Agent + request pattern, but that gets complex fast.
- The unlock path is a secondary system (SMS provider, support queue) that could also be attacked. Does the Queen's ruling account for DDoS-ing the unlock path itself?
- If we rate-limit too aggressively to catch the attack, Marcus can't work. If we rate-limit too loosely, the attacker wins. The tension feels real and I'm not sure where the balance lands.
