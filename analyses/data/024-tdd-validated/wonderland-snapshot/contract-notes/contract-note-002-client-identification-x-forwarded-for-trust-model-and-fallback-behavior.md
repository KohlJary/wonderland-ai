## Contract Note 002: Client identification: X-Forwarded-For trust model and fallback behavior

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No prior contract.

**Proposed Change:**

Backend identifies client by: (1) X-Forwarded-For header if present AND trusted (per config), (2) fallback to remote address. Frontend assumption: rate limit is per-client-as-backend-identifies-it. This is not visible to frontend in the happy path (request succeeds), but matters when rejection happens. Frontend needs to know: what does backend do if both headers are missing/invalid? Does it reject, or use a default fallback?

**Source:** story-003 (spoofing defense) + ADR-001 (trust model)

**Frontend Impact (Tweedledee):**

Your question about fallback — backend answer: if client cannot be identified, request is rejected 400, not dropped. So from frontend standpoint: you will never see a mysterious 429 from an unidentified client. Either request succeeds (client identified, under quota), or returns 429 (identified, over quota), or returns 400 (not identifiable). This keeps error semantics predictable.

**Backend Impact (Tweedledum):**

Client ID priority: (1) User-ID header, (2) X-Forwarded-For (first IP in list, if present), (3) request.client.host (socket IP). No 400 rejection if fallback is needed; all three sources are always available in test environment. In production, reverse proxy config determines X-Forwarded-For trust.
