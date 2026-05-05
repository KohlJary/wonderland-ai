"""Tests for the synthetic-consensus guard.

These tests use synthetic transcripts — the guard is purely
deterministic, so no LLM is needed.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from wonderland import (
    AgentIdentity,
    ConsensusAlert,
    InMemoryCaucus,
    SpeechAct,
    SyntheticConsensusGuard,
    Utterance,
    UtteranceContent,
    default_agent_domains,
)
from wonderland.consensus import jaccard, shingles

# ---------- helpers ----------


def _u(
    *,
    speaker: str,
    body: str,
    act: SpeechAct = SpeechAct.PROPOSAL,
    thread_id: str = "t",
    when: datetime | None = None,
) -> Utterance:
    kwargs = {
        "thread_id": thread_id,
        "speaker": AgentIdentity(name=speaker, constitution_version="0.1"),
        "addressed_to": "caucus",
        "speech_act": act,
        "content": UtteranceContent(body=body),
    }
    if when is not None:
        kwargs["timestamp"] = when
    return Utterance(**kwargs)


# ---------- shingles + jaccard ----------


def test_shingles_lowercases_and_tokenizes() -> None:
    assert shingles("Rate Limiting NOW", size=2) == {
        "rate limiting",
        "limiting now",
    }


def test_shingles_handles_short_text() -> None:
    """Bodies shorter than the shingle size fall back to bare tokens."""
    assert shingles("yes", size=3) == {"yes"}


def test_shingles_strips_punctuation() -> None:
    assert "we should" in shingles("We should, however, ship it.", size=2)


def test_jaccard_identical_sets_is_one() -> None:
    s = shingles("rate limiting is the answer here", size=3)
    assert jaccard(s, s) == 1.0


def test_jaccard_disjoint_sets_is_zero() -> None:
    a = shingles("the architecture needs scale headroom", size=3)
    b = shingles("user pastes huge emoji blob", size=3)
    assert jaccard(a, b) == 0.0


def test_jaccard_partial_overlap_is_between_zero_and_one() -> None:
    a = shingles("we should add rate limiting now", size=3)
    b = shingles("rate limiting now is the answer", size=3)
    score = jaccard(a, b)
    assert 0.0 < score < 1.0


def test_jaccard_empty_inputs_are_zero() -> None:
    assert jaccard(set(), set()) == 0.0


# ---------- default_agent_domains ----------


def test_default_domains_covers_all_canonical_speakers() -> None:
    domains = default_agent_domains()
    for name in (
        "alice",
        "cheshire_cat",
        "white_rabbit",
        "mad_hatter",
        "caterpillar",
        "queen_of_hearts",
        "dormouse",
    ):
        assert name in domains, f"{name} missing from default_agent_domains()"


def test_tweedles_share_implementation_domain() -> None:
    """The pair is one constitutional voice, not two."""
    domains = default_agent_domains()
    assert domains["tweedledee"] == domains["tweedledum"] == "implementation"


def test_dodo_has_orchestration_domain() -> None:
    """The Dodo never issues substantive acts but the map is still total."""
    assert default_agent_domains()["dodo"] == "orchestration"


# ---------- SyntheticConsensusGuard — construction ----------


def test_guard_rejects_min_agents_below_two() -> None:
    bus = InMemoryCaucus()
    with pytest.raises(ValueError, match="at least two voices"):
        SyntheticConsensusGuard(bus, min_agents=1)


def test_guard_rejects_threshold_outside_unit_interval() -> None:
    bus = InMemoryCaucus()
    with pytest.raises(ValueError):
        SyntheticConsensusGuard(bus, similarity_threshold=1.1)
    with pytest.raises(ValueError):
        SyntheticConsensusGuard(bus, similarity_threshold=-0.1)


def test_guard_rejects_window_smaller_than_min_agents() -> None:
    bus = InMemoryCaucus()
    with pytest.raises(ValueError, match="never contain enough"):
        SyntheticConsensusGuard(bus, min_agents=3, window_size=2)


# ---------- guard observation: positive case ----------


async def test_guard_fires_when_three_distinct_domains_converge() -> None:
    """Cat + Rabbit + Queen converging on the same proposal — slightly
    different phrasings of the same position — is the canonical
    synthetic-consensus shape this guard exists to catch."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus,
        min_agents=3,
        similarity_threshold=0.5,
        shingle_size=2,
    )
    await guard.start()
    try:
        await bus.publish(
            _u(
                speaker="cheshire_cat",
                body="we should add rate limiting to the auth endpoint",
            )
        )
        await bus.publish(
            _u(
                speaker="white_rabbit",
                body="add rate limiting to the auth endpoint please",
            )
        )
        await bus.publish(
            _u(
                speaker="queen_of_hearts",
                body="add rate limiting to the auth endpoint now",
            )
        )
        alert = await asyncio.wait_for(anext(guard.alerts()), timeout=2.0)
        assert isinstance(alert, ConsensusAlert)
        assert alert.speech_act is SpeechAct.PROPOSAL
        assert set(alert.agents) == {
            "cheshire_cat",
            "white_rabbit",
            "queen_of_hearts",
        }
        assert set(alert.domains) == {"architecture", "sequence", "security"}
        assert alert.average_pairwise_similarity >= 0.5
        assert len(alert.sample_bodies) == 3
    finally:
        await guard.stop()


# ---------- guard observation: negative cases ----------


async def test_guard_silent_when_bodies_diverge() -> None:
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.5
    )
    await guard.start()
    try:
        await bus.publish(_u(speaker="cheshire_cat", body="restructure the seam"))
        await bus.publish(_u(speaker="white_rabbit", body="add a third sprint"))
        await bus.publish(
            _u(speaker="queen_of_hearts", body="rotate every shared credential")
        )
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


async def test_guard_silent_below_min_agents() -> None:
    """Two agents agreeing isn't synthetic consensus — even at high similarity."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2
    )
    await guard.start()
    try:
        await bus.publish(_u(speaker="cheshire_cat", body="add rate limiting now"))
        await bus.publish(_u(speaker="white_rabbit", body="rate limiting now please"))
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


async def test_guard_treats_tweedles_as_one_domain() -> None:
    """Both Tweedles share the implementation domain — three agreeing voices
    requires Cat + Rabbit + (one Tweedle), not Cat + Dee + Dum."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2
    )
    await guard.start()
    try:
        await bus.publish(_u(speaker="cheshire_cat", body="rate limiting now please"))
        await bus.publish(_u(speaker="tweedledee", body="rate limiting now please"))
        await bus.publish(_u(speaker="tweedledum", body="rate limiting now please"))
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


async def test_guard_silent_on_procedural_acts() -> None:
    """Acknowledgments and other procedural acts shouldn't count toward consensus."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.3, shingle_size=2
    )
    await guard.start()
    try:
        for speaker in ("cheshire_cat", "white_rabbit", "queen_of_hearts"):
            await bus.publish(
                _u(
                    speaker=speaker,
                    body="thread complete; settled.",
                    act=SpeechAct.ACKNOWLEDGMENT,
                )
            )
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


async def test_guard_skips_unknown_speakers() -> None:
    """A speaker not in the domain map (e.g., a human operator stub) is
    silently excluded — we don't guess at their constitutional domain."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2
    )
    await guard.start()
    try:
        await bus.publish(_u(speaker="cheshire_cat", body="rate limiting now please"))
        await bus.publish(_u(speaker="white_rabbit", body="rate limiting now please"))
        await bus.publish(_u(speaker="external_human", body="rate limiting now please"))
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


# ---------- guard observation: speech-act discrimination ----------


async def test_guard_groups_by_speech_act() -> None:
    """Two PROPOSALs and one CONCERN doesn't trigger — only same-act
    convergence counts."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.3, shingle_size=2
    )
    await guard.start()
    try:
        await bus.publish(
            _u(
                speaker="cheshire_cat",
                body="rate limiting now please",
                act=SpeechAct.PROPOSAL,
            )
        )
        await bus.publish(
            _u(
                speaker="white_rabbit",
                body="rate limiting now please",
                act=SpeechAct.PROPOSAL,
            )
        )
        await bus.publish(
            _u(
                speaker="queen_of_hearts",
                body="rate limiting now please",
                act=SpeechAct.CONCERN,
            )
        )
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


# ---------- guard: thread isolation + duplicate suppression ----------


async def test_guard_isolates_threads() -> None:
    """Convergence on thread A doesn't leak into thread B."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2
    )
    await guard.start()
    try:
        await bus.publish(
            _u(speaker="cheshire_cat", body="rate limiting now please", thread_id="A")
        )
        await bus.publish(
            _u(speaker="white_rabbit", body="rate limiting now please", thread_id="A")
        )
        await bus.publish(
            _u(speaker="queen_of_hearts", body="totally different angle on B", thread_id="B")
        )
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


async def test_guard_suppresses_duplicate_alerts_for_same_agent_set() -> None:
    """Once we've alerted on (thread, act, agents), more same-set
    utterances shouldn't re-trigger."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2
    )
    await guard.start()
    try:
        await bus.publish(_u(speaker="cheshire_cat", body="rate limiting now please"))
        await bus.publish(_u(speaker="white_rabbit", body="rate limiting now please"))
        await bus.publish(
            _u(speaker="queen_of_hearts", body="rate limiting now please")
        )
        first = await asyncio.wait_for(anext(guard.alerts()), timeout=2.0)
        assert isinstance(first, ConsensusAlert)

        # Same trio talking again — shouldn't re-fire.
        await bus.publish(
            _u(speaker="cheshire_cat", body="rate limiting now please indeed")
        )
        await bus.publish(
            _u(speaker="white_rabbit", body="rate limiting now please indeed")
        )
        await bus.publish(
            _u(speaker="queen_of_hearts", body="rate limiting now please indeed")
        )
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


async def test_guard_fires_again_when_agent_set_changes() -> None:
    """A different set of agents reaching consensus is a new signal."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2, window_size=20
    )
    await guard.start()
    try:
        # First trio
        for speaker in ("cheshire_cat", "white_rabbit", "queen_of_hearts"):
            await bus.publish(_u(speaker=speaker, body="rate limiting now please"))
        first = await asyncio.wait_for(anext(guard.alerts()), timeout=2.0)
        assert "queen_of_hearts" in first.agents

        # Add a fourth agent — new agent set, should re-fire
        await bus.publish(_u(speaker="caterpillar", body="rate limiting now please"))
        second = await asyncio.wait_for(anext(guard.alerts()), timeout=2.0)
        assert "caterpillar" in second.agents
    finally:
        await guard.stop()


# ---------- guard: window behavior ----------


async def test_guard_window_trims_old_utterances() -> None:
    """An agent's *latest* same-act utterance is what counts; older ones
    age out as the window slides."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus,
        min_agents=3,
        similarity_threshold=0.4,
        shingle_size=2,
        window_size=3,
    )
    await guard.start()
    try:
        # Fill the window with three converging utterances on different acts
        # (so they don't trigger), then push three new same-act ones.
        await bus.publish(
            _u(speaker="cheshire_cat", body="x", act=SpeechAct.QUESTION)
        )
        await bus.publish(
            _u(speaker="white_rabbit", body="y", act=SpeechAct.QUESTION)
        )
        await bus.publish(
            _u(speaker="queen_of_hearts", body="z", act=SpeechAct.QUESTION)
        )
        # The window now holds those three. New PROPOSAL utterances start
        # evicting them as they arrive.
        await bus.publish(
            _u(speaker="cheshire_cat", body="rate limiting now please")
        )
        await bus.publish(
            _u(speaker="white_rabbit", body="rate limiting now please")
        )
        await bus.publish(
            _u(speaker="queen_of_hearts", body="rate limiting now please")
        )
        alert = await asyncio.wait_for(anext(guard.alerts()), timeout=2.0)
        assert isinstance(alert, ConsensusAlert)
    finally:
        await guard.stop()


# ---------- guard: agent-keyed deduplication of same-domain repeats ----------


async def test_same_agent_speaking_twice_counts_once() -> None:
    """The Cat speaking twice doesn't artificially inflate the count."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2
    )
    await guard.start()
    try:
        await bus.publish(_u(speaker="cheshire_cat", body="rate limiting now please"))
        await bus.publish(_u(speaker="cheshire_cat", body="rate limiting now please"))
        await bus.publish(_u(speaker="white_rabbit", body="rate limiting now please"))
        await asyncio.sleep(0.1)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(anext(guard.alerts()), timeout=0.2)
    finally:
        await guard.stop()


# ---------- guard: alert content ----------


async def test_alert_includes_excerpt_of_each_body() -> None:
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2
    )
    await guard.start()
    try:
        await bus.publish(
            _u(speaker="cheshire_cat", body="rate limiting now please")
        )
        await bus.publish(
            _u(speaker="white_rabbit", body="rate limiting now please")
        )
        await bus.publish(
            _u(speaker="queen_of_hearts", body="rate limiting now please")
        )
        alert = await asyncio.wait_for(anext(guard.alerts()), timeout=2.0)
        assert all(
            "rate limiting" in body for body in alert.sample_bodies
        )
        assert "average pairwise similarity" in alert.reason
    finally:
        await guard.stop()


async def test_alert_at_is_recent() -> None:
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus, min_agents=3, similarity_threshold=0.4, shingle_size=2
    )
    await guard.start()
    try:
        for speaker in ("cheshire_cat", "white_rabbit", "queen_of_hearts"):
            await bus.publish(_u(speaker=speaker, body="rate limiting now please"))
        alert = await asyncio.wait_for(anext(guard.alerts()), timeout=2.0)
        assert datetime.now(UTC) - alert.at < timedelta(seconds=5)
    finally:
        await guard.stop()
