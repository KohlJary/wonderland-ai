## Review 044: M3 story portfolio: scope coherence and foundation grounding

**GUID:** 01KRY042JDYT52TNSNHHD0CBYP
**Files reviewed:** stories already on disk
**Verdict:** request-changes

### Findings

#### change-required: Stories 024–030 are well-formed but collectively drift M3's done_when boundary
**Location:** story slugs: save-endpoint-persists-note-state-to-sqlite-atomically through frontend-revision-id-tracking-and-collision-detection-flow-integration
**Quote:**

```
Stories 024–030 (Save endpoint, Load endpoint, Audit trail, Collision detection, Save button, Load-on-boot, Revision ID tracking) form a coherent set addressing backend persistence + collision safety, but they are authored as 'developer' foundation stories when they should be authored as 'Kohl' user-facing stories or deferred to a post-M3 durability milestone.
```

**Read:** Alice shipped 7 new stories in this turn, all grounded in developer personas ('Developer building the backend save handler,' 'Developer implementing collision detection,' etc.). Each story is individually coherent and addresses the persistence + collision pipeline M3's done_when implies. However, the framing as 'developer needs' rather than 'Kohl's experience needs' creates a persona mismatch: these aren't plumbing stories (developer-as-builder framing for internal infrastructure), they're capability stories (Kohl-as-user framing for observable behavior). The persona confusion matters because it obscures the actual milestone boundary: is M3 about 'the system persists and detects collisions' (Kohl-anchored), or is M3 about 'the developer builds a save endpoint' (foundation framing)? The done_when says the former; the story personas suggest the latter.
**Concern:** Mixing foundation personas (dev-building-X) with user-facing capability (Kohl's notebook persists) creates ambiguity about what counts as 'done.' If M3's done_when is 'Kohl can save and reload and the note is there,' then the stories should anchor in Kohl's actions, not in the developer's implementation tasks. Alternatively, if M3 is meant to be a foundation milestone (all developer-facing), the done_when should be rewritten to reflect that. Current state conflates the two frames.
**Request:** For each of Stories 024–030: either (a) reframe the story to anchor in Kohl's observable behavior (e.g., 'Kohl clicks Save and her note persists to SQLite' rather than 'Developer builds Save endpoint'), or (b) move the story to a post-M3 foundation-focused durability milestone. The choice depends on whether M3's intent is user-facing (Kohl saves and reloads) or infrastructure-focused (endpoint contracts). Alice's stories are clearer if you pick one frame. My read: M3 is user-facing (done_when is 'Kohl perceives persistence'), so reframe 024–030 to center Kohl's actions, not the developer's endpoint-building.

#### suggestion: Stories 024–030 lack explicit Kohl persona, inviting trainer hallucination in future M3 implementation
**Location:** all 7 stories authored this turn
**Quote:**

```
Each story opens with 'As a developer building X' or 'As a developer implementing Y.' The persona is a developer-as-implementer, not Kohl-as-user.
```

**Read:** The Dodo's constitution guards against 'persona + domain drift' — stories naming personas not in the seeded whitelist (only Kohl is seeded; Maya, Sarah, Akira, Jordan are pedagogical examples, not this project's characters). Alice caught this pattern earlier in the thread ('constitutional-prior leak'). Stories 024–030 don't name an out-of-scope persona by title, but they do frame the narrative as 'developer building' rather than 'Kohl using.' This is a subtle leak: the developer-builder frame invites the team to design around implementer concerns (endpoint contracts, revision IDs, transaction atomicity) rather than Kohl's concerns (work survives reload, collisions are caught, feedback is clear). The distinction matters because it shapes acceptance criteria and test scenarios downstream.
**Concern:** A story framed as 'developer building Save endpoint' naturally generates acceptance criteria like 'endpoint accepts title, body, tags' and 'transaction is atomic' — implementation details. A story framed as 'Kohl clicks Save and sees success feedback' naturally generates criteria like 'feedback is clear' and 'keystroke buffer survives' — user-observable behavior. Both are true, but they anchor differently. Alice's framing choice shapes what the Hatter tests, what the Tweedles implement, what the Caterpillar reviews. Mixing frames means different reviewers may expect different things.
**Request:** Rewrite Stories 024–030 with Kohl as the explicit persona and her observable actions as the narrative spine. Example: 'Kohl clicks Save button and sees a success message; the note persists to the backend and survives a page reload.' Then decompose the developer tasks (endpoint contracts, collision detection, audit logging) into separate stories or tickets where the framing is 'Developer implements Save endpoint to support Kohl's Save button flow.' This keeps the user-facing story pool aligned with Kohl's experience and the infrastructure stories honest about their supporting role.

#### suggestion: Stories 024–027 (Save endpoint, Load endpoint, Audit trail, Collision detection) assume backend contract design is done, but M3 done_when doesn't require contract negotiation to be complete
**Location:** stories 024, 025, 026, 027
**Quote:**

```
Story 024: 'POST /notes (or PUT /notes/{id}) accepts title, body, tags in the request body; Endpoint writes note and all tags to SQLite in a single transaction.' Story 027: 'Save endpoint requires the client to include the note's revision_id in the request; Before writing, the endpoint compares the client's revision_id to the backend's current revision_id.'
```

**Read:** Each of these stories names specific API contracts (endpoint paths, request bodies, response shapes, collision detection fields). The confusion-flags acknowledge ambiguities ('unclear whether PUT and POST are the same endpoint,' 'unclear whether revision_id should be in body or header,' 'unclear whether tags are nested or separate'). These are design decisions, not implementation details. M3's done_when doesn't mention 'contract negotiated' or 'API spec finalized' — it names observable outcomes ('Save button writes to SQLite,' 'page reload fetches from SQLite,' 'notes survive server restart'). The stories are pre-committing to contract details that should be negotiated in M3's M3.5 composition phase (when Caterpillar and the Tweedles align on the actual interface). Shipping these stories now locks in design choices that the pair protocol is meant to resolve collaboratively.
**Concern:** If these stories land on disk as-is, the Tweedles will feel pressure to implement the specific contracts named (PUT /notes/{id}, revision_id in body, SHA256 hash, etc.) because they're now 'requirements.' But these are scaffolding proposals, not firm requirements. The confusion-flags buried in each story acknowledge the ambiguity, but they're not surfaced loudly enough for the Rabbit to treat these as 'tickets with open design questions' rather than 'tickets with clear specs.' Result: the Tweedles either implement the scaffolding as-written (foregoing better design), or they push back and re-litigate these same decisions during pair protocol negotiation (wasting cycles).
**Request:** Keep Stories 024–027 but demote the specific contract details from acceptance criteria to confusion-flags. Rewrite acceptance as: 'Save endpoint persists note state to SQLite atomically with collision detection' (contract TBD). Move the 'POST /notes vs PUT /notes/{id}', 'revision_id in body vs header', 'SHA256 vs counter' decisions to a separate ADR or contract note that the Cheshire Cat and Tweedles negotiate in M3.5. This way the stories stay user-outcome-focused and the contracts are designed openly rather than baked into story acceptance.

#### note: Stories 028–030 (Save button integration, Load-on-boot, Revision tracking) are frontend-focused and well-aligned with M3's observable outcomes
**Location:** stories 028, 029, 030
**Quote:**

```
Story 028: 'Clicking Save button triggers an async POST to /notes/{id} (or /notes) with the current note state and revision_id... On 200/201 success response, the UI shows a brief success message and updates the note's local revision_id to the new one.' Story 029: 'On app boot, trigger a loadNotes() call that fetches GET /notes... Parse the response and for each note, compare its revision_id to the localStorage entry's revision_id.'
```

**Read:** These three stories are grounded in observable frontend behavior and user-facing flows: the Save button shows feedback, the app loads notes on boot, the revision ID is tracked so collisions are caught. They're more specific than Stories 024–027 and less contract-fragile because they describe components and logic, not API shapes. If the backend contract shifts (e.g., different endpoint path or response field names), these stories can adapt easily because they focus on the behavior, not the interface details.
**Concern:** none — these are well-formed and support M3's done_when coherently
**Request:** Leave Stories 028–030 as-is. Use them as anchors for the M3.5 contract negotiation: the backend contract must provide whatever the frontend needs to implement these flows. That's a cleaner coupling than Stories 024–027's vice-versa approach (backend contract first, frontend implements it).

### Approvals

- Stories 028–030 are well-grounded in frontend user flows and support M3's observable outcomes — they're clear references for the Tweedles to anchor their contract negotiation.

### Cross-domain references

- Stories 024–027 should be reviewed by Cheshire Cat as architectural proposals once reframed as 'contract options to negotiate' rather than 'confirmed specifications.' The API shape, collision detection mechanism, and revision ID encoding are architectural decisions that belong in an ADR, not in story acceptance criteria.
- The Hatter should flag the acceptance criteria in Stories 024–030 after reframing: some will be testable user-facing behaviors (Save button success feedback, notes persist across reload), while others are backend-contract specifics that belong in integration tests between the Tweedles, not in Kohl-persona scenarios.
