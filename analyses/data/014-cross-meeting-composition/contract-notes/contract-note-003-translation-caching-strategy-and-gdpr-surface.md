## Contract Note 003: Translation Caching Strategy and GDPR Surface

**State:** agreed
**Contract Version:** v1 (backend maintains 5-minute in-memory cache per message; cache invalidation is automatic on message edit/delete; GDPR surface bounded by TTL)

**Current Shape:**

On-read translation per Cat's proposal; no explicit caching layer mentioned.

**Proposed Change:**

Three options with different GDPR/cost implications: (1) No caching—every read triggers a translator call (high baseline cost, minimal data retention); (2) Short-lived cache (e.g., Redis with 5-minute TTL per message-language pair)—reduces translator calls on re-reads within a conversation, but adds a GDPR-relevant cache surface (what triggers cache expiry? what's the retention liability?); (3) Session-scoped cache (translations live for the duration of a single conversation session, cleared on close)—middle ground, but requires cache-key design that Tweedledum owns. The contract surface is: does the message-envelope include a cache-validity token or version, or is caching transparent to the frontend?

**Source:** Tweedledum's concern: the Cat's proposal doesn't surface the translator-call volume implication of on-read translation or the GDPR cost of caching. This is a design decision, not an implementation detail.

**Frontend Impact (Tweedledee):**

Frontend expects the same message to always show the same translation across reads. If backend caches translations for the conversation lifetime, the frontend doesn't need to handle translation variance. The frontend also needs to know the cache lifetime so it can make deletion assumptions: when a conversation is deleted, are cached translations also deleted? (Yes, if cache lifetime = conversation lifetime.) The contract signal should be implicit on this — backend handles cache cleanup when conversation is deleted; frontend trusts that.

**Backend Impact (Tweedledum):**

Backend maintains an in-memory cache (TTL: 5 minutes) of translation results, keyed by (message_id, target_language). Cache invalidation on message edit or deletion. This keeps translator throughput manageable while bounding GDPR retention surface—the cache is a performance layer, not a data store. Stateless service design; cache is per-instance, not shared, so we accept cache misses on failover.

**Resolution:**

agreed—backend caches for 5 minutes, frontend assumes consistency within that window, GDPR retention is minimal
