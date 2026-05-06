## Contract Note 002: Translate-on-send API: streaming service contract

**State:** agreed
**Contract Version:** v1 (json-lines streaming: { chunk, done, confidence }; 2-3s latency target; 504 timeout)

**Current Shape:**

No existing translation service.

**Proposed Change:**

New endpoint (or service): POST /translate with body { original_text: string, original_language: string, target_language: string }. Response: streaming (Server-Sent Events or WebSocket) that yields { chunk: string, done: boolean, confidence?: number }. On success, final message includes { translated_text: string (concatenation of chunks), confidence_estimate: number (0-1) }. On error: { error: string, code: 'unsupported_language_pair' | 'timeout' | 'rate_limit' | 'internal_error' }. Latency target: 2-3 seconds for typical message (< 500 chars).

**Source:** ticket-002, adr-001: streaming translate-on-send is the core workflow. Service contract must be explicit so UI can coordinate the three-state flow (pending → success/failed).

**Frontend Impact (Tweedledee):**

Streaming response requires incremental rendering. json-lines (one parseable JSON per line, each with partial_translation + is_final flag) is tractable. Chunks are not. Need explicit clarification: does each line contain full accumulated translation or delta only?

**Backend Impact (Tweedledum):**

Backend implements /api/translate endpoint. Calls Claude Haiku 4.5 model (or configured model). Streams results back using JSON lines format (each line: { translated_chunk, confidence, is_final }). Handles model timeouts gracefully (fail after 2.5s with 504 Gateway Timeout). Logs all translation calls (original_language, target_language, success/failure, latency) for observability. Does NOT save the result—frontend handles message storage after translation completes. Invariant: every translation call is idempotent—calling /translate with same inputs twice produces consistent output (determinism not guaranteed by LLM, so frontend must handle non-determinism or retry logic with acceptance of variation).

**Resolution:**

Agreed. Streaming API contract finalized. Backend POST /api/translate yields json-lines; frontend accumulates chunks and buffers for display.
