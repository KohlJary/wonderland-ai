## Ticket 025: Dead code: unused apiQuery and apiTags state variables

**GUID:** 01KRXVSS194TZEX5V93PA99V11
**Sources:** kohl-can-find-past-notes-by-title-or-content-search, search-feature-implementation-full-stack
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``search-feature-implementation-full-stack`` (change-required):

**Concern:** Dead code increases cognitive load and suggests incomplete refactoring. Readers may wonder what these variables are for and why they're not used, which wastes their time. Removing unused state clarifies the component's actual concerns.

**Request:** Remove the two unused state declarations (lines 54-55) and remove the corresponding setApiQuery and setApiTags assignments (lines 68-69). If you need to track the API-side query for some reason (e.g., to prevent redundant requests), add a comment explaining why; otherwise, remove it.

**Location:** ``frontend/src/Search.tsx:54-55``

**Acceptance:**
- Remove the two unused state declarations (lines 54-55) and remove the corresponding setApiQuery and setApiTags assignments (lines 68-69). If you need to track the API-side query for some reason (e.g., to prevent redundant requests), add a comment explaining why; otherwise, remove it.
