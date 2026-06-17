"""Tests for WonderlandAgent — the base class for every character."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from wonderland import (
    AgentIdentity,
    AgentMemory,
    CachedBlock,
    Context,
    InMemoryCaucus,
    SpeechAct,
    Utterance,
    UtteranceContent,
    WonderlandAgent,
    format_transcript,
    format_utterance,
    load_constitution,
)
from wonderland.identity import (
    ConstitutionHeader,
    Identity,
)
from wonderland.llm import LLMClient
from wonderland.parsing import ResponseParseError, extract_and_validate

# ---------- helpers ----------


def _make_identity(
    name: str = "cheshire_cat",
    interests: frozenset[SpeechAct] | None = None,
) -> Identity:
    return Identity(
        name=name,
        header=ConstitutionHeader(
            display_name=name,
            role="r",
            lineage="Wonderland v0.1",
            version="0.1",
            license="MIT",
        ),
        constitution_text=f"You are {name}.",
        interests=interests if interests is not None else frozenset(SpeechAct),
    )


def _utterance(
    *,
    thread_id: str = "t",
    speaker: str = "white_rabbit",
    act: SpeechAct = SpeechAct.PROPOSAL,
    body: str = "...",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=act,
        content=UtteranceContent(body=body),
    )


async def _agent(
    tmp_path: Path,
    *,
    identity: Identity | None = None,
) -> WonderlandAgent:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    await memory.open()
    return WonderlandAgent(
        identity=identity or _make_identity(),
        memory=memory,
        bus=bus,
    )


# ---------- transcript helpers ----------


def test_format_utterance_includes_speaker_and_act() -> None:
    u = _utterance(speaker="cat", act=SpeechAct.PROPOSAL, body="...")
    out = format_utterance(u)
    assert "[cat — proposal]" in out
    assert "..." in out


def test_format_transcript_joins_with_blank_line() -> None:
    a = _utterance(speaker="A", body="first")
    b = _utterance(speaker="B", body="second")
    out = format_transcript([a, b])
    assert out == f"{format_utterance(a)}\n\n{format_utterance(b)}"


def test_format_transcript_empty() -> None:
    assert format_transcript([]) == ""


def test_format_transcript_preserves_order() -> None:
    """Caller is responsible for chronological order; transcript honors it."""
    a = _utterance(body="A")
    b = _utterance(body="B")
    c = _utterance(body="C")
    forward = format_transcript([a, b, c])
    reverse = format_transcript([c, b, a])
    assert forward.index("A") < forward.index("B") < forward.index("C")
    assert reverse.index("C") < reverse.index("B") < reverse.index("A")


# ---------- T-ab24a context-size instrumentation ----------


def test_log_context_size_silent_under_threshold(caplog) -> None:
    """Small prompts shouldn't spam the log — instrumentation only
    fires above 30K tokens (INFO) or 100K (WARN). A normal first-
    turn deliberation easily fits below 30K."""
    import logging
    from wonderland.agent import _log_context_size

    ctx = Context(
        constitution="You are X.",
        relationships="",
        current_thread="",
        triggers=(),
        engagement_state="",
    )
    with caplog.at_level(logging.INFO, logger="wonderland.context_size"):
        _log_context_size("tweedledee", [], ctx)
    assert len(caplog.records) == 0


def test_log_context_size_warns_above_100k_tokens(caplog) -> None:
    """T-ab24a: context approaching Claude's 200K cap should fire a
    WARN with the per-layer breakdown so operators can see which
    layer is driving inflation (mvp-demo-rerun-A: thread_history
    grew to ~170K after N iterations on the same feature, crashing
    every implement attempt)."""
    import logging
    from wonderland.agent import _log_context_size

    # ~500K chars at 4 chars/token = ~125K tokens — above the 100K
    # WARN threshold.
    huge_thread = "x" * 500_000
    ctx = Context(
        constitution="c",
        relationships="r",
        current_thread=huge_thread,
        triggers=(),
        engagement_state="e",
    )
    with caplog.at_level(logging.INFO, logger="wonderland.context_size"):
        _log_context_size("tweedledum", [], ctx)

    records = [
        r for r in caplog.records if r.name == "wonderland.context_size"
    ]
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    msg = records[0].getMessage()
    # Per-layer breakdown is in the message
    assert "tweedledum" in msg
    assert "thread_history=125000" in msg
    assert "total~=125" in msg  # total is ~125003


def test_log_context_size_info_between_30k_and_100k(caplog) -> None:
    """Between the 30K floor and the 100K WARN: INFO-level visibility
    for steady-state monitoring without alarming the operator."""
    import logging
    from wonderland.agent import _log_context_size

    # ~200K chars at 4 chars/token = ~50K tokens
    moderate_thread = "x" * 200_000
    ctx = Context(
        constitution="c",
        relationships="r",
        current_thread=moderate_thread,
        triggers=(),
        engagement_state="e",
    )
    with caplog.at_level(logging.INFO, logger="wonderland.context_size"):
        _log_context_size("alice", [], ctx)

    records = [
        r for r in caplog.records if r.name == "wonderland.context_size"
    ]
    assert len(records) == 1
    assert records[0].levelno == logging.INFO


# ---------- T-ab24b thread_history truncation ----------


def _seed_utt(body: str = "seed") -> Utterance:
    """Seed utterance (is_seed=True) for budget-preservation tests."""
    u = _utterance(body=body)
    return u.model_copy(update={"is_seed": True})


def test_budget_thread_history_passes_through_under_budget() -> None:
    """Under budget, history is returned unchanged with zero
    dropped — no overhead for the healthy path."""
    from wonderland.agent import _budget_thread_history

    history = [_utterance(body="small")] * 10
    kept, dropped = _budget_thread_history(history, budget_chars=100_000)
    assert dropped == 0
    assert kept == history


def test_budget_thread_history_preserves_first_k_and_recent() -> None:
    """T-ab24c: over budget, keep first-K (priming/framing) +
    newest fit-in-budget. Drop the middle. Seed-ness is irrelevant
    to the truncation — meeting framing is at the start of the
    thread regardless of how seed-flagging happened."""
    from wonderland.agent import _budget_thread_history, _PRIMING_KEEP

    # First _PRIMING_KEEP utterances are small (priming). Then a
    # big middle of ~5000-char utterances. Then a few small recent
    # ones. Budget should preserve priming + most-recent.
    priming = [_utterance(body=f"prime{i}") for i in range(_PRIMING_KEEP)]
    middle = [_utterance(body=f"{chr(65+i)}" * 5000) for i in range(6)]
    recent = [_utterance(body=f"recent{i}") for i in range(3)]
    history = priming + middle + recent

    # Budget = priming (~10 × 100 = 1000) + recent (3 × 100 = 300) + headroom
    # for 0-1 middle entries. Set tight enough to drop most middle.
    kept, dropped = _budget_thread_history(history, budget_chars=3000)

    # All priming preserved
    for p in priming:
        assert p in kept
    # All recent preserved
    for r in recent:
        assert r in kept
    # Most or all middle dropped
    middle_kept = [u for u in middle if u in kept]
    assert len(middle_kept) <= 1
    assert dropped >= 5


def test_budget_thread_history_handles_seed_heavy_threads() -> None:
    """T-ab24c regression: mvp-demo-rerun-A had a thread with 2165
    seed utterances and 4 non-seeds. T-ab24b's "preserve all seeds"
    rule kept everything; T-ab24c treats them equivalently so
    truncation actually shrinks the rendered context."""
    from wonderland.agent import _budget_thread_history, _PRIMING_KEEP

    # Simulate the shape: many seeds at the start (re-published from
    # prior threads via Runner.convene), each ~2000 chars, plus a
    # handful of recent non-seeds.
    seeds = [_seed_utt(body="S" * 2000) for _ in range(50)]
    non_seeds = [_utterance(body="recent") for _ in range(4)]
    history = seeds + non_seeds

    # Total ≈ 50 × 2080 + 4 × 86 = ~104K chars. Budget 30K should
    # force aggressive truncation.
    kept, dropped = _budget_thread_history(history, budget_chars=30_000)

    # First _PRIMING_KEEP seeds preserved (priming)
    assert kept[:_PRIMING_KEEP] == seeds[:_PRIMING_KEEP]
    # Recent non-seeds preserved
    for r in non_seeds:
        assert r in kept
    # Most middle seeds dropped — kept length much less than original
    assert len(kept) < len(history) * 0.5
    assert dropped > 0


def test_budget_thread_history_drops_tail_when_priming_overflows() -> None:
    """Edge case: even the first-K (priming) exceeds budget.
    Keep priming + drop everything after. Operator-investigatable;
    Stage 3 (LLM summarization) would handle this gracefully."""
    from wonderland.agent import _budget_thread_history, _PRIMING_KEEP

    big_priming = [_utterance(body="X" * 8000) for _ in range(_PRIMING_KEEP)]
    tail = [_utterance(body="t") for _ in range(3)]
    history = big_priming + tail

    kept, dropped = _budget_thread_history(history, budget_chars=5000)

    assert kept == big_priming  # priming preserved despite oversized
    assert dropped == 3  # all tail dropped


# ---------- T-ab25a memory_scope ----------


async def test_compose_context_all_scope_includes_seeds(tmp_path) -> None:
    """memory_scope='all' (default): thread transcript includes
    seeded + non-seeded utterances. Original behavior."""
    agent = await _agent(tmp_path)
    thread_id = "test-thread-scope-all"
    seed = _utterance(thread_id=thread_id, body="seed body").model_copy(
        update={"is_seed": True}
    )
    fresh = _utterance(thread_id=thread_id, body="fresh body")
    await agent.memory.episodic.record(seed)
    await agent.memory.episodic.record(fresh)

    trigger = _utterance(thread_id=thread_id, body="trigger")
    ctx = await agent.compose_context([trigger], memory_scope="all")
    assert "seed body" in ctx.current_thread
    assert "fresh body" in ctx.current_thread


async def test_compose_context_meeting_only_scope_excludes_seeds(
    tmp_path,
) -> None:
    """T-ab25a: memory_scope='meeting_only' drops seed utterances.
    The thread transcript shows only what happened in THIS meeting,
    not accumulated context re-published from prior threads. The
    fix that unblocks mvp-demo-rerun-A's broken implement: 2165
    seeds dropped, only non-seeds rendered."""
    agent = await _agent(tmp_path)
    thread_id = "test-thread-scope-meeting"
    seed = _utterance(thread_id=thread_id, body="seed body").model_copy(
        update={"is_seed": True}
    )
    fresh = _utterance(thread_id=thread_id, body="fresh body")
    await agent.memory.episodic.record(seed)
    await agent.memory.episodic.record(fresh)

    trigger = _utterance(thread_id=thread_id, body="trigger")
    ctx = await agent.compose_context([trigger], memory_scope="meeting_only")
    assert "seed body" not in ctx.current_thread
    assert "fresh body" in ctx.current_thread


async def test_t_ab52_compose_context_honors_inheritance_chain(tmp_path) -> None:
    """T-ab52: compose_context must scope its recall to the active
    branch's inheritance chain, NOT all branches.

    obol-260522-1 measured 72 cross-milestone utterances leaking
    into M6's design recall via shared ``thread_id='scoping'`` —
    T-ab8 set up per-milestone write isolation but agent.py:732
    called query_by_thread without ``branches=``, so reads pulled
    from every branch. This test pins the fix: when the active
    branch is ``design:m6``, utterances under
    ``design:m5`` on the same thread_id must NOT appear in the
    rendered thread transcript.
    """
    from wonderland.memory.episodic import (
        set_active_branch_id,
        reset_active_branch_id,
    )

    agent = await _agent(tmp_path)
    thread_id = "scoping"

    # Plant an utterance from a "sibling milestone" branch.
    sibling_token = set_active_branch_id("design:m5-sibling")
    try:
        sibling = _utterance(
            thread_id=thread_id, body="sibling milestone leak"
        )
        await agent.memory.episodic.record(sibling)
    finally:
        reset_active_branch_id(sibling_token)

    # Plant an utterance from the "active milestone" branch.
    active_token = set_active_branch_id("design:m6-active")
    try:
        m6_utt = _utterance(
            thread_id=thread_id, body="active milestone content"
        )
        await agent.memory.episodic.record(m6_utt)

        # compose_context with the m6 branch active. Without T-ab52
        # the rendered transcript pulls BOTH utterances; with the
        # fix it pulls only m6's (plus project, but we wrote
        # nothing there).
        trigger = _utterance(thread_id=thread_id, body="trigger")
        ctx = await agent.compose_context([trigger])
    finally:
        reset_active_branch_id(active_token)

    assert "active milestone content" in ctx.current_thread
    assert "sibling milestone leak" not in ctx.current_thread, (
        "compose_context leaked an utterance from a sibling "
        "milestone branch — inheritance_chain not being honored on "
        "the recall query"
    )


def test_phase_spec_rejects_invalid_memory_scope() -> None:
    """Substrate-level validator: PhaseSpec only accepts known
    memory_scope values. Typos / future renames should fail loud
    at workflow-load time, not silently default to ``all``."""
    from wonderland.workflow import PhaseSpec

    PhaseSpec(name="implement", memory_scope="all")
    PhaseSpec(name="implement", memory_scope="meeting_only")
    try:
        PhaseSpec(name="implement", memory_scope="bogus")
    except Exception as e:
        assert "memory_scope" in str(e)
    else:
        raise AssertionError("expected ValueError for unknown memory_scope")


def test_phase_spec_default_memory_scope_is_all() -> None:
    """Backwards compat: phases that don't declare memory_scope
    default to 'all' (original behavior)."""
    from wonderland.workflow import PhaseSpec

    spec = PhaseSpec(name="implement")
    assert spec.memory_scope == "all"
    phase_def = spec.to_phase_definition()
    assert phase_def.memory_scope == "all"


async def test_compose_context_drops_nudges_from_thread_history(
    tmp_path,
) -> None:
    """T-ab27: Dodo's priority-window-open nudges are pure
    scaffolding — they don't carry semantic content the agent
    benefits from re-reading. compose_context filters them out so
    the rendered transcript stays focused on real deliberation.
    Storage is preserved (audit trail); only the agent's view is
    cleaned. Future-proofed by speech_act (not speaker) so any
    framing nudges from other characters get the same treatment."""
    agent = await _agent(tmp_path)
    thread_id = "test-thread-nudge-filter"

    # A real deliberation utterance + a Dodo nudge in the same thread
    real_utt = _utterance(
        thread_id=thread_id, body="real proposal content",
        act=SpeechAct.PROPOSAL,
    )
    dodo_nudge = _utterance(
        thread_id=thread_id,
        speaker="dodo",
        body="**Priority window — phase: implement.** It is your turn to act.",
        act=SpeechAct.NUDGE,
    )
    await agent.memory.episodic.record(real_utt)
    await agent.memory.episodic.record(dodo_nudge)

    trigger = _utterance(thread_id=thread_id, body="trigger")
    ctx = await agent.compose_context([trigger], memory_scope="all")

    assert "real proposal content" in ctx.current_thread
    assert "Priority window" not in ctx.current_thread
    assert "It is your turn to act" not in ctx.current_thread


def test_truncation_banner_mentions_count_and_strategy() -> None:
    """Banner gives agents enough signal to know they're seeing a
    truncated transcript and what was kept."""
    from wonderland.agent import _truncation_banner

    b = _truncation_banner(42)
    assert "42" in b
    assert "elided" in b.lower() or "truncat" in b.lower()
    assert "seed" in b.lower()
    assert "recent" in b.lower()


# ---------- Context ----------


def test_context_to_llm_request_caches_constitution() -> None:
    from wonderland.primer import FRAMEWORK_PRIMER

    ctx = Context(constitution="You are X.")
    system, messages = ctx.to_llm_request()
    # Framework primer is a plain string (gets cached as part of the
    # constitution-prefix); constitution is the first CachedBlock.
    # Context-compression Lever A traded the framework's own
    # breakpoint slot for a current_thread breakpoint slot to stay
    # under Anthropic's 4-cache-breakpoint limit per request.
    assert system == [
        FRAMEWORK_PRIMER,
        CachedBlock("You are X."),
    ]
    assert messages == [{"role": "user", "content": "(no trigger)"}]


def test_context_to_llm_request_caches_relationships_when_present() -> None:
    from wonderland.primer import FRAMEWORK_PRIMER

    ctx = Context(constitution="You are X.", relationships="Tweedles overengineer.")
    system, _ = ctx.to_llm_request()
    assert system == [
        FRAMEWORK_PRIMER,
        CachedBlock("You are X."),
        CachedBlock("Tweedles overengineer."),
    ]


def test_context_to_llm_request_caches_current_thread() -> None:
    """Context-compression Lever A: current_thread becomes a
    CachedBlock so within a single agent emission's tool-use loop
    (~27 LLM calls per emission in mvp-demo2 M7 telemetry), the
    transcript hits cache reads at $0.10/MTok instead of being
    re-billed at $1/MTok uncached input on every round-trip.
    """
    ctx = Context(
        constitution="You are X.",
        relationships="rels",
        current_thread="thread snapshot",
    )
    system, _ = ctx.to_llm_request()
    # All system parts after the framework primer are CachedBlocks,
    # including current_thread (the key behavioral change).
    assert isinstance(system[-1], CachedBlock)
    assert system[-1].text == "thread snapshot"
    # Total breakpoint count: constitution + relationships + thread
    # = 3 CachedBlocks. Framework primer is a plain string. With
    # Tweedle protocol inserted at index 2 we'd have 4, exactly the
    # Anthropic max — see Tweedle agent for that case.
    cached_count = sum(1 for s in system if isinstance(s, CachedBlock))
    assert cached_count == 3, (
        f"expected 3 cache breakpoints (constitution + relationships + "
        f"current_thread); got {cached_count}"
    )


def test_context_to_llm_request_formats_triggers_into_user_message() -> None:
    u = _utterance(speaker="rabbit", act=SpeechAct.TICKET, body="implement X")
    ctx = Context(constitution="C", triggers=(u,))
    _, messages = ctx.to_llm_request()
    assert messages[0]["role"] == "user"
    assert "[rabbit — ticket]" in messages[0]["content"]
    assert "implement X" in messages[0]["content"]


def test_context_to_llm_request_joins_multiple_triggers() -> None:
    a = _utterance(body="A")
    b = _utterance(body="B")
    ctx = Context(constitution="C", triggers=(a, b))
    _, messages = ctx.to_llm_request()
    assert "A" in messages[0]["content"]
    assert "B" in messages[0]["content"]


# ---------- WonderlandAgent — base behavior ----------


async def test_constructor_wires_identity_memory_bus_llm(tmp_path: Path) -> None:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "cat")
    await memory.open()
    identity = _make_identity()
    agent = WonderlandAgent(identity=identity, memory=memory, bus=bus, llm=None)
    assert agent.identity is identity
    assert agent.memory is memory
    assert agent.bus is bus
    assert agent.llm is None


async def test_should_engage_delegates_to_identity(tmp_path: Path) -> None:
    """Identity owns the policy; the agent just calls into it."""
    interests = frozenset({SpeechAct.PROPOSAL})
    identity = _make_identity(interests=interests)
    agent = await _agent(tmp_path, identity=identity)

    proposal = _utterance(act=SpeechAct.PROPOSAL)
    ticket = _utterance(act=SpeechAct.TICKET)
    assert agent.should_engage(proposal) is True
    assert agent.should_engage(ticket) is False


async def test_default_compose_context_contains_constitution(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)
    triggers = [_utterance()]
    ctx = await agent.compose_context(triggers)
    assert ctx.constitution == agent.identity.constitution_text
    assert ctx.triggers == tuple(triggers)


async def test_compose_context_with_no_triggers_has_empty_thread(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)
    ctx = await agent.compose_context([])
    assert ctx.current_thread == ""
    assert ctx.triggers == ()


async def test_compose_context_populates_current_thread_from_episodic_memory(
    tmp_path: Path,
) -> None:
    """Prior utterances on the same thread show up in the current_thread layer."""
    from datetime import UTC, datetime

    agent = await _agent(tmp_path)
    base = datetime(2026, 5, 4, 12, 0, 0, tzinfo=UTC)

    # Prior thread history (recorded as if we'd observed and engaged earlier)
    earlier = Utterance(
        thread_id="t",
        speaker=AgentIdentity(name="white_rabbit", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.TICKET,
        content=UtteranceContent(body="ticket body"),
        timestamp=base.replace(second=0),
    )
    await agent.memory.record(earlier)

    # The trigger arrives now
    trigger = Utterance(
        thread_id="t",
        speaker=AgentIdentity(name="mad_hatter", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.TEST_SCENARIO,
        content=UtteranceContent(body="trigger body"),
        timestamp=base.replace(second=10),
    )
    await agent.memory.record(trigger)

    ctx = await agent.compose_context([trigger])
    assert "ticket body" in ctx.current_thread
    assert "[white_rabbit — ticket]" in ctx.current_thread


async def test_compose_context_populates_relationships_from_relational_memory(
    tmp_path: Path,
) -> None:
    """When the trigger comes from an agent we have notes about, those notes
    show up in Context.relationships."""
    agent = await _agent(tmp_path)
    agent.memory.relational.write(
        "white_rabbit",
        "Asks me for estimates I shouldn't be giving. Gentle redirect each time.",
    )

    trigger = _utterance(thread_id="t", speaker="white_rabbit", body="by when?")
    ctx = await agent.compose_context([trigger])

    assert "white_rabbit" in ctx.relationships
    assert "estimates I shouldn't be giving" in ctx.relationships


async def test_compose_context_relationships_empty_when_no_notes(tmp_path: Path) -> None:
    """No relational notes for the trigger's speaker → relationships layer empty."""
    agent = await _agent(tmp_path)
    trigger = _utterance(thread_id="t", speaker="white_rabbit")
    ctx = await agent.compose_context([trigger])
    assert ctx.relationships == ""


async def test_compose_context_includes_relationships_for_thread_speakers(
    tmp_path: Path,
) -> None:
    """Relationships layer covers everyone in the thread, not just the trigger speaker."""
    agent = await _agent(tmp_path)
    agent.memory.relational.write("white_rabbit", "rabbit-notes")
    agent.memory.relational.write("alice", "alice-notes")

    earlier = _utterance(thread_id="t", speaker="alice", body="user story...")
    await agent.memory.record(earlier)

    trigger = _utterance(thread_id="t", speaker="white_rabbit", body="ticketing it now")
    ctx = await agent.compose_context([trigger])

    assert "rabbit-notes" in ctx.relationships
    assert "alice-notes" in ctx.relationships


async def test_compose_context_excludes_self_from_relationships(tmp_path: Path) -> None:
    """The agent doesn't keep relational notes about itself."""
    agent = await _agent(tmp_path)
    agent.memory.relational.write(agent.identity.name, "should not appear")
    trigger = _utterance(thread_id="t", speaker=agent.identity.name)
    ctx = await agent.compose_context([trigger])
    assert "should not appear" not in ctx.relationships


async def test_compose_context_excludes_triggers_from_thread_history(tmp_path: Path) -> None:
    """The trigger appears as the immediate stimulus — don't double it in the history."""
    agent = await _agent(tmp_path)
    trigger = _utterance(thread_id="t", body="trigger-only")
    await agent.memory.record(trigger)

    ctx = await agent.compose_context([trigger])
    assert "trigger-only" not in ctx.current_thread
    # But the trigger is still presented as the trigger
    _, messages = ctx.to_llm_request()
    assert "trigger-only" in messages[0]["content"]


async def test_compose_context_isolates_threads(tmp_path: Path) -> None:
    """Other threads' history doesn't leak into this thread's context."""
    agent = await _agent(tmp_path)
    other_thread = _utterance(thread_id="OTHER", body="other-thread-content")
    await agent.memory.record(other_thread)

    trigger = _utterance(thread_id="t", body="this-thread")
    ctx = await agent.compose_context([trigger])
    assert "other-thread-content" not in ctx.current_thread


async def test_compose_context_orders_history_chronologically(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    agent = await _agent(tmp_path)
    base = datetime(2026, 5, 4, 12, 0, 0, tzinfo=UTC)
    for i in range(3):
        await agent.memory.record(
            Utterance(
                thread_id="t",
                speaker=AgentIdentity(name="rabbit", constitution_version="0.1"),
                addressed_to="caucus",
                speech_act=SpeechAct.TICKET,
                content=UtteranceContent(body=f"#{i}"),
                timestamp=base.replace(second=i),
            )
        )
    trigger = _utterance(thread_id="t", body="now")
    ctx = await agent.compose_context([trigger])
    # All three appear, in order
    idx0 = ctx.current_thread.index("#0")
    idx1 = ctx.current_thread.index("#1")
    idx2 = ctx.current_thread.index("#2")
    assert idx0 < idx1 < idx2


async def test_default_deliberate_returns_none(tmp_path: Path) -> None:
    """Silence is the default. Subclasses override to speak."""
    agent = await _agent(tmp_path)
    ctx = Context(constitution="C")
    assert await agent.deliberate(ctx) is None


# ---------- listen loop ----------


async def test_listen_records_and_queues_engaged_utterances(tmp_path: Path) -> None:
    interests = frozenset({SpeechAct.PROPOSAL})
    agent = await _agent(tmp_path, identity=_make_identity(interests=interests))
    listen_task = asyncio.create_task(agent.listen())

    await agent.bus.publish(_utterance(act=SpeechAct.PROPOSAL, body="seen"))

    queued = await asyncio.wait_for(agent.pending.get(), timeout=1.0)
    assert queued.content.body == "seen"
    assert await agent.memory.count() == 1

    listen_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await listen_task


async def test_listen_skips_utterances_outside_interests(tmp_path: Path) -> None:
    interests = frozenset({SpeechAct.PROPOSAL})
    agent = await _agent(tmp_path, identity=_make_identity(interests=interests))
    listen_task = asyncio.create_task(agent.listen())

    # Caucus filters by interests at the subscription layer, so a TICKET never
    # reaches this subscriber. Memory + queue stay empty.
    await agent.bus.publish(_utterance(act=SpeechAct.TICKET))
    await asyncio.sleep(0.05)
    assert agent.pending.empty()
    assert await agent.memory.count() == 0

    listen_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await listen_task


async def test_listen_does_not_record_when_engagement_policy_rejects(tmp_path: Path) -> None:
    """Even if the speech_act is in interests, a custom policy can refuse to engage."""

    def reject_all(_u: Utterance, _memory: object | None = None) -> bool:
        return False

    identity = Identity(
        name="cat",
        header=ConstitutionHeader(
            display_name="cat",
            role="r",
            lineage="Wonderland v0.1",
            version="0.1",
            license="L",
        ),
        constitution_text="",
        interests=frozenset(SpeechAct),
        engagement_policy=reject_all,
    )
    agent = await _agent(tmp_path, identity=identity)
    listen_task = asyncio.create_task(agent.listen())

    await agent.bus.publish(_utterance(act=SpeechAct.PROPOSAL))
    await asyncio.sleep(0.05)
    assert agent.pending.empty()
    assert await agent.memory.count() == 0

    listen_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await listen_task


# ---------- speak loop ----------


async def test_speak_publishes_when_deliberate_returns_utterance(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)

    output = _utterance(speaker="cheshire_cat", act=SpeechAct.PROPOSAL, body="my reply")

    async def fixed_deliberate(_ctx: Context) -> Utterance:
        return output

    agent.deliberate = fixed_deliberate  # type: ignore[method-assign]

    # Subscribe to bus to confirm the agent published
    sub = agent.bus.subscribe(agent_name="observer")
    speak_task = asyncio.create_task(agent.speak())
    await agent.pending.put(_utterance(act=SpeechAct.QUESTION))

    received = await asyncio.wait_for(anext(sub), timeout=1.0)
    assert received.content.body == "my reply"
    assert await agent.memory.count() == 1  # the agent's own output recorded

    speak_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await speak_task


async def test_speak_silently_skips_when_deliberate_returns_none(tmp_path: Path) -> None:
    """Silence is a valid move."""
    agent = await _agent(tmp_path)
    sub = agent.bus.subscribe(agent_name="observer")

    speak_task = asyncio.create_task(agent.speak())
    await agent.pending.put(_utterance(act=SpeechAct.QUESTION))

    # Wait briefly to let the speak loop process; no publish should happen
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(anext(sub), timeout=0.1)
    assert await agent.memory.count() == 0

    speak_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await speak_task


# ---------- lifecycle ----------


async def test_run_starts_both_loops_and_stop_cancels_them(tmp_path: Path) -> None:
    agent = await _agent(tmp_path)
    run_task = asyncio.create_task(agent.run())
    await asyncio.sleep(0.05)  # let run() schedule its sub-tasks
    assert agent._listen_task is not None
    assert agent._speak_task is not None
    assert not agent._listen_task.done()
    assert not agent._speak_task.done()

    await agent.stop()
    assert agent._listen_task is None
    assert agent._speak_task is None

    run_task.cancel()
    with contextlib_suppress(asyncio.CancelledError):
        await run_task


# Tiny helper inline to avoid importing contextlib at top-level for one use
def contextlib_suppress(*excs: type[BaseException]):
    import contextlib as _contextlib

    return _contextlib.suppress(*excs)


# ---------- end-to-end with a real loaded constitution ----------


async def test_end_to_end_with_loaded_constitution(tmp_path: Path) -> None:
    """Wire identity-from-disk + memory + bus and observe one turn."""
    cat_identity = load_constitution("cheshire_cat")
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(tmp_path, "cheshire_cat")
    await memory.open()

    class FixedReplyAgent(WonderlandAgent):
        async def deliberate(self, context: Context) -> Utterance | None:
            assert "Cheshire Cat" in context.constitution
            return Utterance(
                thread_id=context.triggers[0].thread_id,
                speaker=self.identity.as_agent_identity(),
                addressed_to="caucus",
                speech_act=SpeechAct.PROPOSAL,
                content=UtteranceContent(body="What would have to be true?"),
            )

    agent = FixedReplyAgent(identity=cat_identity, memory=memory, bus=bus)
    observer = bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(agent.run())

    await bus.publish(_utterance(act=SpeechAct.DIRECTIVE, body="build a thing"))

    cat_reply = await asyncio.wait_for(anext(observer), timeout=1.0)
    # The first utterance the observer sees might be the original directive
    # (caucus broadcasts to everyone). Skip until we see the cat's reply.
    while cat_reply.speaker.name != "cheshire_cat":
        cat_reply = await asyncio.wait_for(anext(observer), timeout=1.0)
    assert "What would have to be true?" in cat_reply.content.body

    await agent.stop()
    run_task.cancel()
    with contextlib_suppress(asyncio.CancelledError):
        await run_task
    await memory.close()


# ---------- parse-error retry ----------


class _SampleResponse(BaseModel):
    decision: str
    body: str = ""


class _SampleParseError(ResponseParseError):
    pass


def _parse_sample(text: str) -> _SampleResponse:
    return extract_and_validate(text, _SampleResponse, _SampleParseError)


def _scripted_llm(
    *texts: str,
    stop_reasons: list[str] | None = None,
) -> LLMClient:
    """LLMClient whose .complete() returns the given texts in order.

    ``stop_reasons`` lets callers specify a stop_reason per response;
    defaults to "end_turn" for every response. Pass "max_tokens" to
    simulate the truncation case that bit Hatter in the Geocities
    diagnose run (analysis-pending).
    """
    if stop_reasons is None:
        stop_reasons = ["end_turn"] * len(texts)
    assert len(stop_reasons) == len(texts), (
        "stop_reasons length must match texts length"
    )
    responses = [
        SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)],
            stop_reason=stop_reason,
            usage=SimpleNamespace(
                input_tokens=10,
                output_tokens=5,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
            ),
        )
        for text, stop_reason in zip(texts, stop_reasons)
    ]
    iterator = iter(responses)
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(side_effect=lambda **_: next(iterator))
    return LLMClient(client=client)


async def test_parse_with_retry_returns_immediately_on_first_success(tmp_path):
    agent = await _agent(tmp_path)
    agent.llm = _scripted_llm("ignored — only used on retry")
    parsed = await agent._parse_with_retry(
        _parse_sample,
        '{"decision": "story", "body": "ok"}',
        system=[],
        messages=[],
    )
    assert parsed.decision == "story"
    # No retry call should have happened
    assert agent.llm._client.messages.create.await_count == 0


async def test_parse_with_retry_recovers_after_one_failure(tmp_path, capsys):
    agent = await _agent(tmp_path)
    agent.llm = _scripted_llm('{"decision": "story", "body": "from retry"}')
    parsed = await agent._parse_with_retry(
        _parse_sample,
        "this is prose, not JSON",
        system=[],
        messages=[{"role": "user", "content": "go"}],
    )
    assert parsed.decision == "story"
    assert parsed.body == "from retry"
    # Exactly one retry call
    assert agent.llm._client.messages.create.await_count == 1
    captured = capsys.readouterr()
    assert "parse error on attempt 1" in captured.err
    assert "parse retry succeeded on attempt 2" in captured.err


async def test_parse_with_retry_raises_when_retry_also_fails(tmp_path, capsys):
    agent = await _agent(tmp_path)
    agent.llm = _scripted_llm("still not JSON either")
    with pytest.raises(_SampleParseError):
        await agent._parse_with_retry(
            _parse_sample,
            "first attempt also prose",
            system=[],
            messages=[{"role": "user", "content": "go"}],
            max_retries=1,  # explicit: this test is about raise-on-failure
        )
    # Retry happened (one extra LLM call), then both attempts failed.
    assert agent.llm._client.messages.create.await_count == 1
    assert "parse error on attempt 1" in capsys.readouterr().err


async def test_parse_with_retry_handles_empty_response(tmp_path):
    """Empty original response — assistant message gets a placeholder so
    the API doesn't reject the retry payload."""
    agent = await _agent(tmp_path)
    agent.llm = _scripted_llm('{"decision": "story", "body": "filled in"}')
    parsed = await agent._parse_with_retry(
        _parse_sample,
        "",
        system=[],
        messages=[{"role": "user", "content": "go"}],
    )
    assert parsed.decision == "story"
    # Inspect what the retry call sent — assistant content shouldn't be empty
    call_args = agent.llm._client.messages.create.await_args
    sent_messages = call_args.kwargs["messages"]
    assistant_msg = next(m for m in sent_messages if m["role"] == "assistant")
    assert assistant_msg["content"]  # non-empty


async def test_parse_with_retry_max_retries_zero_disables_retry(tmp_path):
    """max_retries=0 means no retry — fail-fast on the first parse error."""
    agent = await _agent(tmp_path)
    agent.llm = _scripted_llm("never called")
    with pytest.raises(_SampleParseError):
        await agent._parse_with_retry(
            _parse_sample,
            "not JSON",
            system=[],
            messages=[],
            max_retries=0,
        )
    assert agent.llm._client.messages.create.await_count == 0


async def test_parse_with_retry_logs_max_tokens_truncation(tmp_path, capsys):
    """When the retry response has stop_reason='max_tokens' (output
    truncated mid-JSON), surface a diagnostic line. The Geocities
    diagnose run hit this when Hatter's wide-directive responses
    exceeded the 4096-token cap; bumping DEFAULT_MAX_TOKENS fixed the
    immediate cause but the diagnostic stays so a future recurrence
    is legible from the run log.
    """
    agent = await _agent(tmp_path)
    # Retry response is also bad JSON AND was cut off at the cap
    agent.llm = _scripted_llm(
        '{"truncated": "json with no closing brace',
        stop_reasons=["max_tokens"],
    )
    with pytest.raises(_SampleParseError):
        await agent._parse_with_retry(
            _parse_sample,
            "first attempt — not JSON either",
            system=[],
            messages=[],
        )
    err = capsys.readouterr().err
    assert "max_tokens cap" in err
    assert "truncated mid-JSON" in err


def test_default_max_tokens_is_at_least_8k():
    """Pin against regressing DEFAULT_MAX_TOKENS below the value
    Hatter's wide-directive responses need. The Geocities diagnose
    run showed responses around 4000 output tokens hitting the old
    4096 cap; 8K is the floor below which we'd expect recurrence,
    16K is the value we landed on for headroom.
    """
    from wonderland.llm import DEFAULT_MAX_TOKENS

    assert DEFAULT_MAX_TOKENS >= 8192, (
        f"DEFAULT_MAX_TOKENS={DEFAULT_MAX_TOKENS} is too low — Hatter's "
        "wide-directive responses can truncate mid-JSON. See Geocities "
        "diagnose run analysis."
    )


# ---------- T-ab57 tool-result truncation ----------


def test_tool_result_truncation_preserves_small_results() -> None:
    """Small tool results pass through unchanged — only oversized
    results get capped. Most tool calls return small results
    (read_file median 1.8K, list_files median 496 bytes) — they
    should not be touched."""
    from wonderland.agent import _maybe_truncate_tool_result

    small = "short file content\n" * 10  # ~190 bytes
    assert _maybe_truncate_tool_result(small, "read_file") == small


def test_tool_result_truncation_caps_oversized() -> None:
    """Results above the cap get truncated with a marker telling the
    model how many bytes were dropped + how to recover them."""
    from wonderland.agent import _maybe_truncate_tool_result

    # 50KB grep result — well over the 5K cap
    big = "match-line\n" * 5000
    result = _maybe_truncate_tool_result(big, "grep")

    assert len(result) < len(big), "should shrink oversized result"
    assert "truncated" in result, "should mark truncation"
    assert "grep" in result, "should reference original tool name"
    assert "bytes" in result, "should report byte count dropped"
    # Head is preserved
    assert result.startswith("match-line"), "head of original content preserved"


def test_tool_result_truncation_handles_non_string_defensively() -> None:
    """Tool framework currently returns str, but defensive in case a
    future tool returns structured content (dict/bytes/etc.).
    Should not crash, just pass through."""
    from wonderland.agent import _maybe_truncate_tool_result

    structured: dict[str, str] = {"key": "value"}
    # Non-string input is returned as-is rather than raising.
    assert _maybe_truncate_tool_result(structured, "weird_tool") is structured  # type: ignore[arg-type]


async def test_parse_with_retry_bails_on_consecutive_empties(tmp_path, capsys):
    """Empty responses on a large context are deterministic — after 2
    consecutive empties, bail instead of burning the full retry budget
    re-sending the context (the bill the frontend Tweedle was running up)."""
    agent = await _agent(tmp_path)
    agent.llm = _scripted_llm("")  # the retry also comes back empty
    with pytest.raises(_SampleParseError):
        await agent._parse_with_retry(
            _parse_sample,
            "",  # initial response is empty too
            system=[],
            messages=[{"role": "user", "content": "go"}],
            max_retries=3,  # would allow 3 retries, but 2 empties bail early
        )
    # Bailed after ONE retry call (2 consecutive empties), not 3.
    assert agent.llm._client.messages.create.await_count == 1
    assert "consecutive" in capsys.readouterr().err
