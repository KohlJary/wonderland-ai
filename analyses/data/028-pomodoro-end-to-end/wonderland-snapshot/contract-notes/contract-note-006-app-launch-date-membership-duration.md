## Contract Note 006: App launch date & membership duration

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

N/A — proposing initial contract

**Proposed Change:**

User entity includes launch_date (UTC timestamp, set on first session creation, immutable). API endpoint /user returns {launch_date, days_tracked}. days_tracked = floor((now - launch_date) / 86400 seconds). Launch date is recorded once and never updated, even if user deletes all sessions.

**Source:** Feature 006 (tracking-since display); tickets 014-015

**Frontend Impact (Tweedledee):**

Client fetches /user on app launch and caches indefinitely. Launch date displayed on profile or stats dashboard as human-readable text: "Tracking for N days" or "Joined Jan 15, 2024". No client-side computation of days_tracked; use server value directly (avoids clock-skew issues and ensures consistency across clients).

Client state: {user: {launch_date, days_tracked}, userFetchedAt}. Cache is never invalidated in v1 (launch_date is immutable and days_tracked is recomputed on each /user fetch, so refreshing is sufficient if data feels stale).

UI states: loaded (displaying launch date / days tracked), loading (initial fetch on app boot), error-recoverable (fetch failed on boot, show placeholder + allow user to proceed). For error handling: if /user fails, we still allow app to function; membership-duration display is deferred until fetch succeeds.

Open questions for pair:
1. Is launch_date always the exact timestamp of first session creation, or is it normalized to midnight of the day the first session was created?
2. If user deletes all sessions, does launch_date remain? (Contract says yes, but confirming client's assumption: we should display "Tracking for X days" even if history is empty.)
3. Does /user endpoint get called in any flow other than app launch? (Or is launch_date truly static, meaning we fetch once and cache forever?)

**Backend Impact (Tweedledum):**

User table includes launch_date UTC timestamp (nullable until first session). On first session creation, if launch_date null, set to session.start_time (exact, not normalized). Launch_date immutable. GET /user returns {launch_date, days_tracked} where days_tracked computed server-side. /user called on app launch and profile view; Tweedledee caches with infinity TTL.
