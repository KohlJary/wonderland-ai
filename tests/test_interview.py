"""Tests for the Interview substrate — models, validation,
RequirementRegistry round-trip, disk-mediated bridge."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from wonderland import (
    Confidence,
    Interview,
    InterviewAnswer,
    InterviewAnswers,
    InterviewQuestion,
    QuestionKind,
    RequirementKind,
    RequirementPayload,
    RequirementRegistry,
    render_requirement,
)
from wonderland.interview import (
    PENDING_INTERVIEW_ANSWERS_FILENAME,
    PENDING_INTERVIEW_FILENAME,
    await_interview_answers,
    write_pending_interview,
)


# --------------------------------------------------------------------- #
# InterviewQuestion validation
# --------------------------------------------------------------------- #


def test_question_free_text_minimal() -> None:
    q = InterviewQuestion(
        id="primary_persona",
        text="Who's using this?",
        kind=QuestionKind.FREE_TEXT,
    )
    assert q.required is False
    assert q.options == []


def test_question_single_choice_requires_options() -> None:
    with pytest.raises(ValidationError, match="requires non-empty options"):
        InterviewQuestion(
            id="success",
            text="Strongest signal?",
            kind=QuestionKind.SINGLE_CHOICE,
            options=[],
        )


def test_question_multi_choice_requires_options() -> None:
    with pytest.raises(ValidationError, match="requires non-empty options"):
        InterviewQuestion(
            id="integrations",
            text="Which integrations matter?",
            kind=QuestionKind.MULTI_CHOICE,
            options=[],
        )


def test_question_free_text_rejects_options() -> None:
    with pytest.raises(
        ValidationError, match="only meaningful for"
    ):
        InterviewQuestion(
            id="persona",
            text="Who?",
            kind=QuestionKind.FREE_TEXT,
            options=["a", "b"],
        )


def test_question_numeric_rejects_options() -> None:
    with pytest.raises(
        ValidationError, match="only meaningful for"
    ):
        InterviewQuestion(
            id="scale",
            text="Users?",
            kind=QuestionKind.NUMERIC,
            options=["1", "many"],
        )


def test_question_id_must_be_non_empty() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestion(
            id="",
            text="Q?",
            kind=QuestionKind.FREE_TEXT,
        )


def test_question_text_must_be_non_empty() -> None:
    with pytest.raises(ValidationError):
        InterviewQuestion(
            id="q1",
            text="",
            kind=QuestionKind.FREE_TEXT,
        )


# --------------------------------------------------------------------- #
# Interview validation
# --------------------------------------------------------------------- #


def _q(qid: str, kind: QuestionKind = QuestionKind.FREE_TEXT) -> InterviewQuestion:
    return InterviewQuestion(
        id=qid, text=f"Question {qid}?", kind=kind
    )


def test_interview_requires_at_least_one_question() -> None:
    with pytest.raises(ValidationError):
        Interview(
            id="i1",
            label="I1",
            name="Empty",
            interviewer="alice",
            goal="x",
            questions=[],
        )


def test_interview_estimated_minutes_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Interview(
            id="i1",
            label="I1",
            name="Bad",
            interviewer="alice",
            goal="x",
            questions=[_q("q1")],
            estimated_minutes=0,
        )


def test_interview_default_allow_followup_true() -> None:
    iv = Interview(
        id="i1",
        label="I1",
        name="P",
        interviewer="alice",
        goal="g",
        questions=[_q("q1")],
    )
    assert iv.allow_followup is True


# --------------------------------------------------------------------- #
# InterviewAnswer / InterviewAnswers
# --------------------------------------------------------------------- #


def test_answer_supports_free_text_value() -> None:
    a = InterviewAnswer(
        question_id="primary_persona",
        value="Maya at a translation startup",
    )
    assert a.value == "Maya at a translation startup"
    assert a.free_response == ""
    assert a.skipped is False


def test_answer_supports_multi_choice_list() -> None:
    a = InterviewAnswer(
        question_id="integrations",
        value=["openai", "github"],
    )
    assert a.value == ["openai", "github"]


def test_answer_supports_numeric_value() -> None:
    a = InterviewAnswer(question_id="scale", value=1000.0)
    assert a.value == 1000.0


def test_answer_supports_skip() -> None:
    a = InterviewAnswer(question_id="optional_q", skipped=True)
    assert a.skipped is True
    assert a.value is None


def test_answer_supports_free_response_alongside_value() -> None:
    """Operator picks an option AND elaborates in free-response."""
    a = InterviewAnswer(
        question_id="success",
        value="anxiety_reduced",
        free_response="specifically the EOD pile feeling tractable",
    )
    assert a.value == "anxiety_reduced"
    assert "EOD pile" in a.free_response


def test_answers_batch_section_skip() -> None:
    """When the operator hits 'skip section' on the whole interview,
    section_skipped is True and the interviewer ships nothing."""
    a = InterviewAnswers(
        interview_id="persona-interview",
        section_skipped=True,
    )
    assert a.section_skipped is True
    assert a.answers == []


# --------------------------------------------------------------------- #
# RequirementPayload validation
# --------------------------------------------------------------------- #


def _req(**overrides) -> RequirementPayload:
    base = {
        "title": "Maya: end-of-day translation triage",
        "interview_id": "persona-interview",
        "question_id": "primary_persona",
        "kind": RequirementKind.PERSONA,
        "body": "Maya, 31, polyglot moderator triaging 40 threads at EOD across four languages.",
        "operator_quote": "Maya at a translation startup, end of day",
    }
    return RequirementPayload(**(base | overrides))


def test_requirement_defaults_to_operator_stated() -> None:
    payload = _req()
    assert payload.confidence is Confidence.OPERATOR_STATED


def test_requirement_accepts_interviewer_inferred() -> None:
    payload = _req(
        confidence=Confidence.INTERVIEWER_INFERRED, operator_quote=""
    )
    assert payload.confidence is Confidence.INTERVIEWER_INFERRED


@pytest.mark.parametrize("kind", list(RequirementKind))
def test_requirement_accepts_each_kind(kind: RequirementKind) -> None:
    payload = _req(kind=kind)
    assert payload.kind is kind


def test_requirement_rejects_empty_body() -> None:
    with pytest.raises(ValidationError):
        _req(body="")


def test_requirement_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        _req(title="")


# --------------------------------------------------------------------- #
# render_requirement markdown
# --------------------------------------------------------------------- #


def test_render_includes_title_and_metadata() -> None:
    payload = _req()
    md = render_requirement(7, payload)
    assert (
        "## Requirement 007: Maya: end-of-day translation triage"
        in md
    )
    assert "**Kind:** persona" in md
    assert "**Confidence:** operator_stated" in md
    assert "**Source interview:** persona-interview" in md
    assert "**Source question:** primary_persona" in md


def test_render_includes_body() -> None:
    payload = _req()
    md = render_requirement(1, payload)
    assert "Maya, 31, polyglot moderator" in md


def test_render_quotes_operator_when_present() -> None:
    payload = _req()
    md = render_requirement(1, payload)
    assert "**Operator quote:**" in md
    assert "> Maya at a translation startup" in md


def test_render_omits_quote_block_for_inferred() -> None:
    """Inferred requirements have no operator quote — the block
    shouldn't render."""
    payload = _req(
        confidence=Confidence.INTERVIEWER_INFERRED, operator_quote=""
    )
    md = render_requirement(1, payload)
    assert "**Operator quote:**" not in md


# --------------------------------------------------------------------- #
# RequirementRegistry round-trip
# --------------------------------------------------------------------- #


def test_registry_writes_numbered_file(tmp_path: Path) -> None:
    reg = RequirementRegistry(tmp_path)
    record = reg.write(_req())
    assert record.number == 1
    assert record.path.name.startswith("requirement-001-")
    assert record.path.exists()


def test_registry_increments_number(tmp_path: Path) -> None:
    reg = RequirementRegistry(tmp_path)
    a = reg.write(_req(title="First"))
    b = reg.write(_req(title="Second"))
    assert a.number == 1
    assert b.number == 2


def test_registry_find_by_slug(tmp_path: Path) -> None:
    reg = RequirementRegistry(tmp_path)
    written = reg.write(_req())
    found = reg.find_by_slug(written.slug)
    assert found is not None
    assert found.title == written.title


def test_registry_find_by_number(tmp_path: Path) -> None:
    reg = RequirementRegistry(tmp_path)
    written = reg.write(_req())
    found = reg.find_by_number(written.number)
    assert found is not None
    assert found.slug == written.slug


def test_registry_list_by_kind(tmp_path: Path) -> None:
    reg = RequirementRegistry(tmp_path)
    reg.write(_req(title="Persona A", kind=RequirementKind.PERSONA))
    reg.write(_req(title="Persona B", kind=RequirementKind.PERSONA))
    reg.write(_req(title="Constraint X", kind=RequirementKind.CONSTRAINT))
    personas = reg.list_by_kind(RequirementKind.PERSONA)
    constraints = reg.list_by_kind(RequirementKind.CONSTRAINT)
    assert len(personas) == 2
    assert len(constraints) == 1


def test_registry_list_by_interview(tmp_path: Path) -> None:
    reg = RequirementRegistry(tmp_path)
    reg.write(_req(title="From I1", interview_id="i1"))
    reg.write(_req(title="Also I1", interview_id="i1"))
    reg.write(_req(title="From I2", interview_id="i2"))
    i1 = reg.list_by_interview("i1")
    i2 = reg.list_by_interview("i2")
    assert len(i1) == 2
    assert len(i2) == 1


def test_registry_empty_when_directory_missing(tmp_path: Path) -> None:
    reg = RequirementRegistry(tmp_path)
    # don't write anything — directory doesn't exist
    assert reg.list_requirements() == []
    assert reg.next_number() == 1


def test_registry_preserves_kind_and_confidence_through_read(
    tmp_path: Path,
) -> None:
    """Round-trip: write a requirement, list it back, verify the
    parsed metadata matches what was written."""
    reg = RequirementRegistry(tmp_path)
    reg.write(
        _req(
            title="Inferred constraint",
            kind=RequirementKind.CONSTRAINT,
            confidence=Confidence.INTERVIEWER_INFERRED,
            operator_quote="",
        )
    )
    records = reg.list_requirements()
    assert len(records) == 1
    assert records[0].kind is RequirementKind.CONSTRAINT
    assert records[0].confidence is Confidence.INTERVIEWER_INFERRED


def test_registry_tolerates_unrelated_files(tmp_path: Path) -> None:
    """Random non-requirement files in the directory shouldn't crash
    the registry — same tolerance as the other registries."""
    reg = RequirementRegistry(tmp_path)
    reg.write(_req())
    # drop a stray file
    (reg.path / "README.md").write_text("not a requirement\n")
    (reg.path / "ignore-me.txt").write_text("ignore\n")
    records = reg.list_requirements()
    assert len(records) == 1


# --------------------------------------------------------------------- #
# Disk-mediated bridge — write_pending_interview / await_interview_answers
# --------------------------------------------------------------------- #


def _sample_interview() -> Interview:
    return Interview(
        id="persona-interview",
        label="I1",
        name="Who is this for?",
        interviewer="alice",
        goal="capture personas",
        questions=[
            InterviewQuestion(
                id="primary_persona",
                text="Who's using this?",
                kind=QuestionKind.FREE_TEXT,
                required=True,
            ),
            InterviewQuestion(
                id="success",
                text="Strongest signal:",
                kind=QuestionKind.SINGLE_CHOICE,
                options=["task_completed", "anxiety_reduced"],
            ),
        ],
    )


def test_write_pending_interview_lays_down_json(tmp_path: Path) -> None:
    interview = _sample_interview()
    batch_id = write_pending_interview(tmp_path, interview)
    out = tmp_path / PENDING_INTERVIEW_FILENAME
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["batch_id"] == batch_id
    assert data["interview_id"] == "persona-interview"
    assert data["interviewer"] == "alice"
    assert data["label"] == "I1"
    assert len(data["questions"]) == 2
    assert data["questions"][0]["kind"] == "free_text"
    assert data["questions"][1]["options"] == [
        "task_completed",
        "anxiety_reduced",
    ]


def test_write_pending_interview_respects_explicit_batch_id(
    tmp_path: Path,
) -> None:
    """Tests can pass a fixed batch_id for deterministic round-trip
    checks; production uses fresh uuid4 per call."""
    bid = write_pending_interview(
        tmp_path, _sample_interview(), batch_id="fixed-batch"
    )
    assert bid == "fixed-batch"


async def test_await_interview_answers_picks_up_matching_batch(
    tmp_path: Path,
) -> None:
    interview = _sample_interview()
    batch_id = write_pending_interview(
        tmp_path, interview, batch_id="b1"
    )
    answer_path = tmp_path / PENDING_INTERVIEW_ANSWERS_FILENAME
    # Simulate the TUI writing the answers file mid-wait.
    answer_path.write_text(
        json.dumps(
            {
                "batch_id": batch_id,
                "interview_id": "persona-interview",
                "answers": [
                    {
                        "question_id": "primary_persona",
                        "value": "Maya at translation startup",
                        "free_response": "",
                    },
                    {
                        "question_id": "success",
                        "value": "anxiety_reduced",
                        "free_response": "EOD pile feels tractable",
                    },
                ],
                "section_skipped": False,
            }
        ),
        encoding="utf-8",
    )

    answers = await await_interview_answers(
        tmp_path, batch_id=batch_id, poll_seconds=0.05, timeout_seconds=2.0
    )
    assert answers is not None
    assert answers.interview_id == "persona-interview"
    assert len(answers.answers) == 2
    assert answers.answers[1].free_response == "EOD pile feels tractable"


async def test_await_interview_answers_cleans_up_both_files(
    tmp_path: Path,
) -> None:
    write_pending_interview(
        tmp_path, _sample_interview(), batch_id="b1"
    )
    (tmp_path / PENDING_INTERVIEW_ANSWERS_FILENAME).write_text(
        json.dumps(
            {
                "batch_id": "b1",
                "interview_id": "persona-interview",
                "answers": [],
                "section_skipped": True,
            }
        ),
        encoding="utf-8",
    )

    answers = await await_interview_answers(
        tmp_path, batch_id="b1", poll_seconds=0.05, timeout_seconds=2.0
    )
    assert answers is not None
    assert answers.section_skipped is True
    # Both files should be gone — interview is consumed.
    assert not (tmp_path / PENDING_INTERVIEW_FILENAME).exists()
    assert not (
        tmp_path / PENDING_INTERVIEW_ANSWERS_FILENAME
    ).exists()


async def test_await_interview_answers_ignores_stale_batch(
    tmp_path: Path,
) -> None:
    """A stale answers file from a prior batch should be deleted +
    polling continues for the current batch's answers."""
    write_pending_interview(
        tmp_path, _sample_interview(), batch_id="current"
    )
    answer_path = tmp_path / PENDING_INTERVIEW_ANSWERS_FILENAME

    # Stale answers file from a previous batch.
    answer_path.write_text(
        json.dumps(
            {
                "batch_id": "old-stale",
                "interview_id": "persona-interview",
                "answers": [],
            }
        ),
        encoding="utf-8",
    )

    async def _write_real_answers_soon() -> None:
        # Wait a bit for the loop to see the stale file + delete it,
        # then write the real ones.
        await asyncio.sleep(0.2)
        answer_path.write_text(
            json.dumps(
                {
                    "batch_id": "current",
                    "interview_id": "persona-interview",
                    "answers": [
                        {
                            "question_id": "primary_persona",
                            "value": "Real answer",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    write_task = asyncio.create_task(_write_real_answers_soon())
    answers = await await_interview_answers(
        tmp_path,
        batch_id="current",
        poll_seconds=0.05,
        timeout_seconds=3.0,
    )
    await write_task
    assert answers is not None
    assert answers.answers[0].value == "Real answer"


async def test_await_interview_answers_returns_none_on_timeout(
    tmp_path: Path,
) -> None:
    write_pending_interview(
        tmp_path, _sample_interview(), batch_id="never-answered"
    )
    answers = await await_interview_answers(
        tmp_path,
        batch_id="never-answered",
        poll_seconds=0.05,
        timeout_seconds=0.2,
    )
    assert answers is None
    # Files cleaned up even on timeout.
    assert not (tmp_path / PENDING_INTERVIEW_FILENAME).exists()


async def test_await_interview_answers_handles_malformed_file(
    tmp_path: Path,
) -> None:
    """A malformed answers file is logged + cleaned up; the loop
    keeps waiting. We hit timeout in this test because no clean
    answers ever arrive."""
    write_pending_interview(
        tmp_path, _sample_interview(), batch_id="b1"
    )
    (tmp_path / PENDING_INTERVIEW_ANSWERS_FILENAME).write_text(
        "{ not valid json", encoding="utf-8"
    )

    answers = await await_interview_answers(
        tmp_path,
        batch_id="b1",
        poll_seconds=0.05,
        timeout_seconds=0.4,
    )
    # Malformed file → not parseable → loop times out → None.
    assert answers is None
