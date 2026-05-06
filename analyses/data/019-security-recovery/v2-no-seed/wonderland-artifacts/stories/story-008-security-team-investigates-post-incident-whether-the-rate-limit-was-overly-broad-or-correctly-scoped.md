## Story 008: Security team investigates post-incident whether the rate-limit was overly broad or correctly scoped

**Persona:** Morgan, 35, on the incident response team. When attacks happen, Morgan's job is triage: was the defense effective, did it cause collateral damage, should we keep it or refine it?

**Situation:**

The credential-stuffing attack is halted. 47 accounts were locked out. But the rate-limit also rejected login attempts from multiple office networks and an ISP-assigned IP range that legitimately shares the attacker's /24. Morgan needs to know: was this necessary collateral damage, or is the rate-limit too blunt?

**Need:**

As Morgan, I want clear telemetry showing how many legitimate users hit the rate-limit, what IP ranges they came from, and whether there's a tighter scoping (geography, AS path, risk signals) that would stop the attack while sparing office networks, so that I can propose a refined defense for the next incident.

**Acceptance:**
- Telemetry shows count of legitimate logins rejected by rate-limit (by IP range, geography, or other signal)
- We have evidence of which IP ranges hosted both attack attempts and legitimate users
- Analysis identifies whether a tighter scoping strategy would have stopped the attack without collateral damage
- If tighter scoping is possible, the Hatter's monitoring tickets include a scenario for detecting it

**Tier:** core

**Confusion-flags:**
- We're defending against an attack by blocking office networks. That's not a defense, that's shifting the damage from attacker to defenders.
- How do we know the rate-limit didn't cause someone to miss a critical production incident because they couldn't log in?
- This feels like the kind of incident where our defense teaches the attacker something — next time they'll use a residential proxy or a botnet with distributed IPs. Did we just kick the problem downstream?
