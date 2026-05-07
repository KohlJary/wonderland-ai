## Contract Note 005: View homepage by username (public read endpoint)

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

no contract yet

**Proposed Change:**

GET /user/{username} (no auth required). Response: { username, rendered_html, updated_at } OR 404 if user doesn't exist. Username lookup is case-insensitive (or case-sensitive? **QUESTION for pair: should username lookup be case-insensitive?**). Rendered HTML is pre-sanitized. If user exists but has no homepage yet, return { username, rendered_html: null, updated_at: null } OR 404? **QUESTION: what's behavior for user with no homepage—404 or empty doc?**

**Source:** ticket-005: view-user-homepage-by-username-url

**Frontend Impact (Tweedledee):**

Frontend parses /{username} from URL, GETs /user/{username}, displays returned rendered_html if present. Handles 404 gracefully (show 'page not found' message). Meta tags for page title can use username. No auth needed. Need clarity on case-sensitivity and empty-homepage behavior—affects user-facing discoverability.

**Backend Impact (Tweedledum):** _pending_
