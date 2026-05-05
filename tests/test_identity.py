"""Tests for Identity and the constitution loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland import (
    AgentIdentity,
    ConstitutionHeader,
    ConstitutionParseError,
    Identity,
    SpeechAct,
    Stance,
    Utterance,
    UtteranceContent,
    default_engagement_policy,
    load_constitution,
    parse_constitution_header,
)

# All character constitutions currently in the repo. The pair protocol is
# deliberately excluded — it is a relational artifact, not a character.
CHARACTERS = [
    "alice",
    "caterpillar",
    "cheshire_cat",
    "dodo",
    "dormouse",
    "mad_hatter",
    "queen_of_hearts",
    "tweedledee",
    "tweedledum",
    "white_rabbit",
]


# ---------- Header parsing ----------


def test_parse_minimal_header() -> None:
    text = (
        "# Cheshire Cat\n"
        "\n"
        "**Role:** Technical SME / Architect\n"
        "**Lineage:** Wonderland v0.1\n"
        "**License:** MIT\n"
        "\n"
        "---\n"
        "\n"
        "## I. Constitution\n"
        "You are the Cheshire Cat.\n"
    )
    h = parse_constitution_header(text)
    assert h.display_name == "Cheshire Cat"
    assert h.role == "Technical SME / Architect"
    assert h.lineage == "Wonderland v0.1"
    assert h.version == "0.1"
    assert h.license == "MIT"
    assert h.pair is None


def test_parse_header_extracts_pair_when_present() -> None:
    text = (
        "# Tweedledee\n"
        "\n"
        "**Role:** Implementation — Frontend\n"
        "**Lineage:** Wonderland v0.2\n"
        "**Pair:** Tweedledum\n"
        "**License:** MIT\n"
        "\n"
        "---\n"
    )
    h = parse_constitution_header(text)
    assert h.pair == "Tweedledum"
    assert h.version == "0.2"


def test_parse_header_stops_at_separator() -> None:
    """`**Status:**` etc. inside the body must not be treated as header keys."""
    text = (
        "# Cat\n"
        "**Role:** X\n"
        "**Lineage:** Wonderland v0.1\n"
        "**License:** L\n"
        "---\n"
        "**Status:** proposed\n"  # body, not header
    )
    h = parse_constitution_header(text)
    assert h.role == "X"


def test_parse_rejects_missing_h1() -> None:
    text = "**Role:** X\n**Lineage:** Wonderland v0.1\n**License:** L\n---\n"
    with pytest.raises(ConstitutionParseError, match="H1"):
        parse_constitution_header(text)


def test_parse_rejects_missing_role() -> None:
    """Files like the Tweedle pair protocol have Lineage and License but no Role."""
    text = (
        "# The Tweedle Pair Protocol\n"
        "**Lineage:** Wonderland v0.2\n"
        "**Applies to:** Tweedledee, Tweedledum\n"
        "**License:** MIT\n"
        "---\n"
    )
    with pytest.raises(ConstitutionParseError, match="Role"):
        parse_constitution_header(text)


def test_parse_rejects_missing_lineage() -> None:
    text = "# X\n**Role:** R\n**License:** L\n---\n"
    with pytest.raises(ConstitutionParseError, match="Lineage"):
        parse_constitution_header(text)


def test_parse_rejects_missing_license() -> None:
    text = "# X\n**Role:** R\n**Lineage:** Wonderland v0.1\n---\n"
    with pytest.raises(ConstitutionParseError, match="License"):
        parse_constitution_header(text)


def test_parse_rejects_unparseable_lineage() -> None:
    text = "# X\n**Role:** R\n**Lineage:** something else\n**License:** L\n---\n"
    with pytest.raises(ConstitutionParseError, match="version"):
        parse_constitution_header(text)


# ---------- Loader against real constitutions ----------


@pytest.mark.parametrize("name", CHARACTERS)
def test_loads_each_real_constitution(name: str) -> None:
    identity = load_constitution(name)
    assert identity.name == name
    assert identity.header.display_name
    assert identity.header.role
    assert identity.header.version
    assert identity.constitution_text  # non-empty


def test_loaded_identity_carries_full_text() -> None:
    identity = load_constitution("cheshire_cat")
    assert "You are the Cheshire Cat." in identity.constitution_text
    # The ADR template lives in §V — full body retained
    assert "ADR" in identity.constitution_text


def test_tweedles_have_pair_field() -> None:
    dee = load_constitution("tweedledee")
    dum = load_constitution("tweedledum")
    assert dee.header.pair == "Tweedledum"
    assert dum.header.pair == "Tweedledee"


def test_singletons_have_no_pair() -> None:
    cat = load_constitution("cheshire_cat")
    assert cat.header.pair is None


def test_load_with_custom_root(tmp_path: Path) -> None:
    custom = tmp_path / "constitutions"
    custom.mkdir()
    (custom / "test_agent.md").write_text(
        "# Test Agent\n"
        "**Role:** Tester\n"
        "**Lineage:** Wonderland v9.9\n"
        "**License:** MIT\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    identity = load_constitution("test_agent", root=custom)
    assert identity.header.role == "Tester"
    assert identity.header.version == "9.9"


def test_load_missing_constitution_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_constitution("nonexistent", root=tmp_path)


def test_load_pair_protocol_is_rejected_as_non_character() -> None:
    """The Tweedle pair protocol is in constitutions/ but isn't a character."""
    with pytest.raises(ConstitutionParseError):
        load_constitution("tweedle_pair_protocol")


# ---------- Identity behavior ----------


def test_default_interests_is_all_speech_acts() -> None:
    identity = load_constitution("cheshire_cat")
    assert identity.interests == frozenset(SpeechAct)


def test_as_agent_identity_uses_canonical_name_and_version() -> None:
    identity = load_constitution("cheshire_cat")
    aid = identity.as_agent_identity()
    assert aid.name == "cheshire_cat"
    assert aid.constitution_version == identity.header.version


def test_as_agent_identity_drops_into_an_utterance() -> None:
    identity = load_constitution("cheshire_cat")
    u = Utterance(
        thread_id="t",
        speaker=identity.as_agent_identity(),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    assert u.speaker.name == "cheshire_cat"


def test_default_engagement_policy_engages_on_interest_match() -> None:
    interests = frozenset({SpeechAct.PROPOSAL, SpeechAct.QUESTION})
    policy = default_engagement_policy(interests)
    speaker = AgentIdentity(name="cat", constitution_version="0.1")

    proposal = Utterance(
        thread_id="t",
        speaker=speaker,
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    ticket = Utterance(
        thread_id="t",
        speaker=speaker,
        addressed_to="caucus",
        speech_act=SpeechAct.TICKET,
        content=UtteranceContent(body="..."),
    )
    assert policy(proposal, None) is True
    assert policy(ticket, None) is False


def test_should_engage_uses_default_when_no_policy_set() -> None:
    identity = Identity(
        name="x",
        header=ConstitutionHeader(
            display_name="X",
            role="R",
            lineage="Wonderland v0.1",
            version="0.1",
            license="L",
        ),
        constitution_text="",
        interests=frozenset({SpeechAct.PROPOSAL}),
    )
    speaker = AgentIdentity(name="cat", constitution_version="0.1")
    proposal = Utterance(
        thread_id="t",
        speaker=speaker,
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    assert identity.should_engage(proposal)


def test_should_engage_uses_provided_policy_when_set() -> None:
    """Custom policy can ignore interests entirely."""
    calls: list[Stance] = []

    def policy(u: Utterance, _memory: object | None = None) -> bool:
        calls.append(u.stance)
        return False

    identity = Identity(
        name="x",
        header=ConstitutionHeader(
            display_name="X",
            role="R",
            lineage="Wonderland v0.1",
            version="0.1",
            license="L",
        ),
        constitution_text="",
        interests=frozenset(SpeechAct),  # would normally engage
        engagement_policy=policy,
    )
    speaker = AgentIdentity(name="cat", constitution_version="0.1")
    u = Utterance(
        thread_id="t",
        speaker=speaker,
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body="..."),
    )
    assert identity.should_engage(u) is False
    assert calls == [Stance.IN_CHARACTER]
