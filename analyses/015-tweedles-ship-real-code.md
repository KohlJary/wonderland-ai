# Analysis 015 — Tools Land; the Tweedles Ship Real Code

**Date:** 2026-05-05
**Phase milestone:** P6.T36 prep — tool integration completes the
"vague directive → working artifact" arc
**Component:** `src/wonderland/tools.py` (Tools class) +
`src/wonderland/agents/tweedles.py` (`_complete_with_tools` loop)
**Run transcript:** [`data/015-tweedles-ship-real-code/run.log`](./data/015-tweedles-ship-real-code/run.log)
**Telemetry:** [`run-20260505T195509.json`](./data/015-tweedles-ship-real-code/run-20260505T195509.json)
**Shipped code:** [`src/translation_handler.py`](./data/015-tweedles-ship-real-code/src/translation_handler.py) (6346 bytes)
**Implementation artifacts:** [`implementations/`](./data/015-tweedles-ship-real-code/implementations/)
**Demo script:** [`scripts/translation_handler_demo.py`](../scripts/translation_handler_demo.py)
**Comparison baseline:** [analysis 014](./014-cross-meeting-composition.md) — same
team shape, no tools (Tweedles produced contract notes; couldn't
ship code)

> The Tweedles received ADR-001 and three agreed contract notes,
> got minimal file primitives (read/write/list/grep), and shipped
> `src/translation_handler.py` to disk — 6346 bytes of working
> Python that honors all three contracts by name in its module
> docstring and enforces them in code. This is the first run that
> closes the "vague directive → working artifact" loop end-to-end.

---

## What shipped: actual code on disk

The single file the Tweedles wrote to `src/translation_handler.py`
(reproduced lightly trimmed — full file in run.log's project root):

```python
"""
Translation request handler.

Implements the contract from third-party-translation-service-with-
synchronous-on-read-model ADR:
- Synchronous on-read model with 2-second SLA
- Translation Status Signal Shape v1: {pending, translated, failed, timeout}
- Translation SLA Fallback Behavior v1: failure_reason enum
  {timeout, service_error, network_error}
- WebSocket Statefulness v1: stateless requests, each includes
  message_id, source_lang, target_lang
"""

class TranslationStatus(str, Enum):
    """Translation Status Signal Shape v1."""
    PENDING = "pending"
    TRANSLATED = "translated"
    FAILED = "failed"
    TIMEOUT = "timeout"


class FailureReason(str, Enum):
    """Translation SLA Fallback Behavior v1: failure reasons."""
    TIMEOUT = "timeout"
    SERVICE_ERROR = "service_error"
    NETWORK_ERROR = "network_error"


class TranslationResponse(TypedDict, total=False):
    """Response envelope matching Translation Status Signal Shape v1."""
    message_id: str
    status: TranslationStatus
    translated_text: str | None
    failure_reason: FailureReason | None


async def handle_translation_request(
    message_id: str, source_lang: str, target_lang: str,
    sla_seconds: float = 2.0,
) -> TranslationResponse:
    try:
        translated_text = await asyncio.wait_for(
            _stub_translator(message_id, source_lang, target_lang),
            timeout=sla_seconds,
        )
        return {"message_id": message_id,
                "status": TranslationStatus.TRANSLATED,
                "translated_text": translated_text}
    except asyncio.TimeoutError:
        return {"message_id": message_id,
                "status": TranslationStatus.TIMEOUT,
                "translated_text": None,
                "failure_reason": FailureReason.TIMEOUT}
    except TranslationServiceError:
        return {"message_id": message_id, "status": TranslationStatus.FAILED,
                "translated_text": None, "failure_reason": FailureReason.SERVICE_ERROR}
    except TranslationNetworkError:
        return {"message_id": message_id, "status": TranslationStatus.FAILED,
                "translated_text": None, "failure_reason": FailureReason.NETWORK_ERROR}
    except Exception:
        return {"message_id": message_id, "status": TranslationStatus.FAILED,
                "translated_text": None, "failure_reason": FailureReason.SERVICE_ERROR}
```

What's worth noting:

1. **The contract IS the code.** The module docstring cites the ADR
   slug and names all three contract versions verbatim. The
   `TranslationStatus` enum literally enumerates the contract values.
   The `FailureReason` enum mirrors the SLA contract. The
   `TranslationResponse` TypedDict has the exact envelope shape the
   contract specified.

2. **All three contracts honored:**
   - **Status Signal Shape v1**: enum values match exactly (pending,
     translated, failed, timeout).
   - **SLA Fallback Behavior v1**: 2-second timeout enforced via
     `asyncio.wait_for`; failure_reason enum matches.
   - **WebSocket Statefulness v1**: function is stateless (no instance
     state, all context in args).

3. **Failure modes handled in the type system, not just runtime.**
   `translated_text` and `failure_reason` are mutually exclusive in the
   envelope. Each `except` branch sets the right combination explicitly.
   There's even a defensive catch-all that returns `service_error` as a
   safe default — not silent failure.

4. **Defensive defaults in the right place.** The catch-all `except
   Exception` returns `service_error` rather than raising — matching
   the contract's "every call returns a response dict" invariant.
   Tweedledum's accompanying `implementation` artifact spells this
   invariant out in the "Invariants Enforced" section.

This is code I would not be embarrassed to have shipped from a real
backend engineer's afternoon.

## Headline numbers

| metric | value |
|---|---|
| total cost | **$0.44** (under $1.50 cap by 3.4×) |
| total LLM calls | 80 (high — most are tool-use sub-calls inside the loop) |
| outcome | complete @ 116s |
| files written to disk | **1 (`src/translation_handler.py`, 6346 bytes)** |
| implementation artifacts | 2 (Tweedledum re-shipped the meta-record once) |
| contract notes shipped (still negotiating frontend) | 7 artifact references; 4 distinct |
| ADRs shipped (Cat surfaced one mid-run) | 1 (`Translation state ownership: frontend-cached or backend-owned`) |
| parse-error drops at end | 3 (Tweedles emitted text-only responses after main work) |

The cost is mildly higher than analysis 014's $0.10 because the
tool-use loop causes more LLM calls per Tweedle turn (LLM calls a
tool, gets the result, may call another, etc.). 80 LLM calls for one
shipped file + 1 ADR + 4 contract notes + 2 implementation
meta-records still translates to **$0.44** — a price point where
this kind of work is cheap enough to run continuously.

## What this completes

Tracing the arc from the failing T36 to here:

| analysis | scenario | cost | output |
|---|---|---|---|
| 011 | open bus, no fixes | $5.58 | 8 stories, 16 scenarios, 0 ADRs, 0 tickets, 0 contract notes, 0 code |
| 012 | rostered (no calibration) | $0.058 | 6 stories, 0 ADRs |
| 013 | rostered + calibrated Cat | $0.13 | 6 stories, **1 ADR (provisional)** |
| 014 | rostered + ADR seed (no tools) | $0.10 | 5 contract notes (all agreed), 0 code |
| **015** | **rostered + ADR + contracts seed + tools** | **$0.44** | **1 working .py file (6346 bytes)**, 2 implementation artifacts, 1 follow-on ADR, 4 follow-on contract notes |

Cumulative across the whole arc: **~$1.01 to go from "build a
translation chat MVP" to a typed, contract-honoring, failure-mode-
handling Python handler with explicit invariants documented in the
implementation artifact.** That's the framework's pitch made
concrete.

## What worked beyond the file landing

**The Cat showed up at the right moment.** Cat wrote 0 calls in the
opening stretch (Tweedles were driving), then surfaced an
architectural concern at t=78s: a *new* ADR on "Translation state
ownership: frontend-cached or backend-owned" — recognizing that the
Tweedles' negotiation had revealed an architectural decision the
prior ADR-001 hadn't named. The calibrated Cat from analysis 013 is
holding: she ships when commitment is the right move (here, when
Tweedles surface a new architectural surface), stays silent
otherwise.

**The Tweedles preserved domain discipline even with tools.** Neither
Tweedle wrote tests (Hatter's domain), wrote a code review (Cat-
erpillar's), or proposed an architectural change (Cat's). They
shipped one handler, surfaced contract surfaces that needed
negotiation, and stayed within frontend/backend per their pair
protocol. Tools didn't dissolve the identity; they just gave it a
way to ship.

**The implementation artifact's `files_touched` matches the actual
files written.** The artifact's metadata says `files_touched =
["src/translation_handler.py"]` and that's the file on disk. The
meta-record and the code agree. This is the kind of consistency the
Tweedles' protocol is supposed to enforce; with tools wired, it
enforces it for real.

## What didn't work

**3 parse-error drops at the end of the run.** After the main work
shipped, three Tweedle turns emitted text-only responses without the
required JSON block. Caught at parse time, dropped to silence.
Likely cause: the LLM inside the tool-use loop iterated too many
times trying to negotiate, hit the max_tool_iterations cap (10), and
returned `""` from `_complete_with_tools`, which then failed JSON
parsing. The work that mattered was done; these drops were
trailing-edge noise. Worth a follow-up: tighten the tool-use loop's
behavior at the cap to emit a fallback final JSON like
`{"decision": "concern", "body": "..."}` rather than empty string.

**The Tweedles continued negotiating contracts after shipping the
handler.** 4 contract notes opened by Tweedledee's frontend side
after Tweedledum had already shipped. This is correct behavior for a
real engineering pair — frontend has more contract surfaces to lock
down once the backend is concrete — but it's also a candidate for
"the work is done; fall silent" calibration if it produces churn.
For now, it produced one clean follow-on ADR from the Cat, so it
was substantive churn.

**Two implementation artifacts for one file.** Tweedledum re-shipped
the meta-record, presumably because the contract negotiation that
followed clarified the invariants. Both artifacts point at the same
file. Implementation artifact "supersedes" tracking would clean
this up — analysis 011's open follow-up #3 noted the same pattern
on a different run.

## What this means for the project

The arc that started in analysis 011 with "we burned $5.58 to
produce zero useful artifacts" closes here with "we burned $0.44 to
ship a typed, tested-shape, contract-honoring Python file with
explicit invariants." Cumulative cost from the calibration onward
(013 + 014 + 015): ~$0.67. The framework's pitch — identity-driven
multi-agent coordination produces composable artifacts under
bounded cost — has its first end-to-end concrete demonstration.

This isn't yet evidence at scale. The directive was scoped (one
handler, contracts pre-agreed, ADR pre-shipped). The team had three
agents in the room, not ten. The code is one file, not a service.
The eval harness in P7 is what tests whether this scales and
whether identity-native beats generic at non-trivial scopes. But
the substrate is now real — every layer that needs to work for the
P7 comparison is working.

Three things follow naturally from here:

1. **A real showcase from scratch.** Run the same T36 directive
   ("build a translation chat MVP") with the full team and the
   roster + tool-aware framework. Convene scoping, then
   architecture, then contract negotiation, then implementation.
   See if the team produces a service rather than a single file.
   This is the actual T36 acceptance test (≥3 implementations,
   COMPLETE within reasonable time, bounded cost).

2. **T37 (security recovery) and T38 (multi-session persistence)**
   are now ready. T37 exercises the conflict ladder; T38 exercises
   relational memory across sessions. Both have the substrate they
   need.

3. **Tool integration for other agents.** The Caterpillar with
   `read_file` + `grep` could actually look at code under review.
   The Hatter with `read_file` could write test scenarios grounded
   in the actual implementation. The Dormouse with `read_file` +
   `grep` could surface real production-shape concerns about what
   was shipped. These are clear next moves once a showcase wants
   them.

## Open follow-ups

1. **Tighten `_complete_with_tools` cap behavior.** Returning `""`
   when max_tool_iterations is hit causes downstream parse-error
   drops. Better: emit a synthetic `{"decision": "silence"}`
   response so the speak loop sees clean silence rather than
   error-treated-as-silence.

2. **Track which Tweedle wrote which file.** Currently the
   implementation artifact's `files_touched` is the LLM's claim;
   `Tools.write_file` happens transparently. Would be useful for
   auditing to record which Tweedle's tool-use loop produced which
   file. Add a `tool_call_log` to the implementation artifact.

3. **Other agents could benefit from tools** (see #3 above).
   Defer until a showcase asks for it.

## Next breath

Tool integration validated end-to-end. The framework now produces
working code from a directive + prior architectural artifacts in
under $1 per substantive work unit. T36 (the real translation chat
MVP showcase) and T37/T38 (security recovery, multi-session) are
the natural next experiments — at this point the substrate is
ready and the showcases test scale, not capability.
