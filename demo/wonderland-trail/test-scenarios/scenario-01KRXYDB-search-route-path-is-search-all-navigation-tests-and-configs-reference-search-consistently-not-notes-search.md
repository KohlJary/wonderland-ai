## Scenario 188: Search route path is /search; all navigation, tests, and configs reference /search consistently (not /notes/search)

**GUID:** 01KRXYDBED29B1DN9NNN3336YM
**Severity:** degradation

**Setup:**

Ticket doesn't mandate route path (/search vs /notes/search). Implementation chooses and registers it.

**Trigger:**

Implementation creates route and navigation links throughout codebase.

**Expected:**

All useNavigate calls, <Link> components, route registration, and documentation use the same path consistently.

**Concern:**

If different parts of codebase use different paths (/search in navbar, /notes/search in router), or if there are typos, navigation will break. Consistency issue.

**Property:**

All references to search route must use the same URL path.

**Implies:**
- Implies: Route path should be chosen once and documented (contract note or README)
- Implies: Code review should check for path consistency
