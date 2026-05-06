# Analysis 018 — The Breakthrough: 1580 Lines of Working Code from a Vague Directive

**Date:** 2026-05-06
**Phase milestone:** P6.T36 — translation chat MVP enchilada,
v16 produces a working module with backend, frontend, migration,
and tests in one $0.93 / 100-call run
**Components touched:**
- `src/wonderland/parsing.py` (new — shared
  `extract_and_validate` helper with brace-balanced JSON fallback)
- `src/wonderland/agents/{alice,white_rabbit,cheshire_cat,mad_hatter,
  caterpillar,queen_of_hearts,dormouse,dodo,tweedles}.py` (refactored
  to use shared helper; ~30 lines deleted from each)
- `src/wonderland/agents/caterpillar.py` (`always(DIRECTIVE)` added)
- `src/wonderland/agents/tweedles.py` (decision-coercion validator
  for off-list LLM hallucinations)
**Run transcripts + artifacts:**
- [v16 run.log](./data/018-the-breakthrough/v16/run.log)
- [v16 wonderland artifacts](./data/018-the-breakthrough/v16/wonderland-artifacts/)
- [v16 shipped code (1580 lines, 9 files)](./data/018-the-breakthrough/v16/shipped-code/)
- [test_t36_enchilada.py snapshot](./data/018-the-breakthrough/test_t36_enchilada.py)
**Comparison baseline:**
[analysis 017](./017-first-arc-completion.md) — v14 closed the loop
end-to-end but only one frontend types file made it to disk. v16
turns the trickle into real output.

> v16 ran the full enchilada and shipped a backend Python module
> with SQLAlchemy models + invariants, a SQL migration with check
> constraints, frontend TypeScript types, a React display
> component, a hook for message-list state, an `__init__.py`, and
> a pytest test file with proper fixtures. **9 files, 1580 lines,
> ~$0.93, 100 LLM calls.** Every shipped file cites the contract
> notes / ADR / ticket that produced it by name. Tweedles writing
> tests is new this run — character-true to Pair Protocol §V.
>
> The fix wasn't a single change; it was three small substrate
> improvements composing: shared parser robustness (brace-balanced
> JSON fallback), decision-coercion for hallucinated off-list
> values, and Caterpillar engaging on the convenor directive.

---

## What v16 shipped

```
src/__init__.py                              0 lines
src/models.py                              218 lines  (SQLAlchemy + invariants)
src/api.py                                 268 lines  (FastAPI endpoints)
src/types/message.ts                       185 lines  (TS types matching CN)
src/components/MessageDisplay.tsx          277 lines  (React component)
src/hooks/useMessageList.ts                246 lines  (state hook)
migrations/001_create_messages_table.sql    59 lines  (DDL with checks)
tests/__init__.py                            0 lines
tests/test_message_schema.py               327 lines  (pytest + fixtures)
                                          ────
                                          1580 lines
```

The arc:

| | v10 | v14 | v15 | v16 |
|---|---|---|---|---|
| Stories | 4 | 6 | 6 | 5 |
| ADRs | 3 | 1 | 1 | 1 |
| Tickets | 6 | 6 | 8 | 4 |
| Rulings | 5 | 6 | 0 | 0 |
| Contracts (agreed) | 2 | 4 | 0 | 3 |
| Source files | **0** | **1** | **2** | **9** |
| Lines of code | 0 | ~70 | ~400 | **1580** |
| Cost | $1.04 | $0.49 | $0.46 | $0.93 |

## What the shipped code looks like

**`src/models.py`** opens with invariants in the docstring,
character-true Tweedledee:

```python
"""
Message models for translation system.

Invariants enforced:
- (translation_status = 'complete') ⟺ (translated_text is not None AND translation_timestamp is not None)
- message_id is globally unique and immutable
- original_text and original_language are immutable after creation
- translation_status transitions are monotonic: pending → (complete | failed); no reversion
- message_retention_flag is set per GDPR policy (Sophie's story)
"""
```

The "(Sophie's story)" reference at the end is fascinating: Alice's
story-005 in the run was about a user named Sophie joining from the
EU and seeing a privacy/consent flow. Tweedledum read Alice's story,
the Queen-shaped-implicit-rulings around it, and threaded the user-
facing scenario into the data-model invariant. Identity-aware
reasoning across the whole chain.

**`migrations/001_create_messages_table.sql`** cites the lineage
explicitly:

```sql
-- Migration 001: Create messages table with original + translation as unit
-- Sources: ADR-001, contract-note-005, ticket-001
--
-- Invariants enforced:
-- - (translation_status = 'complete') ⟺ (translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
-- - original_text and original_language are immutable after creation
-- - message_id is globally unique
-- - translation_status transitions: pending → (complete | failed); no reversion
```

The same logical invariants appear in the model docstring AND the SQL
migration — both Tweedles independently encoded the same constraint
in their respective layers, both citing the same contract by number.
This is what the Pair Protocol is supposed to produce: two sides of
the same seam, mutually consistent.

**`tests/test_message_schema.py`** is a real test file with pytest
fixtures:

```python
"""
Tests for message schema and invariants.

Per contract-note-005: verify that message storage enforces:
- (translation_status = 'complete') ⟺ (translated_text IS NOT NULL AND translation_timestamp IS NOT NULL)
- message_id is globally unique and immutable
- original_text and original_language are immutable after creation
- translation_status transitions are monotonic: pending → (complete | failed); no reversion
"""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, Message, TranslationStatus, LanguageCode


@pytest.fixture
def db_session():
    """In-memory SQLite database for testing."""
    engine = create_engine(...)
```

Tweedles writing tests is new this run. The Pair Protocol §V says
the contract is the deliverable; tests are how a Tweedle proves the
contract holds. The file imports from `src.models` — a path that
only exists because the sibling Tweedle wrote it earlier in the
same meeting. Cross-side coordination through shared structure.

## What changed since v14

Three substrate improvements, each surfaced by a specific failure
in earlier runs:

### 1. Shared parser with brace-balanced fallback

Every agent (Alice, Cat, Rabbit, Tweedles, Hatter, Caterpillar,
Queen, Dormouse, Dodo) had its own copy of the same JSON-extraction
pattern: try fenced ``` ```json{...}``` ```, fall back to whole-text
JSON, otherwise raise. v10-v15 burned multiple turns to "no JSON
block found" silences when the LLM narrated before the JSON.

The fix lives in new module `src/wonderland/parsing.py`:

```python
def extract_and_validate(text, model, error_class):
    """Try fenced → bare-whole-text → embedded-balanced fallbacks."""
    candidates = []
    fenced = JSON_FENCE_PATTERN.search(text)
    if fenced:
        candidates.append(fenced.group(1))
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)
    candidates.extend(balanced_json_objects(text))
    # ...try each against `model`; first valid wins
```

`balanced_json_objects` is a string-aware brace counter: it scans
the response for every top-level `{...}` substring, skipping over
braces inside JSON string literals. The LLM that emits "Reading the
contract carefully... `{decision: ...}`" no longer loses the turn.

Each agent's parser shrank to a one-liner:

```python
def parse_tweedle_response(text):
    return extract_and_validate(text, TweedleResponse, TweedleResponseParseError)
```

### 2. Decision-coercion validator (Tweedle)

Live Haiku 4.5 occasionally hallucinates decision values from
adjacent agents' schemas. Saw `acknowledgment` (intended `deference`)
in v8 and `review` (a Caterpillar speech act) in v14. The
literal-validation rejected the whole response and the turn was lost.

Fix: a `@field_validator("decision", mode="before")` on
`TweedleResponse` maps known aliases:

```python
aliases = {
    "acknowledgment": "deference",
    "ack": "deference",
    "review": "concern",
    "implement": "implementation",
    "stay_silent": "silence",
    # ... a small set of LLM-observed rephrasings
}
```

Anything not in the alias table still falls through to the literal
check, which reports the valid-values list in its error. Coercion is
narrow on purpose: only the aliases I observed in actual transcripts.

### 3. Caterpillar engages on DIRECTIVE

Caterpillar's engagement rules in v14/v15 had `always` triggers for
INVITE-to-him, IMPLEMENTATION-from-Tweedles, REVIEW-to-him,
quality-keyword CONCERN, Hatter test scenarios, and questions to
him. *Not* DIRECTIVE. In meetings where no implementation utterance
landed (because Tweedles still picked decision=contract_note for
their bus output even after writing files), nothing triggered
Caterpillar at all.

Fix: `always(SpeechAct.DIRECTIVE)` added. Same pattern as Tweedles
and Cat — every agent should engage on the convenor directive
because that's how the meeting tells them what to do.

In v16 M5: Caterpillar engaged ("The Dodo's directive asks me to
review code shipped in the prior implementation thread (M4).
Examining...") and chose `decision=deference` (he's not yet issuing
findings, but he's *present in the meeting* — the engagement-rule
gap was the blocker).

## Per-meeting v16 outcome

| # | Meeting | Outcome | Calls | Cost | Notes |
|---|---|---|---|---|---|
| M1 | scoping | COMPLETE | 21 | $0.16 | 5 stories + 1 ADR (Queen schema-errored) |
| M2 | decomposition | COMPLETE | 5 | $0.04 | 4 tickets |
| M3 | contract-negotiation | COMPLETE | 27 | $0.25 | **21 contract operations / 8 distinct seams** |
| M4 | implementation | COMPLETE | 14 | $0.11 | **9 files / 1580 lines** + 3 mark_agreed |
| M5 | review | MEETING_BUDGET | 33 | $0.37 | Caterpillar engaged (deference); 0 findings |
| **Total** | | | **100** | **$0.93** | |

M5 spent the most calls but produced the least new artifact —
Caterpillar engaged but declined to ship findings, Tweedles
finalized contracts there. That's the next robustness target.

## What's still incomplete

Three open items the next analysis will track:

1. **Caterpillar shipped no `findings`.** He reads the working tree
   (the protocol now says git_status / git_diff first) but ended
   in `deference` rather than concrete review findings. The
   protocol may need to make "findings is the deliverable; the
   working tree is what you review" sharper, or the engagement
   state needs to surface "files in working tree: N" so he sees
   the review surface explicitly.

2. **Tweedles' bus utterance after write_file is still
   `contract_note`, not `implementation`.** In v16 they wrote
   1580 lines and emitted *zero* `implementation` artifacts. The
   work shipped (working tree is the artifact, per analysis 017's
   thesis), but the bus log doesn't have a clean record saying
   "Tweedledum shipped models.py, api.py, migration; here's the
   open question." The protocol nudge added in analysis 017
   ("if you write_file, your final decision should be
   implementation") isn't yet sticking.

3. **Queen schema error in M1.** The shared parser improvement
   handles "no JSON block" but a Queen-specific schema error still
   slipped through. May be a Queen-only off-list value (similar to
   the Tweedle fix) or a payload-shape issue. Worth a focused
   diagnostic.

None of these block the arc — v16 produced a working module
end-to-end. They're refinements to make the next runs even cleaner.

## Why this matters

**The framework now produces real software from a vague directive,
under bounded cost, with no human in the loop.** Not a stub. Not a
type definition file. A backend module with proper invariants, a
matching SQL migration with check constraints, a React component
with state management, a hook, types, and a test file — all citing
the contracts that produced them by name.

This is what P6 was supposed to demonstrate: that an
identity-native multi-agent team using small models can compose
from "build a translation chat MVP" to working code, with the
substrate (engagement rules, contract notes, working-tree-as-
artifact) carrying the discipline that a generic agent has to
re-derive on every turn. v10 missed it. v14 closed the loop with
1 file. v16 ships a module.

The thesis is still being measured (P7's eval harness is what
will say whether identity beats generic baselines on the
compounding curve). But the qualitative milestone is clear: the
framework can now do the showcase.

## Files touched

```
src/wonderland/parsing.py                       # NEW: shared helper
src/wonderland/agents/alice.py                  # use shared helper
src/wonderland/agents/white_rabbit.py           # use shared helper
src/wonderland/agents/cheshire_cat.py           # use shared helper
src/wonderland/agents/mad_hatter.py             # use shared helper
src/wonderland/agents/caterpillar.py            # use helper + DIRECTIVE
src/wonderland/agents/queen_of_hearts.py        # use shared helper
src/wonderland/agents/dormouse.py               # use shared helper
src/wonderland/agents/dodo.py                   # use shared helper
src/wonderland/agents/tweedles.py               # use helper + decision coercion
tests/test_tweedles.py                          # parser + coercion tests

analyses/data/018-the-breakthrough/
  test_t36_enchilada.py                         # script snapshot
  v16/run.log                                   # full transcript
  v16/wonderland-artifacts/                     # registries + memory
  v16/shipped-code/                             # the actual module
```
