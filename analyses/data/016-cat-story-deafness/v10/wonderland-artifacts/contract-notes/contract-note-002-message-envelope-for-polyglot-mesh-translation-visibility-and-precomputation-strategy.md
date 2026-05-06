## Contract Note 002: Message envelope for polyglot mesh: translation visibility and precomputation strategy

**State:** agreed
**Contract Version:** v1 (lazy-on-demand with async workers, retroactive jobs for new-user joins, no eager pre-compute for all-user-preference-pairs)

**Current Shape:**

Message carries original_text and original_language only; translation is not persisted or cached on the message object (per ADR-001 immutability).

**Proposed Change:**

Message envelope must carry visible_translations as a queryable/renderable field to support Marcus's story (polyglot moderator spots translation failure) and Yuki's story (German↔Japanese direct path without English bridge). The change is how translations are surfaced and cached—not changing immutability of original_text.

**Source:** ADR-003 commit to mesh model + stories 002 (Marcus visibility) and 003 (Yuki mesh path)

**Frontend Impact (Tweedledee):**

See Tweedledee's response to contract-note-002.

**Backend Impact (Tweedledum):**

Precomputation strategy: no eager pre-compute for all user-language-pairs. Instead, translations are enqueued asynchronously as messages post; workers handle one (message, target_language) pair per job. DeepL API (per ADR-001) returns one translation per call, so we make sequential calls or batch-enqueue jobs. By render time (~5s SLA for common pairs), most translations are in the JSONB. Uncommon pairs or service slowness: user sees translation_status=pending with loading state. Background retry handles transient failures; permanent failure shows translation_status=failed with original text fallback. No user-facing re-translation button in v1; system guarantees 'we tried; outcome is visible.' Message immutability: original_text is the audit/GDPR record; translations map is computed/updatable without changing the source.

**Resolution:**

Confirmed lazy-on-demand strategy: translations computed asynchronously when message posted (all supported languages), retroactively when new user joins. Background worker FIFO, SLA ~5s common pairs, 3 retries over 5min, status=failed if exhausted. User sees loading state while in flight. Matches Tweedledee's implementation needs; defers all-user-preference pre-compute to v2 optimization. Contract locked; ready for implementation.
