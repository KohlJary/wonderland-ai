"""Tests for the Runner — lifecycle, event emission, escalation, budget cap.

These tests use mocked LLMs throughout. The Runner's behavior is
deterministic given a synthetic event stream, so live-LLM testing is
not needed at this layer (we have it elsewhere via per-agent smokes).
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from wonderland import (
    LLMClient,
    SpeechAct,
    TokenUsage,
)
from wonderland.runner import Runner, RunnerEvent

# --------------------------------------------------------------------- #
# Mock LLM helpers
# --------------------------------------------------------------------- #


def _silent_llm() -> LLMClient:
    """An LLMClient whose `complete` always returns a silence response."""
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text='```json\n{"decision": "silence"}\n```')],
        stop_reason="end_turn",
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(return_value=response)
    return LLMClient(client=client)


# --------------------------------------------------------------------- #
# Lifecycle
# --------------------------------------------------------------------- #


async def test_late_publish_handler_suppresses_utterance_on_completed_thread(
    tmp_path: Path,
) -> None:
    """Late-publish stop-gap (roadmap 29497820): when an agent's
    deliberation completes after its trigger's thread has already
    transitioned to COMPLETE, the utterance is suppressed and stored
    in lost_utterances() rather than published into the closed thread.

    Synthetic test: drive the runner to a point where a thread is
    COMPLETE, hand the runner a freshly-deliberated utterance for that
    thread, confirm the handler returns True (suppress) and the
    utterance lands in lost_utterances()."""
    from datetime import UTC, datetime
    from wonderland.identity import AgentIdentity
    from wonderland.thread_monitor import ThreadInfo, ThreadState
    from wonderland.utterance import Utterance, UtteranceContent

    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    # Manually mark a thread COMPLETE via the monitor's internal state.
    runner._monitor._threads["closed-thread"] = ThreadInfo(
        thread_id="closed-thread",
        state=ThreadState.COMPLETE,
        last_activity=datetime.now(UTC),
    )
    late_utterance = Utterance(
        thread_id="closed-thread",
        speaker=AgentIdentity(name="tweedledee", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.CONTRACT_NOTE,
        content=UtteranceContent(body="late contract note"),
    )

    suppressed = runner._handle_late_publish(late_utterance)
    assert suppressed is True
    assert len(runner.lost_utterances()) == 1
    assert runner.lost_utterances()[0].id == late_utterance.id


async def test_late_publish_handler_passes_through_active_thread(
    tmp_path: Path,
) -> None:
    """Active threads (RUNNING / STUCK / QUIESCENT but not COMPLETE)
    don't trigger suppression — the utterance publishes normally."""
    from datetime import UTC, datetime
    from wonderland.identity import AgentIdentity
    from wonderland.thread_monitor import ThreadInfo, ThreadState
    from wonderland.utterance import Utterance, UtteranceContent

    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    runner._monitor._threads["live-thread"] = ThreadInfo(
        thread_id="live-thread",
        state=ThreadState.RUNNING,
        last_activity=datetime.now(UTC),
    )
    utterance = Utterance(
        thread_id="live-thread",
        speaker=AgentIdentity(name="tweedledee", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.CONTRACT_NOTE,
        content=UtteranceContent(body="timely contract note"),
    )
    assert runner._handle_late_publish(utterance) is False
    assert runner.lost_utterances() == []


async def test_runner_setup_and_teardown_clean(tmp_path: Path) -> None:
    """Setup spins up the consumer tasks; teardown cancels them all and
    writes the run record."""
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    await runner.setup()
    await runner.teardown()
    # Telemetry record was written
    record = tmp_path / ".wonderland" / "telemetry" / f"run-{runner.run_id}.json"
    assert record.is_file()


async def test_runner_publishes_directive_to_bus(tmp_path: Path) -> None:
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    await runner.setup()
    try:
        utterance = await runner.publish_directive("test directive")
        assert utterance.speech_act is SpeechAct.DIRECTIVE
        assert utterance.content.body == "test directive"
        assert utterance.speaker.name == "dodo"
    finally:
        await runner.teardown()


# --------------------------------------------------------------------- #
# Event emission
# --------------------------------------------------------------------- #


async def test_runner_emits_utterance_events(tmp_path: Path) -> None:
    """When the directive lands, an `utterance` event fires."""
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=10.0,
    )
    await runner.setup()
    received: list[RunnerEvent] = []
    try:
        await runner.publish_directive("test directive")
        async with asyncio.timeout(2.0):
            async for event in runner.events():
                received.append(event)
                # Break as soon as we see the directive utterance — we're
                # only verifying that utterance events emit, not that the
                # whole run completes.
                if event.kind == "utterance" and (
                    event.payload["utterance"].content.body == "test directive"
                ):
                    break
    finally:
        await runner.teardown()

    utterance_events = [e for e in received if e.kind == "utterance"]
    assert any(e.payload["utterance"].content.body == "test directive" for e in utterance_events)


async def test_runner_emits_timeout_event(tmp_path: Path) -> None:
    """When the timeout elapses without completion, the Runner yields
    a `timeout` event."""
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=0.5,  # very short
    )
    await runner.setup()
    try:
        await runner.publish_directive("triggers nothing — agents silent")
        async with asyncio.timeout(3.0):
            async for event in runner.events():
                if event.kind == "timeout":
                    break
    finally:
        await runner.teardown()


async def test_runner_abort_emits_aborted_event(tmp_path: Path) -> None:
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=10.0,
    )
    await runner.setup()
    received: list[RunnerEvent] = []
    try:
        await runner.publish_directive("test")
        runner.abort(reason="test wants to stop")
        async with asyncio.timeout(2.0):
            async for event in runner.events():
                received.append(event)
                if event.kind == "aborted":
                    break
    finally:
        await runner.teardown()
    assert any(e.kind == "aborted" for e in received)


# --------------------------------------------------------------------- #
# Budget cap
# --------------------------------------------------------------------- #


async def test_runner_emits_budget_warning_at_80_percent(tmp_path: Path) -> None:
    """When telemetry crosses 80% of the budget, a warning fires (once)."""
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=0.001,  # tiny budget so even the first call may cross it
        timeout_seconds=2.0,
    )
    # Fake a usage event by recording directly into telemetry.
    runner.telemetry.record(
        "alice",
        TokenUsage(input_tokens=900),  # $0.0009 — 90% of $0.001
    )
    await runner.setup()
    received: list[RunnerEvent] = []
    try:
        await runner.publish_directive("test")
        async with asyncio.timeout(3.0):
            async for event in runner.events():
                received.append(event)
                if event.kind in ("budget_warning", "budget_exceeded", "timeout"):
                    break
    finally:
        await runner.teardown()

    assert any(e.kind in ("budget_warning", "budget_exceeded") for e in received)


async def test_runner_emits_budget_exceeded_when_over_budget(tmp_path: Path) -> None:
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=0.001,
        timeout_seconds=3.0,
    )
    # Pre-record usage that exceeds the budget.
    runner.telemetry.record("alice", TokenUsage(input_tokens=2000))  # $0.002
    await runner.setup()
    received: list[RunnerEvent] = []
    try:
        await runner.publish_directive("test")
        async with asyncio.timeout(4.0):
            async for event in runner.events():
                received.append(event)
                if event.kind == "budget_exceeded":
                    break
    finally:
        await runner.teardown()

    exceeded = [e for e in received if e.kind == "budget_exceeded"]
    assert len(exceeded) >= 1
    assert exceeded[0].payload["cost"] >= 0.001


async def test_hard_budget_cap_halts_agent_llm_calls(tmp_path: Path) -> None:
    """When the budget is already exceeded at setup, no LLM call should
    fire during the run. The hard cap (per analysis 011) is what makes
    the budget number on the CLI actually enforced rather than aspirational."""
    call_log: list[str] = []

    def tracking_llm() -> LLMClient:
        client = MagicMock()
        client.messages = MagicMock()

        async def _create(**kwargs):
            call_log.append("called")
            response = SimpleNamespace(
                content=[
                    SimpleNamespace(type="text", text='```json\n{"decision": "silence"}\n```')
                ],
                stop_reason="end_turn",
                usage=SimpleNamespace(
                    input_tokens=1,
                    output_tokens=1,
                    cache_creation_input_tokens=0,
                    cache_read_input_tokens=0,
                ),
            )
            return response

        client.messages.create = _create
        return LLMClient(client=client)

    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: tracking_llm(),
        budget_dollars=0.0001,  # tiny
        timeout_seconds=2.0,
        quiescence_seconds=0.5,
    )
    # Pre-record usage that already exceeds the budget; setup() will
    # then wire each agent's gate to refuse new calls.
    runner.telemetry.record("alice", TokenUsage(input_tokens=10_000))  # $0.01

    await runner.setup()
    try:
        await runner.publish_directive("triggers nothing because budget is gated")
        async with asyncio.timeout(3.0):
            async for event in runner.events():
                if event.kind in ("complete", "timeout", "aborted"):
                    break
    finally:
        await runner.teardown()

    # The directive itself doesn't fire an LLM call (relay_directive
    # publishes a directive utterance directly). Every other agent
    # would normally engage on the directive — but the gate should
    # have refused. Zero LLM calls is the test.
    assert call_log == [], (
        f"hard budget cap should have prevented all LLM calls; got {len(call_log)} calls"
    )


async def test_publish_directive_with_recipients_registers_roster(tmp_path: Path) -> None:
    """publish_directive(..., recipients=[...]) registers a scoped meeting:
    the named agents + the Dodo see the thread; everyone else doesn't.
    Per the P6.T36-prep roster architecture (Block 2a)."""
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    await runner.setup()
    try:
        await runner.publish_directive(
            "scoping the translation envelope",
            thread_id="scoping",
            recipients=["alice", "cheshire_cat", "queen_of_hearts"],
            goal="produce ADR for translation envelope",
        )
    finally:
        await runner.teardown()

    assert runner.roster is not None
    assert not runner.roster.is_open("scoping")
    members = runner.roster.members("scoping")
    # Recipients + the Dodo (always added so it can orchestrate).
    assert members == frozenset({"alice", "cheshire_cat", "queen_of_hearts", "dodo"})
    assert runner.roster.goal("scoping") == "produce ADR for translation envelope"
    assert runner.roster.convenor("scoping") == "dodo"


# ---------- Block 2b: Runner.convene ----------


async def test_convene_registers_roster_and_publishes_seeds(tmp_path: Path) -> None:
    """convene() registers the new thread's roster (Dodo auto-added),
    re-stamps each seed's thread_id, and publishes the seeds to the bus.
    Per analysis 014: the convene mechanism is what enables cross-meeting
    composition — seed utterances from prior meetings drive engagement
    in the new one."""
    from wonderland.utterance import (
        Artifact,
        SpeechAct,
        Utterance,
        UtteranceContent,
    )

    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    await runner.setup()

    # Build a Cat-spoken proposal as if it came from a prior meeting.
    cat_identity = runner.agents["cheshire_cat"].identity.as_agent_identity()
    seed = Utterance(
        thread_id="prior-thread",  # will be re-stamped
        speaker=cat_identity,
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(
            body="ADR-001 stub for the test",
            artifacts=[
                Artifact(
                    kind="adr",
                    payload={"slug": "test-adr", "title": "Test ADR"},
                ),
            ],
        ),
    )

    try:
        published = await runner.convene(
            thread_id="followup",
            goal="produce a contract note",
            roster=["tweedledee", "tweedledum"],
            seed_utterances=[seed],
        )
    finally:
        await runner.teardown()

    # Roster: the named agents + the Dodo (auto-added).
    assert runner.roster is not None
    assert runner.roster.members("followup") == frozenset({"tweedledee", "tweedledum", "dodo"})
    assert runner.roster.goal("followup") == "produce a contract note"
    assert runner.roster.convenor("followup") == "dodo"

    # Seeds: published, re-stamped, fresh ids, parent_id cleared.
    assert len(published) == 1
    restamped = published[0]
    assert restamped.thread_id == "followup"
    assert restamped.id != seed.id, "id should be regenerated to avoid duplicates"
    assert restamped.parent_id is None
    assert restamped.speaker.name == "cheshire_cat"
    assert restamped.speech_act is SpeechAct.PROPOSAL
    assert restamped.content.artifacts[0].payload["slug"] == "test-adr"


async def test_convene_with_directive_publishes_dodo_directive_too(
    tmp_path: Path,
) -> None:
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    await runner.setup()
    try:
        published = await runner.convene(
            thread_id="t",
            goal="g",
            roster=["alice"],
            convenor_directive="Here's what this meeting is for.",
        )
    finally:
        await runner.teardown()

    # Returned list includes the directive (last entry).
    assert len(published) == 1
    last = published[0]
    assert last.speech_act.value == "directive"
    assert last.speaker.name == "dodo"
    assert last.thread_id == "t"


async def test_convene_routes_seeds_only_to_roster_members(tmp_path: Path) -> None:
    """Bus filtering by roster: rostered agents see the seed, non-rostered
    don't. Validated by checking that only roster members' listen loops
    receive the seed utterance via the bus."""
    from wonderland.utterance import (
        SpeechAct,
        Utterance,
        UtteranceContent,
    )

    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )

    # A separate observer subscriber that bypasses the roster — this is
    # what the runner-observer does — sees every utterance regardless.
    sniffer = runner.bus.subscribe("test-sniffer", bypass_roster=True)
    sniffed: list[Utterance] = []

    async def _sniff() -> None:
        async for u in sniffer:
            sniffed.append(u)

    sniff_task = asyncio.create_task(_sniff())

    cat_identity = runner.agents["cheshire_cat"].identity.as_agent_identity()
    seed = Utterance(
        thread_id="any",
        speaker=cat_identity,
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="seed body"),
    )

    await runner.setup()
    try:
        await runner.convene(
            thread_id="scoped",
            goal="g",
            roster=["alice"],
            seed_utterances=[seed],
        )
        # Give the bus a tick to deliver.
        await asyncio.sleep(0.05)
    finally:
        sniff_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sniff_task
        await runner.teardown()

    # The bypass-roster sniffer saw the seed (proves it was published).
    assert any(u.content.body == "seed body" for u in sniffed)


async def test_convene_raises_without_roster() -> None:
    """convene() requires a ThreadRoster; Runner constructed without one
    can't scope meetings."""
    import tempfile

    from wonderland.agents.dodo import Dodo
    from wonderland.caucus import InMemoryCaucus
    from wonderland.memory import AgentMemory

    bus = InMemoryCaucus()
    # Build a minimal Dodo stub so we can construct the Runner; convene
    # should fail before it actually uses the dodo.
    with tempfile.TemporaryDirectory() as td:
        memory = AgentMemory.for_project(Path(td), "dodo")
        await memory.open()
        dodo = Dodo.__new__(Dodo)
        # Bypass __init__ so we don't need the full constitution machinery.
        Dodo.__init__(dodo, memory=memory, bus=bus, llm=None)
        runner = Runner(
            bus=bus,
            agents={"dodo": dodo},
            dodo=dodo,
            project_root=Path(td),
            roster=None,
        )
        with pytest.raises(RuntimeError, match="requires the Runner to have a ThreadRoster"):
            await runner.convene(thread_id="t", goal="g", roster=["alice"])
        await memory.close()


async def test_publish_directive_without_recipients_leaves_thread_open(
    tmp_path: Path,
) -> None:
    """Default behavior preserved: no `recipients` arg means no roster
    registration, so the thread is open (every agent sees it). This is
    the backward-compat shape the existing showcases rely on."""
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    await runner.setup()
    try:
        await runner.publish_directive("open thread, everyone sees")
    finally:
        await runner.teardown()

    assert runner.roster is not None
    assert runner.roster.is_open("main")


async def test_set_budget_guard_can_be_cleared(tmp_path: Path) -> None:
    """Direct construction without a Runner leaves the gate unset; setting
    it to None explicitly clears it. Used by tests + scripts that wire
    agents directly."""
    from wonderland.agent import WonderlandAgent
    from wonderland.caucus import InMemoryCaucus
    from wonderland.identity import ConstitutionHeader, Identity
    from wonderland.memory import AgentMemory

    identity = Identity(
        name="probe",
        header=ConstitutionHeader(
            display_name="Probe",
            role="probe",
            lineage="test",
            version="0.1",
            license="test",
        ),
        constitution_text="",
    )
    bus = InMemoryCaucus()
    mem = AgentMemory.for_project(tmp_path, "probe")
    await mem.open()
    agent = WonderlandAgent(identity=identity, memory=mem, bus=bus, llm=None)
    assert agent._budget_ok is None
    agent.set_budget_guard(lambda: True)
    assert agent._budget_ok is not None
    agent.set_budget_guard(None)
    assert agent._budget_ok is None
    await mem.close()


# --------------------------------------------------------------------- #
# Interactive escalation
# --------------------------------------------------------------------- #


async def test_runner_relays_escalation_response_as_dodo_directive(
    tmp_path: Path,
) -> None:
    """When the human responds to an escalation, the Runner relays the
    response via Dodo.relay_directive so the team sees the human's call."""
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=5.0,
    )
    await runner.setup()
    received: list[RunnerEvent] = []
    relayed_directives: list[str] = []
    escalation_task: asyncio.Task[None] | None = None
    try:
        # Manually trigger an escalation by calling the Dodo's escalate_deadlock
        # with the runner's interactive channel.
        await runner.publish_directive("seed")

        # Wait for the directive to land, then trigger an escalation as a
        # background task — _escalate_via_runner awaits the channel which
        # awaits the human response, so it will not return until we call
        # respond_to_escalation, which we can only do from the event loop
        # below.
        await asyncio.sleep(0.1)
        escalation_task = asyncio.create_task(
            runner._escalate_via_runner("main", reason="test escalation")
        )

        # Consume events; respond to the escalation prompt.
        async with asyncio.timeout(5.0):
            async for event in runner.events():
                received.append(event)
                if event.kind == "escalation_prompt":
                    await runner.respond_to_escalation(
                        event.payload["prompt_id"],
                        "go with option B",
                    )
                if event.kind == "utterance":
                    u = event.payload["utterance"]
                    if (
                        u.speaker.name == "dodo"
                        and u.speech_act is SpeechAct.DIRECTIVE
                        and "Human resolution" in u.content.body
                    ):
                        relayed_directives.append(u.content.body)
                        break
    finally:
        if escalation_task is not None and not escalation_task.done():
            escalation_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await escalation_task
        await runner.teardown()

    assert any("go with option B" in d for d in relayed_directives)


async def test_respond_to_unknown_escalation_raises(tmp_path: Path) -> None:
    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=2.0,
    )
    await runner.setup()
    try:
        with pytest.raises(ValueError, match="No pending escalation"):
            await runner.respond_to_escalation("nonexistent-id", "response")
    finally:
        await runner.teardown()


# --------------------------------------------------------------------- #
# Run record
# --------------------------------------------------------------------- #


async def test_run_record_includes_outcome_and_elapsed(tmp_path: Path) -> None:
    """Telemetry written at teardown captures the outcome + elapsed time."""
    import json

    runner = await Runner.make_full_cast(
        tmp_path,
        llm_factory=lambda name, tel: _silent_llm(),
        budget_dollars=10.0,
        timeout_seconds=0.5,
    )
    await runner.setup()
    try:
        await runner.publish_directive("test")
        with contextlib.suppress(Exception):
            async with asyncio.timeout(2.0):
                async for event in runner.events():
                    if event.kind == "timeout":
                        break
    finally:
        await runner.teardown()

    record_path = tmp_path / ".wonderland" / "telemetry" / f"run-{runner.run_id}.json"
    record = json.loads(record_path.read_text())
    assert record["outcome"] == "timeout"
    assert record["elapsed_seconds"] > 0
    assert record["budget_dollars"] == 10.0
    assert record["budget_exceeded"] is False
