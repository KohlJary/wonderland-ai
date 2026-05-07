## Scenario: User journey — Jordan signs up, logs in, creates a homepage

**Severity:** breakage (if the happy path breaks, nothing else matters)

**Setup:**

Jordan has a Gmail account and 20 minutes before a meeting. They've heard about this platform and want to claim a username and put up a quick bio.

**Trigger:**

1. Jordan navigates to the landing page.
2. Jordan clicks "Sign up".
3. Jordan enters email (jordan@gmail.com) and desired username (jordan_music).
4. Jordan submits the form.
5. System sends verification email.
6. Jordan clicks the verification link in the email (or it's auto-verified; contract is ambiguous).
7. Jordan logs in with email + password.
8. Jordan navigates to "Edit Homepage".
9. Jordan enters Markdown: "# Jordan\n\nI make music. Check out my [SoundCloud](https://soundcloud.com/...)".
10. Jordan clicks "Publish".
11. Jordan shares the URL /~jordan_music with a friend.
12. Friend visits the URL and sees Jordan's published page.

**Expected:**

All of the above succeeds, and takes less than 2 minutes (per the story's acceptance criteria, though this is Alice's domain to test). At each step:

- Jordan receives clear feedback (success message, next button, etc.).
- Form validation is clear (e.g., "Email is invalid" or "Username must be 3+ characters").
- Verification email is sent to the correct address.
- Login succeeds and gives a token/session.
- Homepage editor shows a live preview (or at least, saves and renders correctly).
- The published page is publicly visible at the correct URL.
- The page renders the Markdown correctly (bold, links, etc.).

**Concern:**

This is the entire happy path. If it breaks, everything breaks. Common failures:

1. **Email validation** — backend accepts invalid emails; verification email never arrives.
2. **Token/session management** — login succeeds but logout doesn't clear the token; or the token format is wrong and subsequent requests fail.
3. **Markdown rendering** — homepage is saved but renders as plaintext or HTML, not as styled Markdown.
4. **URL routing** — the public URL is wrong (e.g., /user/jordan instead of /~jordan_music).
5. **Persistence** — homepage is created in the session but not saved to the database; it disappears on page refresh.
6. **CORS or content-type issues** — responses are sent with wrong headers; frontend can't parse JSON.

This scenario is the smoke test. If it fails, the whole app is broken.

**Property:**

For a user U with email E and desired username N:

1. Registration with (E, N) succeeds and sends a verification email to E.
2. Clicking the verification link (or auto-verifying) makes U's account ready to log in.
3. Login with (E, password) succeeds and returns a valid token T.
4. With token T, U can POST to /api/user/me/homepage with Markdown M.
5. Subsequent GETs to /api/user/N return the rendered HTML version of M.
6. Unauthenticated visitors can GET /api/user/N and see the rendered page.
7. The rendered page contains the HTML corresponding to M (links are <a> tags, bold is <strong>, etc.).

**Implies:**

Implies a full integration test (Tweedledum's domain). Implies that email sending works (may need mocking or a test email service). Implies that the contract agreements between Tweedledee (frontend) and Tweedledum (backend) are solid and complete.

---

## Notes for Test Implementation

This is the scenario that would ideally be run end-to-end with a real browser (Tweedledee's territory). At the backend level, we test:

1. POST /api/register with valid email/username succeeds.
2. POST /api/login with email/password returns a token.
3. POST /api/user/me/homepage with markdown (auth required) succeeds.
4. GET /api/user/{username} returns the rendered page.
5. All responses have correct status codes and content-type.

Notably: email sending is mocked (or we use a test email service), and we don't test the "click email link" part. That's Tweedledee's domain (browser integration).

This test will FAIL until all six endpoints and their integration are correctly implemented.
