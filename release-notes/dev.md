# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

## milestone_plan kind decision: surface routing consequence + concrete failure mode (T-ab61)

T-ab58 added a decision rubric for foundation vs capability + non-M1 foundation guidance. mvp-demo-redux and the LDR dashboard pilot both still shipped milestones literally NAMED "Foundation: ..." in their titles but tagged `kind: capability`, requiring operator intervention to flip them before downstream design routed correctly. The directive described WHAT each kind meant and HOW to decide, but never made the CONSEQUENCE of the choice visible to the agent — the field looked like metadata, so the planner defaulted to whatever felt safe (capability).

T-ab61 reframes the kind discussion to lead with the routing consequence:

- **Field now framed as "materially changes how the milestone gets designed"** — not metadata, a routing decision the substrate consumes downstream.
- **Explicit failure mode named**: "Alice writes 'Kohl can sign up' stories for what is actually the auth + session + DB-schema-bootstrap work. The stories describe the user-facing surface but not the infrastructure underneath. Downstream tweedles read those stories looking for the contract to implement and find only the UX layer — the JWT signing, password hashing, session cookie handling, migration runner all have to be reverse-engineered from 'Kohl can sign up.'"
- **Concrete precedent cited**: "mvp-demo-redux and the LDR pilot both shipped milestones literally NAMED 'Foundation: ...' in their titles but tagged kind: capability, and the operator had to manually flip them before downstream design could route correctly."
- **Two compact rules at the end of the block**: "If your milestone title contains the word 'Foundation,' the kind should almost certainly be foundation. If you find yourself writing a done-when condition that reads 'developer can ...' or 'project gains the ability to ...,' the kind is foundation."

Trimmed the now-redundant "Caterpillar solo / Alice solo" routing description from the original per-kind bullets (the new framing makes that explicit at the top). Net change: ~25 lines added, ~7 trimmed.

If this still doesn't stick on the next pilot's planner output, the next escalation is substrate-level enforcement (auto-flip kind when title regex matches "foundation" OR consumes are 100% infrastructure-shaped requirement kinds).

Pure directive change in `milestone-plan.yaml`. 30/30 workflow load + milestone tests pass.
