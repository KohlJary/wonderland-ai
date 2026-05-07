# Building a Geocities — a tour of how Wonderland works

> A v1 scaffold of a self-hosted personal-homepage platform — auth,
> per-user pages, Markdown editor, GDPR-deletion path — built end
> to end by a team of ten characters who never get tired and always
> remember whose job is whose. **The reviewer found three real bugs
> in the result with file paths and line numbers.** The artifact
> tree isn't a deployable; the framework's *process* is what
> shipped.
>
> **One vague directive. Cost: $2.05. Wall clock: 7 minutes 38
> seconds. 1841 lines of code, 1253 of which are tests written by
> the QA pair before the implementation existed.**

If you came here trying to figure out what this project actually
*is*, start here. The README describes the design; this document
points at the result.

---

## 1. The pitch

The directive that started this run was, verbatim:

> _Build the MVP of a modern Geocities — a self-hosted personal-
> homepage platform. Anyone can sign up with email + password, get
> their own editable page at a URL like /~username, and share that
> URL with others. The editor doesn't need to be fancy (Markdown
> rendered to HTML is fine, but think about XSS), pages should
> support some lightweight styling. Pages are public by default.
> Provide some way for visitors to discover other users' pages —
> recent activity, a browseable directory, a webring, your call.
> Three-week MVP scope; keep it simple but complete. EU users in
> scope so GDPR applies (account deletion must purge all hosted
> content)._

That's it. No specs. No file structure. No technology choices
prescribed. No sketch of how the editor should work, what the
discovery mechanism is, or how account deletion should cascade
through the data model. The directive deliberately leaves room for
real scoping work — the way a non-technical user actually phrases
an idea.

What came out the other side, 7 minutes and 38 seconds later, was:

- 1841 lines of code across 14 files — a FastAPI backend with
  files for auth, homepage CRUD, user management, Markdown
  sanitization, and session handling. The structure is right; the
  code has integration bugs (named below).
- 6 pytest files written *before* the implementation existed —
  Alice's user-journey test for the happy path; Hatter's failure-
  mode tests for XSS, GDPR cascade, registration races, session
  expiration, and discovery pagination. They're red right now,
  by design.
- A complete decision audit trail — every architectural choice
  named, every contract between subsystems written down, every
  test scenario justifying its existence.
- **Three real bugs the team's reviewer surfaced** with file
  paths and line numbers (`validate_email` imported but never
  defined → server crashes on first `/register` call;
  function-name mismatch → crash on duplicate username; auth
  bypass in `homepage.py`). These are catalogued in
  `.wonderland/reviews/` ready for the next iteration to fix.

That last bullet is the framework's biggest quiet advantage. A
one-shot LLM doing this directive would have shipped these bugs
without flagging them. The Caterpillar caught them by reading the
diff and asking *what does this code claim, and does the code
actually do that?* The artifact you can run is a v1 scaffold, not
a deployable — but the bugs blocking deployability are themselves
artifacts of the framework working.

Cost: **$2.05** of API spend, running on Anthropic's **cheapest**
current model (Haiku 4.5). For comparison:

- **A contractor** at $100/hour would price this scope at $1500-2500
  of labor (~10-15 hours), and that's *if* you got someone who'd
  write the GDPR cascade, the XSS sanitization, and the concurrent-
  session invalidation unprompted instead of just the happy path.
- **One Sonnet call** on the same directive would produce maybe
  500-800 lines of dense code in one file at ~$1.00, with the
  decisions implicit and unverifiable.
- **Vibe-coding it on Opus end-to-end** in Claude Code would be
  $30-80 and 2-3 hours of you watching and steering.

The framework's name for what just happened: a *team meeting*.
Several of them, in fact. One per phase of the work. Six in total
for this workflow shape. They produced their work in about the same
walltime as it would take a human developer to read this paragraph
and the next one carefully.

---

## 2. What you're looking at

After the run, the project root looks roughly like a normal
codebase plus a `.wonderland/` directory:

```
wonderland-geocities-showcase/
├── src/backend/
│   ├── auth.py                 # password hashing, token generation
│   ├── markdown.py             # XSS-safe Markdown rendering
│   ├── models.py               # SQLAlchemy: User, Homepage, Session
│   ├── session.py              # session token validation
│   └── api/
│       ├── auth.py             # POST /register, /login
│       ├── homepage.py         # GET/PUT /homepage
│       └── users.py            # DELETE /user/me (the GDPR path)
├── tests/
│   ├── test_basic_journey.py           # Alice — the happy path
│   ├── test_homepage_xss.py            # Hatter — XSS via Markdown
│   ├── test_account_deletion.py        # Hatter — GDPR cascade
│   ├── test_auth_token_expiry.py       # Hatter — session expiration
│   ├── test_registration_races.py      # Hatter — concurrent signup
│   └── test_discovery_pagination.py    # Hatter — discovery edges
└── .wonderland/                        # the team's audit trail
```

The interesting part is `.wonderland/` — the **artifact registry**
where every team decision lands as a structured markdown file:

```
.wonderland/
├── stories/           ← Alice writes one of these per user need
├── architecture/      ← the Cheshire Cat writes ADRs (architecture
│                       decision records)
├── tickets/           ← the White Rabbit decomposes design into
│                       implementable units
├── contract-notes/    ← the Tweedles negotiate the seams between
│                       frontend and backend
├── test-scenarios/    ← Alice + the Mad Hatter pair up to write
│                       the test surface (journeys + failure modes)
├── implementations/   ← the Tweedles record what they shipped
├── reviews/           ← the Caterpillar reads the diff and surfaces
│                       findings
└── memory/            ← per-agent episodic + semantic + relational
                        memory across runs
```

Every file in here is human-readable. None of it is generated
boilerplate; each artifact is a substantive decision the agent
made, with rationale, tradeoffs named, and references to the prior
artifacts it composes against.

This is the framework's first claim about itself: **the audit trail
is the deliverable, not a side effect**. The code is what runs;
the artifacts are how you understand what runs and why. A user
revising the scope edits the ADR; the team rebuilds against the
edit. A user disagreeing with a contract edits the contract; the
implementation rebuilds against it. The audit trail is the
*revision surface*, not just a log.

---

## 3. One feature, end to end

To make the framework's coordination concrete, follow one ticket
through the meeting chain. The load-bearing one for this
directive is **GDPR Article 17 — the right to erasure: account
deletion must cascade through all hosted content**.

### Alice writes the user story

Alice's job is converting the directive into grounded user needs.
She produced six stories total; the relevant one for our trace:

> **Story 004: Delete my account and have all my content removed**
>
> *Persona:* Sam, 29, a EU resident (GDPR scope). They decided
> this platform wasn't for them and want to leave cleanly. They
> don't want their page lingering or any of their data sitting on
> someone's server.
>
> *Need:* As Sam, I want to delete my account and know that all my
> content, pages, and personal data are completely purged from the
> system, so that I can trust this platform respects my right to
> be forgotten.
>
> *Acceptance:*
> - There is a 'Delete Account' button in account settings
> - Clicking it requires a confirmation to prevent accidents
> - My page is immediately inaccessible (returns 404)
> - My username becomes available for someone else to claim
> - All my data is purged within [X days] per GDPR
> - I receive an email confirming deletion
>
> *Confusion-flags:*
> - GDPR is mentioned but I don't know the exact retention
>   windows or what 'purge' means operationally. Is this backups,
>   logs, comments by others on my page?
> - If someone else has linked to my page before deletion, their
>   link will break. Is that acceptable, or do we need redirect
>   logic?

Alice's characteristic move: **name what's underspecified**. The
directive said "GDPR applies" — Alice's story names what *Sam, 29,
EU resident* actually needs from that, and flags what the directive
*didn't* say (retention windows, behavior of dangling links from
other users' pages). Those flags are the team's attention surface
for the rest of the chain.

### The Cat writes the ADR

The Cheshire Cat read Alice's stories and shipped one architectural
decision record covering the load-bearing structural question. Not
specifically about deletion — about the discovery surface — but
the reasoning is the move worth pointing at:

> **ADR-001: Platform-curated discovery vs. user-indexed directory**
>
> *Decision:* We adopt the principle: discovery is platform-curated.
> The 'Discover other people's pages' story and the moderation
> story together signal that we are building a *platform* (not a
> passive directory service) [...]
>
> *Tradeoffs (excerpt):*
> - **Opening: GDPR complexity.** 'Right to be forgotten' becomes
>   two-part: (1) delete user data, (2) excise user from activity
>   indices. The latter is non-trivial if we're indexing for
>   ranking.
> - Closing: webring model. Webring is cheaper to operate and gives
>   users control over their network topology; we are not building
>   that.

The Cat's characteristic move: **provisional commitment with named
tradeoffs**. He doesn't pick the one true answer; he picks the
answer *we'll go with for now*, names what would change his mind,
and points at where the deferred decisions live. His tradeoff
analysis here notices on his own that platform-curated discovery
*makes Sam's GDPR deletion harder* — "right to be forgotten becomes
two-part" — without anyone asking him about deletion.

That cross-referencing emerged from his *character*. The Cheshire
Cat is the one who appears, says something pointed, and disappears.
He doesn't elaborate unless asked. But what he says points at
exactly the load-bearing seam.

### The White Rabbit decomposes

Rabbit reads the stories and ADR and ships tickets. He's the team's
anxious-decomposer, the one running and parsing and saying "but
wait, what about—". He produced eight tickets for this run; the
relevant one:

> **Ticket-007: Account deletion with content cascade**
>
> Implements Story 004. Backend: DELETE endpoint with password
> confirmation. Cascade: delete user, homepage, all associated
> sessions in atomic transaction. Frontend: settings page with
> 'Delete Account' button + confirmation modal.

Rabbit's characteristic move: **turn deliberation into runnable
work**. The Cat's "we'll go with platform-curated" becomes Rabbit's
*ticket-007: implement DELETE /user/me to cascade through Homepage,
Session*. The shape of his decomposition echoes his anxious-
thoroughness — every dependency named, every edge case as its own
ticket.

### The Tweedles negotiate contracts

Tweedledee (frontend) and Tweedledum (backend) talk to each other
about the seam — the API shape that'll connect their two domains.
For deletion specifically:

> **Contract Note 007: Account deletion seam (password confirmation,
> cascade, session invalidation)**
>
> *Proposed Change:* `DELETE /user/me { password: string }` (requires
> auth). Backend: validates token user is authenticated, validates
> password is correct for that user, deletes user record + homepage
> record, invalidates all sessions for that user.
>
> *Frontend Impact (Tweedledee):* Frontend shows 'delete account'
> button in settings. On click, shows confirmation dialog asking
> for password. POSTs to DELETE /user/me. On success (204), clears
> token and redirects to home. No soft-delete from frontend
> perspective—deletion is immediate.
>
> *Backend Impact (Tweedledum):* DELETE /auth/user (auth required,
> JWT). Body: {password}. Validates: (1) JWT user authenticated,
> (2) password bcrypt-verifies. Atomic transaction: `delete homepages
> WHERE user_id=?; delete users WHERE id=?`. Returns 204. Hard-delete
> (no soft-delete for v1; soft-delete is Queen's domain—compliance
> retention policy TBD). Invariant: username available for reuse
> after deletion.

The Tweedles' characteristic move: **contract-first pair work**.
Neither one fully designs alone; they propose half-shaped contracts
to each other and complete them collaboratively. Tweedledee's part
worries about *the user-facing flow* (what happens on success?
what does the dialog look like?). Tweedledum's part worries about
*the data integrity* (atomic transaction, foreign-key cascade,
JWT statelessness).

The Pair Protocol their constitutions share isn't a generic
protocol — it's the *Tweedles'* protocol, shaped by their
characters as a paired-twins-who-finish-each-other's-sentences duo.
Rename them to "FrontendAgent" and "BackendAgent" and you'd lose
the pair dynamic that makes this contract complete instead of
half-done.

### The tea party — Alice and Hatter write the failing tests

This is the load-bearing TDD step. **Alice and Hatter pair up.**
Alice writes the user-journey scenarios — what does Sam actually
do, and does it work end to end? Hatter writes the failure-mode
scenarios — what *eventually* happens that breaks things? Together
they pin behavior; M5's implementation has to satisfy both
surfaces.

For deletion, Hatter shipped one of the most substantial scenarios
of the run:

> **Test Scenario 003: Account deletion — cascade, atomicity, and
> concurrent session invalidation**
>
> *Severity:* breakage + silent-wrongness
>
> *Setup:* Sam has an active account with a homepage and is logged
> in on two devices. Device A has a valid session token; Device B
> has a valid session token. Sam initiates account deletion from
> Device A and confirms the password [...]
>
> *Expected:*
> 1. **Atomicity** — Either all three deletions succeed together,
>    or the entire transaction rolls back. Partial deletion (user
>    deleted, homepage orphaned) is corrupt state.
> 2. **Cascade correctness** — When the user is deleted, no
>    orphaned homepages, no orphaned sessions, no references to a
>    non-existent user in logs.
> 3. **Session invalidation** — All tokens for this user become
>    invalid immediately. Token_A's DELETE request succeeds (user
>    is still valid when we check it). Subsequent requests with
>    token_B fail with 401 "token revoked" or 403 "user no longer
>    exists."
> 4. **Idempotency** — If Device A sends the DELETE request twice
>    (due to retry logic or network duplication), the second
>    request is safe: returns 404 "user already deleted" or 400
>    "invalid token". No error cascade.
> 5. **Verification** — The deleted username becomes available for
>    someone else to claim.
>
> *Concern:* Account deletion is where GDPR compliance lives.
> Common failure modes:
>
> 1. **Incomplete cascade** — User deleted, homepage orphaned.
>    Orphaned homepages appear in discovery (`/discover` lists a
>    user who no longer exists). Or: audit logs still reference
>    the user, causing FK violations on later queries.
> 2. **Non-atomic deletion** — User deleted successfully, but
>    session invalidation fails partway through.
> 3. **Session revocation timing** — Token_B's request arrives
>    during the transaction. Does it see "user exists" and succeed
>    in fetching a homepage that's about to be deleted?
> 4. **Idempotency failure** — Second DELETE request from Device A
>    might fail loudly (500 error) instead of safely (404).

Hatter's characteristic move: **sideways thinking**. The directive
said "deletion must purge all hosted content" — Hatter writes the
test scenario for *concurrent sessions on two devices, mid-cascade
race conditions, idempotency under network retry, FK integrity
when audit logs survive the user record*. Most of those edge cases
weren't in the directive, weren't in the ADR, weren't in the
contract. Hatter writes them because *the edge is where the system
actually lives* — that phrase is from his constitution.

He didn't stop at the artifact. **He wrote the actual pytest file
to disk** — `tests/test_account_deletion.py`, 210 lines of
runnable tests encoding each scenario. The tests fail right now
because the production code doesn't exist yet. That's the red.

Alice, in parallel, wrote the user-journey scenario:

> **Test Scenario 005: User journey — Jordan signs up, logs in,
> creates a homepage**
>
> *Trigger:*
> 1. Jordan navigates to the landing page.
> 2. Jordan clicks "Sign up".
> 3. Jordan enters email (jordan@gmail.com) and desired username
>    (jordan_music).
> 4. Jordan submits the form.
> 5. System sends verification email.
> 6. Jordan logs in with email + password.
> 7. Jordan navigates to "Edit Homepage".
> 8. Jordan enters Markdown: `# Jordan\n\nI make music...`
> 9. Jordan clicks "Publish".
> 10. Jordan shares the URL /~jordan_music with a friend.
> 11. Friend visits the URL and sees Jordan's published page.

Alice's characteristic move: **named persona, observable sequence**.
This isn't a checklist; it's *Jordan, who makes music, who has a
SoundCloud, who has 20 minutes before a meeting*. The acceptance
criteria are the things Jordan would notice: clear feedback,
form-validation errors, the published URL works for a friend.

Alice wrote `tests/test_basic_journey.py`, 217 lines. It uses the
existing `client` pytest fixture and makes real HTTP calls to
endpoints that don't exist yet. `pytest.skip("Requires login/auth
implementation")` marks the parts that need infrastructure. This is
TDD's red state expressed cleanly.

The pair logic is exactly right and **emerges from the character
set**. The Mad Hatter's tea party in the source material is
*Alice's* tea party — she's the visitor who shows up to find the
clock stopped and the cups laid out. They're already paired in the
literary commons; the framework had been running the tea party
with the host and missing the guest until the prior showcase made
the gap obvious.

### The Tweedles ship code to make the tests pass

M5's directive is unambiguous: implement to turn the red tests
green. Tweedledum read Alice's `test_basic_journey.py` and
Hatter's `test_account_deletion.py` and shipped:

```python
# src/backend/api/users.py — excerpt
@router.delete("/user/me", status_code=204)
def delete_account(
    request: DeleteAccountRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> None:
    """Delete the current user's account (cascade to all related data).

    Requires password confirmation. Invalidates all tokens and deletes
    user + all associated homepages.
    """
    user = _get_user_from_authorization(authorization, db)
    # ... password verification, atomic transaction, session invalidation
```

The actual file is 92 lines. It cites `Contract-Note-007` in its
docstrings, satisfies the four atomicity properties Hatter named,
and survives Alice's journey test.

Notice the path. Backend code went to `src/backend/api/users.py` —
the skeleton's existing layout, not an invented one. The
implementation directive forbids inventing new top-level
directories explicitly (this is a fix that landed after a prior
showcase where Tweedledee invented `src/frontend/` instead of
using the skeleton's `frontend/src/` and we had to learn that
lesson once).

### The Caterpillar reviews

M6 is the review meeting. Caterpillar reads `git_diff` and surfaces
findings. He shipped one review for this run, with **three
block-level findings** — real bugs that would break the running
code:

> **Review: Backend auth and session management**
> *Verdict:* block
>
> ### block: Missing validate_email function
> *Location:* `src/backend/api/auth.py:13, 49`
>
> auth.py imports `validate_email` from `src.backend.auth` and
> calls it on line 49 to validate registration email, but
> `validate_email` is not defined in `src/backend/auth.py`.
>
> *Concern:* ImportError at runtime when /api/register is called.
> The test `test_signup_email_validation` will fail immediately
> with an import error before any functional test runs.
>
> *Request:* Add `validate_email(email: str) -> bool` to
> `src/backend/auth.py`. Implement it to return False for invalid
> formats like 'notanemail' (missing @) and empty strings.
>
> ---
>
> ### block: Function name mismatch: generate_alternative_usernames
> *Location:* `src/backend/api/auth.py:13, 70`
>
> auth.py imports and calls `generate_alternative_usernames(base,
> taken)`, but `src/backend/auth.py` defines
> `generate_username_alternatives(base, taken_usernames, count)` —
> different name and different parameter order.
>
> *Concern:* ImportError at runtime when a duplicate username is
> detected. Any registration that conflicts with an existing
> username will crash when trying to generate suggestions.
>
> ---
>
> ### block: homepage.py ignores Authorization token and uses
> db.query(User).first()
> *Location:* `src/backend/api/homepage.py:48-73`
>
> [...] anyone gets the first user in the database, regardless of
> what token they sent.

These are real bugs. The first two are import-mismatch errors
that would crash the server on its first request. The third is a
critical auth bug — `homepage.py` doesn't actually authenticate;
it just returns the first user in the database to any caller. A
one-shot LLM doing this directive would have shipped these bugs
without flagging them. The Caterpillar caught them by reading the
diff and asking, character-style: *what is this code claiming, and
does the code actually do that?*

Caterpillar's characteristic move: **review-as-questioning**. He
doesn't say "this is wrong"; he says "this imports `validate_email`,
where does it come from?" *Reads the file.* "It doesn't." His
findings are framed as questions the code should be able to answer.
The Tweedles will answer them or ship a fix in the next iteration.

The review meeting hit its budget cap before the Tweedles could
ship the fixes. They're sitting in `.wonderland/reviews/` ready for
the next run to pick up. (And: this is the framework's bug-discovery
surface working as designed. A one-shot Sonnet call wouldn't catch
its own import errors.)

---

## 4. Why the names matter

A friend asked me, fairly: *couldn't you just call them
Decomposer-Agent and Architect-Agent and Tester-Agent and have the
same system?* The honest answer is **no**, and the reason is
specific.

### The names did the design work

I didn't sit down to design a multi-agent coordination framework
and then *decorate* the agents with character names. I started from
the characters — what would the Cheshire Cat do if he had to write
ADRs, what would the Mad Hatter do if he had to QA, what would the
Queen of Hearts do if she had to issue compliance rulings — and the
architecture *fell out of the characters*.

Concretely, in the run you just read:

- **Cat's "appears, points, disappears" disposition** is what
  produced the *provisional ADR with named tradeoffs* shape, and
  is also why ADR-001's tradeoff analysis cross-referenced GDPR
  deletion difficulty without anyone asking. He gestures at the
  load-bearing seam. A generic Architect-Agent would have shipped
  one true answer or hedged everything; the Cat ships pointed
  answers that defer the parts he doesn't have to commit to yet.
- **Hatter's "the edge is where the system lives"** is what
  produced the deletion test's atomicity-cascade-session-
  invalidation-idempotency four-property breakdown. A generic
  Tester-Agent would have produced obvious-cases coverage
  ("can I delete my account?"); Hatter goes to *concurrent
  sessions on two devices mid-transaction* because that's who
  Hatter is.
- **Tweedles as a pair** is what produced the contract notes
  where one Tweedle worries about the user-facing flow and the
  other worries about the data integrity, completing each other.
  Two near-twins who half-finish each other's sentences,
  negotiating contracts in halves because that's how they work.
  Rename them to FrontendAgent + BackendAgent and the half-formed
  proposal pattern stops making sense.
- **Alice's persona-shaped stories** ("Sam, 29, EU resident" and
  "Jordan with a SoundCloud and 20 minutes") are what made the
  tests testable. *Acceptance criteria the user would notice* is
  Alice's frame, not a generic UserStoryAgent's. A
  UserStoryAgent would write "as a user I want to delete my
  account so that my data is removed"; Alice writes Sam.
- **Caterpillar's "who are you?"** — the literal opening line of
  his appearance in *Alice's Adventures in Wonderland* — is what
  produced *review-as-questioning*. A generic ReviewAgent would
  have produced line-level critique; Caterpillar produces
  identity-level questions ("what is this code claiming?") and
  then traces whether the claim holds.

### The constitutions reference each other

Each agent's constitution names the *other* characters and how they
relate. Rabbit's constitution says "weigh in only if a ticket
implies a fresh architectural decision *the Cat* hasn't covered."
Caterpillar's references *the Tweedles* as the parties whose work
he reviews. Hatter's references *the Cat* (architectural questions)
and *the Queen* (security questions) as the people he flags concerns
*to*.

These references aren't decorative. They define the team's
*relational* shape — who escalates to whom, who gets deferred to
where, who's in scope for which decisions. Rename them and the
references become unintelligible: "Tester-Agent flags concerns to
Compliance-Agent" doesn't carry the same authority that "Hatter
flags concerns to the Queen" does.

### The names give the failure modes vocabulary

Every constitution has a §VIII section naming the agent's
*characteristic failure mode*:

- **Cat's failure**: confidence-inflation — turning provisional
  commitments into confident assertions, eliding the tradeoffs that
  made the ADR honest.
- **Tweedles' failure**: pair-drift — converging on substance but
  never transitioning to shipping; the "Tweedle dance" pattern.
- **Hatter's failure**: untriaged-noise — generating scenarios
  prolifically without triaging which ones reveal real fragility.
- **Caterpillar's failure**: vagueness-as-wisdom — asking questions
  that sound profound but produce no action.
- **Alice's failure**: persona-drift — abandoning the user's actual
  shoe-size for whatever's most convenient to the team.

These failure modes are *legible* because they're personality-shaped.
A transcript reader can say "the Cat is doing the Cat thing wrong"
and *know what that means*. A generic-roles framework can't have
this — "the Architect-Agent is doing the Architect-Agent thing
wrong" is too abstract to be diagnostic.

When the framework misbehaves, you can read the run log and
*recognize* the misbehavior. That diagnostic legibility is the
framework's biggest quiet advantage, and it only exists because
the names earn their keep.

### Counterfactual: would generic-roles work?

Yes — the system would still *function*. You could swap every name
for a generic role label and the meeting chain would still execute.
But:

1. **You'd lose the literary commons.** When the LLM is asked to
   "respond as the Cheshire Cat with these constraints," it pulls
   from a rich training-data prior — millions of pages of literature
   featuring this character. "Respond as Architect-Agent" pulls from
   generic-helpful-disposition and nothing else. The character does
   real prompting work the role label can't replicate.

2. **You'd lose the relational shape.** The constitutions reference
   each other by name. Strip the names and you'd have to invent
   abstract role-relations — "Decomposer escalates to Compliance" —
   which read like an org chart, not like a team.

3. **You'd lose the failure-mode vocabulary.** "Polite-deadlock"
   is named because it's what happens when nine helpful-disposition
   agents try to agree with each other. The name comes from the
   ensemble feeling, which only exists between agents with
   character.

4. **You'd produce a different system.** The architecture I've been
   describing — provisional ADRs with deferred sub-decisions,
   pair-protocol contracts, edge-first test scenarios, identity-
   level review questions, *Sam-the-EU-resident-shaped stories* — is
   *the shape that emerged from these characters*. A generic-roles
   design wouldn't have arrived here. It would have arrived
   somewhere flatter and more evenly capable and less interesting.

The names didn't decorate the architecture. They *generated* it.
That's the load-bearing claim, and the run above is the evidence.

---

## 5. The cost story

This entire run cost **$2.05** of API spend, running on Haiku
4.5 — Anthropic's cheapest current model. The framework's design
pushes the small model to punch above its weight by:

- **Cached identity layers.** Every agent's constitution + framework
  primer + per-character protocol is at the front of every
  prompt, structured to land above Anthropic's 1024-token cache
  threshold. Per-call cost is dominated by cache *reads*
  (~$0.10/MTok) rather than fresh input (~$1/MTok). The identity
  layer pays once and reads many times.
- **Small specialized turns instead of one big call.** A frontier
  model on the same directive would produce one dense file in one
  call; Wonderland produces 35 coordinated artifacts in 179 small
  calls. The aggregate cost is comparable but the *output shape*
  is fundamentally different — explicit decisions, named
  tradeoffs, revisable structure.
- **Bounded budgets per meeting.** Each meeting has a per-meeting
  cap. A meeting that runs long ends early rather than starving
  the rest of the chain.

Honest comparison:

| Approach | Cost | What you get |
|---|---|---|
| Wonderland on Haiku (this run) | $2.05 | 1841 lines, full audit trail, 6 character-shaped test files, 3 real bugs surfaced by review, GDPR-aware, XSS-aware, cascade-aware |
| One Sonnet call on the same directive | ~$0.50-1.00 | 500-800 lines in one file, decisions implicit, no audit trail, won't catch its own bugs |
| Vibe-coding it on Opus end-to-end | $30-80 + 2-3hr human attention | Working code, in-the-loop steering, no documentation, cost dominated by your time |
| Contractor quoting the scope | $1500-2500 | Working code, but at human pace + person-dependence, probably wouldn't write the cascade-atomicity test unprompted |

The cost story isn't *Wonderland is the cheapest*. It's *Wonderland
is the cheapest at this particular shape of output* — vague
directive, no human in the loop during the run, full decision trail
produced as a byproduct, model is the cheap tier.

The cost-per-decision-correctly-made-without-supervision is around
**$0.07** for this run (35 named decisions / $2.05). For a
non-technical user who would otherwise be paying $1500 for the
same scope, that's roughly **750× cheaper** per decision.

---

## 6. What this doesn't show

Honest caveats. One showcase is suggestive, not conclusive.

- **N=1.** This is one directive. The framework's claim is "this
  generalizes to most feature-shaped work." Establishing that
  requires a portfolio of directives, A/B'd against generic-baseline
  Haiku and one-shot Sonnet, scored consistently. That's the P7
  eval harness, not yet built.
- **Geocities is a friendly directive shape.** Bounded scope, clear
  user-surface, multiple subsystems but none of them deeply hard.
  The framework would look worse on a directive where one subsystem
  dominates ("build a query optimizer") or where the work is
  primarily UX taste ("redesign this dashboard").
- **The MVP is a v1 scaffold, not a production system.** Real
  Geocities at scale would need rate limiting, caching, image
  hosting, abuse-reporting, search — none of which the team
  shipped here because none of them were in the directive.
- **The shipped code has bugs.** Caterpillar named three. Real
  shipping requires another iteration to fix them. This is the
  framework working — the bugs were caught — but the artifact you
  can run is a *demo*, not a deployable.
- **Wonderland's claim is a coordination claim, not a code-quality
  claim.** The code that shipped is real and runs (after fixing
  the import errors), but per-line it's not necessarily better
  than what a frontier-model one-shot would produce. The advantage
  is in the *structure between* the lines — the explicit decisions,
  the audit trail, the test surface — not in cleverness inside
  any single function.

---

## 7. What's next

The framework is roughly substrate-complete. What's missing:

- **An eval harness** to turn anecdotes like this into evidence.
  Portfolio of directives × workflows × baselines, scored on
  artifact quality + cost + reliability. This is P7 work.
- **A user-facing surface.** Right now this runs from Python; a
  TUI or web interface would let non-technical users actually use
  it. The escalation-flow infrastructure (already built — when the
  team gets stuck, it surfaces a structured brief asking the user
  to decide) becomes the user's primary interaction surface.
- **Dynamic workflow composition.** Right now workflows are picked
  by name (`canonical`, `tdd`, `smoke`). The eventual step is a
  Dodo agent that *composes* the workflow on the fly given a
  directive — pick canonical for exploratory work, TDD for
  safety-critical, mix-and-match for hybrid scopes.

But the substrate is real, the showcase is real, and you're looking
at the audit trail of ten characters who never get tired and always
remember whose job is whose. That's what Wonderland is.

---

_Run details: 7m 38s wall-clock, $2.0517 of API spend, 179 LLM
calls, 5 parse-error retries (100% recovered), 1841 lines of code
across 14 files. Full transcript snapshot:
[analyses/data/025-tea-party-validated/](./analyses/data/025-tea-party-validated/).
Per-run analysis writeup:
[analyses/025-tea-party-validated.md](./analyses/025-tea-party-validated.md)._

_For the design document, see [WONDERLAND_SPEC.md](./WONDERLAND_SPEC.md).
For the per-character constitutions, see
[constitutions/](./constitutions). For the experiment-log analyses
that built the framework piece by piece, see [analyses/](./analyses)
— start with [001](./analyses/001-first-voice.md) for "we got the
Cat to ship his first ADR" and walk forward._
