## Story 011: Feature 004 Happy Path — Kenji exports and shares session history

**Feature:** Share session history as proof of effort (feature-004)

**Persona:** Kenji, 31, a freelancer who occasionally needs to show clients evidence of focused work.

**Happy-path scenario:**

1. Kenji finishes a project. A client asks: "How much time did you actually spend focused on this task?" Kenji opens the app and navigates to History.

2. On the History screen, Kenji sees a date-range picker at the top. He selects "Last 7 days" (Monday–Sunday of the week he worked on the project).

3. A summary card appears: "7 sessions / 175 minutes (2 hours 55 minutes) from Nov 10–16." Below it, a daily breakdown shows:
   - Monday: 3 sessions / 75 min
   - Tuesday: 2 sessions / 50 min
   - Wednesday: 2 sessions / 50 min
   - Thursday-Sunday: 0 sessions

4. Below the summary, an "Export" button appears. Kenji taps it.

5. A simple text report generates:
   ```
   Focused Work Summary: Nov 10–16
   ————————————————————
   Total Sessions: 7
   Total Focus Time: 175 minutes (2 hours 55 minutes)
   ————————————————————
   Generated: 2024-11-18
   ```

6. Kenji taps "Copy" (or "Share"). The report text is copied to clipboard.

7. Kenji pastes the report into an email to his client: "Here's the breakdown of focused time I blocked for this project."

8. The client is satisfied. Kenji never had to manually track or export spreadsheets.

**Expected result:**

Kenji can generate and share a simple, readable proof of work effort without friction. The export is a plain-text summary, not a complex document.

**Contract assumptions validated:**

- History queries support date-range filtering.
- Pre-aggregated session counts and total focus time are computed server-side.
- Export is a simple text summary (not PDF, not image).
- Export can be copied to clipboard or shared via the device's native share intent.
