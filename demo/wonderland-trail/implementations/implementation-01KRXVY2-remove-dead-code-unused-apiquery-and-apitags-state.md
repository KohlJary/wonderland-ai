## Implementation 018: Remove dead code: unused apiQuery and apiTags state

**GUID:** 01KRXVY2GG02EN5XNVJ0Q8FK2M
**Side:** frontend
**Ticket:** ticket-01KRXVSS
**Contract:** message-envelope v3 (search endpoint unchanged)
**Ready for review:** yes

**Approach:**

Removed the unused useState declarations for apiQuery and apiTags (lines 54-55), removed the corresponding setApiQuery and setApiTags assignments in the search effect (lines 68-69), and updated the docstring to remove references to these variables. The component's logic is unchanged; it never read these variables, so their removal has no behavioral impact.

**Client State:**

No change to client state behavior. The component still tracks searchQuery, selectedTags, page, results, loading, and error. Removed unused tracking of apiQuery and apiTags, which were never read or used to derive UI behavior.

**Files:**
- frontend/src/Search.tsx: removed unused state declarations and assignments, updated docstring
