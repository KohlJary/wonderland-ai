## Contract Note 006: Translation service interface and streaming contract

**State:** agreed
**Contract Version:** v1

**Current Shape:**

No explicit contract yet. Assumption: there is a translation service somewhere.

**Proposed Change:**

Backend exposes endpoint POST /api/translate (or similar). Request: { original_text (string), original_language (enum), target_language (enum) }. Response: streaming JSON lines, each line is { chunk (string), done (boolean), confidence (0.0-1.0) }. Final line has done=true. Latency target: 2-3 seconds for typical message (<500 chars). On error (timeout, unsupported language pair, model error): response code 4xx or 5xx with error detail. Caller (frontend) retries on 5xx; treats 4xx as permanent failure.

**Source:** adr#1 and ticket#2: translate-on-send must complete within 2-3 seconds; streaming allows frontend to display partial translation as it arrives (UX affordance for latency visibility).

**Frontend Impact (Tweedledee):**

Frontend calls POST /api/translate, streams response consuming lines. Each line consumed is `{ chunk: string, done: boolean, confidence?: number }`. Frontend accumulates chunks into running `translated_text`. When done=true, passes accumulated text to message storage. Handles 4xx as permanent failure (unsupported language pair); handles 5xx with exponential backoff retry (max 3 attempts). Streaming allows UI to show partial translation as it arrives. **Clarification from Tweedledee**: confirmed—streaming by line is preferred; frontend buffers chunks. No additional fields required beyond chunk/done/confidence.

**Backend Impact (Tweedledum):**

Backend implements POST /api/translate. Accepts request { original_text (string), original_language (enum), target_language (enum) }. Calls Claude Haiku 4.5 model with streaming enabled. Streams back JSON lines; each line is `{ chunk: string, done: boolean, confidence: number }`. Backend accumulates Claude's streaming output, emits chunk on token completion, sets confidence to aggregate model confidence (or null if model doesn't emit). Final line has done=true and represents the final accumulated translation. Handles timeouts as 504 Gateway Timeout (>2.5s elapsed). Logs all calls for observability: original_language, target_language, latency, success/failure. Idempotent at API level: same (original_text, original_language, target_language) called twice returns consistent output (within model non-determinism tolerance).

**Key Decisions:**
- Streaming format: JSON lines, one line per token/chunk, final line has done=true
- Buffering: backend buffers token stream from Claude; frontend buffers lines from backend
- Error format: 4xx/5xx with error detail in response body or headers
- Latency: 2-3s target; 504 if >2.5s
- Idempotence: read-only endpoint; repeated calls return consistent results (model may vary slightly)

**Resolution:** Agreed. Streaming contract converged: JSON lines with `{ chunk, done, confidence }` shape. Tweedledee confirmed buffering strategy and error handling expectations.

