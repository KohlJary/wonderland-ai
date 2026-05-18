## Feature 009: Kohl drafts and saves experimental notes with persistent backup

**GUID:** 01KRY05DYSF1FQT90922AMPAGV
**Kind:** capability
**Sources:** 01KRXRDES1D2YNVMG16Y6PFVSA:localstorage-backed-note-state-layer, 01KRXSYZG7H2YNVMG16Y6PFVSB:replace-hellomessage-scaffolding-with-note-model, 01KRXSZRG7I2YNVMG16Y6PFVSC:editor-ui-layout-two-pane-with-title-body-editor-and-tags, 01KRXZJRZ7SWB69XK08PXVYNEX:save-endpoint-persists-note-state-to-sqlite-atomically, 01KRXZJRZ7SWB69XK08PXVYNEY:load-endpoint-fetches-notes-from-sqlite-with-merge-strategy-for-localstorage-drift, 01KRXZJRZ7SWB69XK08PXVYNEZ:audit-trail-logs-every-save-with-full-note-state-and-revision-id, 01KRXZJRZ7SWB69XK08PXVYNF0:collision-detection-via-revision-id-prevent-silent-overwrites-when-multiple-tabs-save-concurrently, 01KRXZM1NPKFYDBZHDA4GRTS4Y:frontend-save-button-integration-with-backend-save-endpoint, 01KRXZM1NPKFYDBZHDA4GRTS4Z:frontend-load-on-boot-integration-with-backend-notes-endpoint-and-localstorage-merge, 01KRXZM1NPKFYDBZHDA4GRTS50:frontend-revision-id-tracking-and-collision-detection-flow-integration
**Personas:** Kohl
**Stack span:** full-stack
**Tier:** v1

**Description:**

Kohl can write experimental notes with title and markdown body, have her keystrokes buffered to localStorage for resilience during the session, and permanently save the note to backend storage. The save is atomic (no partial writes) and conflict-safe (multiple tabs cannot silently overwrite each other's work). Kohl's work survives page reload, browser restart, and device loss.

**Constituent tickets:**
- *(to be decomposed in M3)*
