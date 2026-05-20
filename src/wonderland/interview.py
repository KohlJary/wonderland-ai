"""Interview substrate — sibling abstraction to Meeting for the
discovery / requirements-gathering phase.

A Meeting is agents-talking-to-agents; an Interview is one
agent-talking-to-the-operator. The operator is the responder; the
interviewer is the single agent on the team side. Output is a batch
of ``requirement`` artifacts that downstream meetings seed from.

See ``project_interviews_milestones_thesis.md`` in user memory for
why this is load-bearing: without Interviews, every design run starts
from a raw directive and there's no continuity between iterations.
With Interviews, operator intent gets captured once as structured
requirements; design and implementation operate against those
requirements instead of regenerating context per run.

Wire shape:

  Interviewer agent (Alice / Cat / Rabbit) ships an
  ``interview_question_batch`` artifact carrying a list of questions
  → substrate writes ``.wonderland/runs/<run_id>/pending_interview.json``
  (the disk-mediated bridge, see ``cli_run_bg.py``)
  → TUI surfaces InterviewModal, operator answers + submits
  → substrate writes ``pending_interview_answers.json``
  → interviewer agent reads answers on its next turn, transforms them
    into ``requirement`` artifacts (with confidence: operator_stated),
    optionally ships a follow-up batch if there are gaps
  → interview closes; RequirementRegistry has the artifacts on disk
    at ``.wonderland/requirements/requirement-NNN-slug.md``.

Storage at ``<project_root>/.wonderland/requirements/`` mirrors the
ADR / Story / Ticket / TestScenario registry pattern: numbered
filenames, slug-from-title, append-only, registry-scans-filesystem
for next-number computation.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from wonderland.adr import slugify
from wonderland.artifact_guid import new_artifact_guid, short_guid

REQUIREMENTS_DIRNAME = "requirements"
# T-g3: filename's id-part is either an 8-char ULID prefix (new) or
# a 1-4 digit legacy number (pre-P18).
_FILENAME_PATTERN = re.compile(
    r"^requirement-(?P<id>[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(?P<slug>[a-z0-9-]+)\.md$"
)
_GUID_PATTERN = re.compile(r"^\*\*GUID:\*\*\s*([0-9A-HJKMNP-TV-Z]{26})\s*$", re.MULTILINE)
_NUMBER_FROM_H2 = re.compile(r"^##\s*Requirement\s+(\d+)\s*:", re.MULTILINE)

# Disk-mediated bridge filenames. Both files live under the run dir
# (.wonderland/runs/<run_id>/) alongside pending_question.json from
# the question bridge. Interview bridge files are distinct so the
# two bridges never collide.
PENDING_INTERVIEW_FILENAME = "pending_interview.json"
PENDING_INTERVIEW_ANSWERS_FILENAME = "pending_interview_answers.json"

# Wall-clock timeout for interview answers. Generous — interviews
# are by-design dormant while operators step away. Default of one
# hour is long enough for a coffee break or a meeting interruption;
# operators who genuinely abandon the run can just kill the
# subprocess.
_DEFAULT_INTERVIEW_TIMEOUT_SECONDS = 3600.0
# Poll cadence for the answers file. Same 0.5s as the question
# bridge — responsive enough that submit → pickup feels instant
# without burning CPU on a dormant run.
_INTERVIEW_POLL_SECONDS = 0.5


# --------------------------------------------------------------------- #
# Question shape — what interviewers ship as a batch
# --------------------------------------------------------------------- #


class QuestionKind(StrEnum):
    """The render shape an InterviewQuestion takes in the TUI form.

    Each kind drives a different widget AND a different answer-value
    type, but every kind admits a free-response escape: the operator
    can always elaborate beyond the form into a free-text box. The
    interviewer agent reads both the structured value and the free-
    response text when transforming answers into requirements.
    """

    FREE_TEXT = "free_text"
    """Multi-line text area. Answer value is the raw string."""
    SINGLE_CHOICE = "single_choice"
    """Radio buttons over ``options``. Answer value is the chosen
    option string, or the literal ``"custom"`` when the operator wrote
    in a free-response answer that didn't match any option."""
    MULTI_CHOICE = "multi_choice"
    """Checkbox group over ``options``. Answer value is a list of
    chosen option strings."""
    NUMERIC = "numeric"
    """Single-line numeric input. Answer value is a float (or None if
    the operator left it blank on a non-required question)."""


class InterviewQuestion(BaseModel):
    """One question in an Interview's batch. Both the structured form
    (kind + options) and the free-response escape are first-class —
    the operator can ignore the form and just write prose, and the
    interviewer agent reads both halves when ranking the answer."""

    id: str = Field(min_length=1)
    """Stable identifier — used as the key in the answers batch.
    Should be slug-shaped within a single interview (e.g.
    ``primary_persona``, ``stack_constraints``)."""

    text: str = Field(min_length=1)
    """The question prompt shown to the operator. One sentence is the
    target; the interviewer should resist multi-question prompts that
    pack two asks into one box."""

    kind: QuestionKind
    """Drives the form widget. ``free_text`` is the default safe
    choice; ``single_choice`` / ``multi_choice`` / ``numeric`` reduce
    cognitive load when the answer space is bounded."""

    required: bool = False
    """When True, the operator can't submit the batch without
    answering OR skipping the section. Use sparingly — too many
    required fields turns the form into a friction wall."""

    options: list[str] = Field(default_factory=list)
    """Choice options for ``single_choice`` and ``multi_choice``
    kinds. Ignored for ``free_text`` and ``numeric``. Operator can
    always escape to free-response on any kind regardless of
    options."""

    @model_validator(mode="after")
    def _options_match_kind(self) -> "InterviewQuestion":
        choice_kinds = (
            QuestionKind.SINGLE_CHOICE,
            QuestionKind.MULTI_CHOICE,
        )
        if self.kind in choice_kinds and not self.options:
            raise ValueError(
                f"question {self.id!r}: kind={self.kind.value} "
                "requires non-empty options"
            )
        if self.kind not in choice_kinds and self.options:
            raise ValueError(
                f"question {self.id!r}: options only meaningful for "
                f"single_choice / multi_choice kinds, got {self.kind.value}"
            )
        return self


class Interview(BaseModel):
    """A structured Q&A unit. Sibling-to-Meeting on the workflow side
    — a workflow can declare ``interviews:`` alongside ``meetings:``
    and the runtime executes interviews before / between / after
    meetings per the YAML order.

    One interviewer + the operator. No multi-agent rotation, no
    rotation budget — Interviews are wall-clock unbounded because
    operators step away. The substrate's response is to mark the run
    dormant on disk and only resume when the answers file appears.
    """

    id: str = Field(min_length=1)
    """Slug-shaped interview id, unique within a workflow."""

    label: str = Field(min_length=1)
    """Short display label (e.g. ``I1``, ``I2``) — parallel to a
    Meeting's ``M1`` / ``M2`` label. Used by the TUI to anchor the
    operator in the discovery flow."""

    name: str = Field(min_length=1)
    """Human-readable interview name (e.g. ``Who is this for?``)."""

    interviewer: str = Field(min_length=1)
    """Single agent name on the team side. Typically Alice for
    persona / situation interviews, Cat for technical-constraint
    interviews, Rabbit for scope / success-criteria interviews."""

    goal: str = Field(min_length=1)
    """One-sentence goal — what the interviewer is trying to capture.
    Shown to the operator at the top of the modal so they know
    what's being asked of them."""

    questions: list[InterviewQuestion] = Field(min_length=1)
    """The question batch. Aim for 3-5 questions; the
    estimated_minutes target should drive the size."""

    estimated_minutes: int = Field(default=5, ge=1)
    """Rough wall-clock estimate shown to the operator. Defaults to
    5 — interviews longer than that should probably be split."""

    allow_followup: bool = True
    """When True, the interviewer reviews the operator's answers and
    may ship one follow-up question batch if there are gaps before
    closing. Set False for terse, no-revisit interviews where the
    initial batch is the entire conversation."""


# --------------------------------------------------------------------- #
# Answer shape — what comes back from the operator
# --------------------------------------------------------------------- #


class InterviewAnswer(BaseModel):
    """One answered question. Free_response is the operator's escape
    text — present alongside the structured value (or instead of it
    if the operator skipped the form widget entirely). Both halves
    are seen by the interviewer when ranking."""

    question_id: str = Field(min_length=1)
    value: str | list[str] | float | None = None
    """Structured value typed by the question's kind. None when the
    operator left the form blank but might still have free-response
    text — the interviewer should treat empty-value-plus-free-response
    as 'operator answered in prose'."""

    free_response: str = ""
    """The operator's escape text on this question. Always populated
    when the operator opened the free-response box; may be empty when
    they only used the structured widget."""

    skipped: bool = False
    """When True, the operator hit 'skip section' on the whole
    interview OR explicitly skipped this question. The interviewer
    should NOT ship a requirement for a skipped question — operator
    intent is 'I have nothing to say here', not 'I have nothing to
    say that I'd accept in the registry'."""


class InterviewAnswers(BaseModel):
    """The full batch of answers an operator submits to one
    interview's pending_interview.json. Carries the interview_id so
    the substrate routes the answers back to the right interviewer
    on its next turn."""

    interview_id: str = Field(min_length=1)
    answers: list[InterviewAnswer] = Field(default_factory=list)
    section_skipped: bool = False
    """Operator chose 'skip section' — close the interview immediately
    without follow-up. The interviewer ships nothing and moves on."""


# --------------------------------------------------------------------- #
# Requirement artifact — what interviews ship
# --------------------------------------------------------------------- #


class RequirementKind(StrEnum):
    """The category of requirement an artifact represents. Drives
    which downstream meetings seed from it: persona / situation feed
    M1 + M2; constraint / integration feed M4 + M5; scope /
    success_criterion / out_of_scope feed M2 + M8.

    Kept as a closed enum so downstream seed filters can dispatch on
    membership without string-matching open-ended categories. Add
    new kinds here when discovery surfaces something the existing
    set can't express.
    """

    PERSONA = "persona"
    """Who uses the system. Named individual + role + context, not
    'the user'."""
    SITUATION = "situation"
    """When the persona reaches for this. What just happened."""
    CONSTRAINT = "constraint"
    """Technical or operational constraint — stack choice, host,
    framework, anything that limits the solution space."""
    INTEGRATION = "integration"
    """External system this needs to talk to — service, API, file
    format, OS surface."""
    SCOPE = "scope"
    """A piece that's in for v1. Pairs with out_of_scope as the dual."""
    SUCCESS_CRITERION = "success_criterion"
    """Observable signal that v1 is done. Concrete enough to test."""
    OUT_OF_SCOPE = "out_of_scope"
    """A piece that's explicitly NOT v1 — guards against scope
    creep when downstream meetings might otherwise propose it."""
    DEAL_BREAKER = "deal_breaker"
    """Something that would make the project a failure regardless of
    features. Surfaces hidden constraints the operator hadn't named
    until asked."""


class RequirementAxis(StrEnum):
    """T-ab15 — orthogonal axis to RequirementKind, classifying the
    requirement by infrastructure-vs-user-facing orientation.

    The existing ``kind`` taxonomy (persona, situation, constraint,
    integration, scope, success_criterion, behavior, ...) describes
    WHAT SHAPE the requirement is. The axis describes WHICH
    DIRECTION it points:

      - ``foundation`` — about the substrate, contracts, plumbing,
        developer/operator concerns. A constraint about SQLite
        choice, a success_criterion about "persistence contract
        verified," an integration with a markdown renderer library.
        Consumed by foundation-kind milestones.

      - ``capability`` — about user-visible behavior, persona
        outcomes, end-user-observable signals. A success_criterion
        about "Kohl finds notes by phrase," a behavior about
        "user can edit notes." Consumed by capability-kind
        milestones.

      - ``both`` — applies across both contexts. Persona
        requirements typically have this axis (they ground every
        milestone). Cross-cutting scope statements similarly.
        Default for legacy / pre-axis requirements (back-compat
        — the validator treats ``both`` permissively).

    The substrate's milestone kind-consistency check (T-ab14) reads
    this axis to determine whether a foundation milestone is
    legitimately consuming a capability-axis requirement (an error)
    or a both-axis one (fine).
    """

    FOUNDATION = "foundation"
    CAPABILITY = "capability"
    BOTH = "both"


class Confidence(StrEnum):
    """How the requirement got into the registry. operator_stated
    means the operator named this directly in an interview;
    interviewer_inferred means an interviewer agent (typically in
    the backfill flow) read existing project state and inferred the
    requirement without operator confirmation.

    Downstream meetings can dispatch on confidence — e.g. M5
    contract negotiation might choose to surface a question to the
    operator before committing to a constraint the substrate
    inferred but the operator never confirmed.
    """

    OPERATOR_STATED = "operator_stated"
    INTERVIEWER_INFERRED = "interviewer_inferred"


class RequirementPayload(BaseModel):
    """Structured payload an interviewer attaches to a ``requirement``
    utterance. One requirement per answered question is the typical
    shape, but a single rich answer can split into multiple
    requirements (a single persona answer might emit one
    ``persona`` + one ``situation`` requirement) at the
    interviewer's discretion."""

    guid: str = Field(default_factory=new_artifact_guid)
    """P18 — stable Requirement identity. Interviewer re-emits with
    same guid to update an existing requirement; new guid creates
    new. Cross-references (story.realizes_requirements,
    milestone.consumes_requirements) cite guid; phantom slug
    references become substrate-detectable rather than silent
    drift."""

    title: str = Field(min_length=1)
    """Short specific title — the requirement summarized in a phrase.
    'Maya: end-of-day translation triage' beats 'persona 1'."""

    interview_id: str = Field(min_length=1)
    """Which interview produced this. Routes back to the source for
    audit / regeneration."""

    question_id: str = Field(min_length=1)
    """Which question's answer this requirement came out of. May be
    the synthetic id ``inferred`` when confidence is
    interviewer_inferred."""

    kind: RequirementKind
    """Category — drives downstream seed dispatch."""

    axis: RequirementAxis = RequirementAxis.BOTH
    """T-ab15 — foundation/capability orientation, orthogonal to
    ``kind``. The same kind can be foundation-oriented (a
    success_criterion about persistence verified) or capability-
    oriented (a success_criterion about user-visible behavior).
    Drives the T-ab14 milestone kind-consistency check; legacy
    requirements default to ``both`` for permissive back-compat
    (validator doesn't reject milestones consuming both-axis
    requirements regardless of milestone kind)."""

    body: str = Field(min_length=1)
    """The structured claim — the interviewer's rendering of what the
    operator said into a stable requirement statement. Typically 1-3
    sentences. Body is what downstream meetings READ; operator_quote
    is what they CITE."""

    operator_quote: str = ""
    """Raw operator answer text preserved verbatim for traceability.
    Empty for inferred requirements (the backfill flow has no quote
    to preserve — the inference itself goes in body)."""

    confidence: Confidence = Confidence.OPERATOR_STATED
    """Provenance — operator_stated vs interviewer_inferred. See
    Confidence docstring for the semantics."""


# --------------------------------------------------------------------- #
# On-disk record + renderer
# --------------------------------------------------------------------- #


@dataclass(frozen=True)
class RequirementRecord:
    number: int
    guid: str
    slug: str
    title: str
    kind: RequirementKind
    confidence: Confidence
    path: Path
    axis: RequirementAxis = RequirementAxis.BOTH

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_requirement(
    number: int, payload: RequirementPayload
) -> str:
    """Render a RequirementPayload as the markdown that lands on
    disk. Same shape as the other registry markdown — title heading,
    bold field labels, body sections. Operator quote sits below the
    body so a human reading the file sees the structured claim first
    and the raw quote for context.

    ``**Slug:**`` ships inline so downstream meetings (milestone-plan,
    tdd-design) that reference requirements by slug can extract them
    from the body without filename round-tripping. Mirrors the
    Milestone markdown shape.
    """
    # Slug derives from title via slugify — same call the registry's
    # write() uses to choose the filename. Including it in the body
    # makes the canonical id available wherever the body is read.
    slug = slugify(payload.title)
    lines: list[str] = [
        f"## Requirement {number:03d}: {payload.title}",
        "",
        f"**GUID:** {payload.guid}",
        f"**Slug:** {slug}",
        f"**Kind:** {payload.kind.value}",
        f"**Axis:** {payload.axis.value}",
        f"**Confidence:** {payload.confidence.value}",
        f"**Source interview:** {payload.interview_id}",
        f"**Source question:** {payload.question_id}",
        "",
        "**Body:**",
        "",
        payload.body.rstrip(),
        "",
    ]
    if payload.operator_quote.strip():
        lines.extend(
            [
                "**Operator quote:**",
                "",
                "> " + payload.operator_quote.rstrip().replace(
                    "\n", "\n> "
                ),
                "",
            ]
        )
    return "\n".join(lines)


# --------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------- #


class RequirementRegistry:
    """Read/write registry over ``<project_root>/.wonderland/requirements/``.
    Same shape as ADR / Story / Ticket / TestScenario registries:
    filesystem-scan numbering, slug-from-title, tolerant of unrelated
    files in the directory.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / REQUIREMENTS_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    def list_requirements(self) -> list[RequirementRecord]:
        if not self._root.is_dir():
            return []
        records: list[RequirementRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def list_by_kind(
        self, kind: RequirementKind
    ) -> list[RequirementRecord]:
        return [r for r in self.list_requirements() if r.kind == kind]

    def list_by_interview(
        self, interview_id: str
    ) -> list[RequirementRecord]:
        """Parse files to find requirements tagged with a given
        interview_id. Used by the interviewer when reviewing what's
        already shipped before deciding on follow-ups."""
        out: list[RequirementRecord] = []
        for record in self.list_requirements():
            try:
                text = record.path.read_text(encoding="utf-8")
            except OSError:
                continue
            if f"**Source interview:** {interview_id}" in text:
                out.append(record)
        return out

    def next_number(self) -> int:
        existing = self.list_requirements()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_guid(self, guid: str) -> RequirementRecord | None:
        """P18 T-g2 — primary identity lookup."""
        if not guid:
            return None
        for record in self.list_requirements():
            if record.guid == guid:
                return record
        return None

    def find_by_slug(self, slug: str) -> RequirementRecord | None:
        for record in self.list_requirements():
            if record.slug == slug:
                return record
        return None

    def find_by_number(
        self, number: int
    ) -> RequirementRecord | None:
        for record in self.list_requirements():
            if record.number == number:
                return record
        return None

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #

    def write(
        self, payload: RequirementPayload | dict
    ) -> RequirementRecord:
        validated = (
            payload
            if isinstance(payload, RequirementPayload)
            else RequirementPayload.model_validate(payload)
        )

        slug = slugify(validated.title)
        # T-g2: guid-first lookup; slug fallback for back-compat.
        existing = self.find_by_guid(validated.guid)
        if existing is None:
            existing = self.find_by_slug(slug)

        if existing is not None:
            number = existing.number
            full_path = existing.path
        else:
            number = self.next_number()
            # T-g3: filename embeds short_guid for substrate identity.
            filename = f"requirement-{short_guid(validated.guid)}-{slug}.md"
            full_path = self._root / filename

        if existing is not None and existing.guid:
            validated = validated.model_copy(update={"guid": existing.guid})

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(
            render_requirement(number, validated), encoding="utf-8"
        )
        return RequirementRecord(
            number=number,
            guid=validated.guid,
            slug=slug,
            title=validated.title,
            kind=validated.kind,
            confidence=validated.confidence,
            path=full_path,
            axis=validated.axis,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _record_from_path(path: Path) -> RequirementRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        id_part = match.group("id")
        slug = match.group("slug")
        title, kind, confidence, axis = (
            RequirementRegistry._fields_from_file(
                path, fallback_title=slug
            )
        )
        guid = RequirementRegistry._guid_from_file(path)
        number = RequirementRegistry._number_from_file(path, id_part)
        return RequirementRecord(
            number=number,
            guid=guid,
            slug=slug,
            title=title,
            kind=kind,
            confidence=confidence,
            path=path,
            axis=axis,
        )

    @staticmethod
    def _number_from_file(path: Path, id_part: str) -> int:
        """T-g3 — legacy filenames carried number in the id slot;
        new-shape files keep it only in the H2 header."""
        if id_part.isdigit():
            return int(id_part)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return 0
        m = _NUMBER_FROM_H2.search(text)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _guid_from_file(path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return new_artifact_guid()
        m = _GUID_PATTERN.search(text)
        return m.group(1) if m else new_artifact_guid()

    @staticmethod
    def _fields_from_file(
        path: Path, *, fallback_title: str
    ) -> tuple[str, RequirementKind, Confidence, RequirementAxis]:
        """Parse the first few lines for title + kind + confidence
        + axis. Falls back to safe defaults for files the writer
        didn't produce (e.g. operator-edited markdown that lost a
        header). Legacy requirements without ``**Axis:**`` line
        default to ``RequirementAxis.BOTH`` — permissive back-compat
        so the T-ab14 validator doesn't reject milestones consuming
        pre-T-ab15 requirements."""
        title = fallback_title
        kind = RequirementKind.SCOPE  # safe default
        confidence = Confidence.OPERATOR_STATED
        axis = RequirementAxis.BOTH
        try:
            with path.open(encoding="utf-8") as f:
                lines = [f.readline() for _ in range(10)]
        except OSError:
            return title, kind, confidence, axis
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## Requirement"):
                if ":" in stripped:
                    title = stripped.split(":", 1)[1].strip() or title
            elif stripped.startswith("**Kind:**"):
                raw = stripped.removeprefix("**Kind:**").strip()
                try:
                    kind = RequirementKind(raw)
                except ValueError:
                    pass
            elif stripped.startswith("**Axis:**"):
                raw = stripped.removeprefix("**Axis:**").strip()
                try:
                    axis = RequirementAxis(raw)
                except ValueError:
                    pass
            elif stripped.startswith("**Confidence:**"):
                raw = stripped.removeprefix("**Confidence:**").strip()
                try:
                    confidence = Confidence(raw)
                except ValueError:
                    pass
        return title, kind, confidence, axis


# --------------------------------------------------------------------- #
# Disk-mediated bridge — paired write + wait helpers
# --------------------------------------------------------------------- #


def write_pending_interview(
    run_dir: Path,
    interview: Interview,
    *,
    batch_id: str | None = None,
) -> str:
    """Serialize an Interview's question batch to
    ``<run_dir>/pending_interview.json`` so the TUI's interview
    poller can surface the InterviewModal. Returns the
    ``batch_id`` written into the file — a fresh uuid by default,
    overridable for tests.

    The on-disk shape is intentionally flat (interview metadata +
    a serialized question list) so the TUI can render directly
    without re-instantiating the Pydantic models. The substrate
    side uses ``batch_id`` to disambiguate this batch's answers
    from any stale answers file left over from a prior
    follow-up round.
    """
    bid = batch_id or uuid.uuid4().hex
    payload = {
        "batch_id": bid,
        "interview_id": interview.id,
        "label": interview.label,
        "name": interview.name,
        "interviewer": interview.interviewer,
        "goal": interview.goal,
        "estimated_minutes": interview.estimated_minutes,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "kind": q.kind.value,
                "required": q.required,
                "options": list(q.options),
            }
            for q in interview.questions
        ],
    }
    path = run_dir / PENDING_INTERVIEW_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return bid


async def await_interview_answers(
    run_dir: Path,
    *,
    batch_id: str,
    timeout_seconds: float = _DEFAULT_INTERVIEW_TIMEOUT_SECONDS,
    poll_seconds: float = _INTERVIEW_POLL_SECONDS,
) -> InterviewAnswers | None:
    """Block waiting for the TUI to write
    ``<run_dir>/pending_interview_answers.json`` matching this
    batch's ``batch_id``. Returns the parsed ``InterviewAnswers``
    on success, ``None`` on timeout / malformed file / no TUI
    attached.

    On success, BOTH the pending_interview.json and
    pending_interview_answers.json files are cleaned up on the way
    out — same lifecycle as the question bridge. The interview is
    "consumed" by the operator's submission.

    Stale answer files (a different batch_id, typically from a
    crashed prior follow-up) are deleted on detection so they don't
    trip the next iteration.
    """
    question_path = run_dir / PENDING_INTERVIEW_FILENAME
    answer_path = run_dir / PENDING_INTERVIEW_ANSWERS_FILENAME

    deadline = asyncio.get_running_loop().time() + timeout_seconds
    answers: InterviewAnswers | None = None
    try:
        while asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(poll_seconds)
            if not answer_path.is_file():
                continue
            try:
                raw = json.loads(
                    answer_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError):
                continue
            if raw.get("batch_id") != batch_id:
                # Stale answers file from a prior batch — clean up
                # and keep waiting for this batch's actual answers.
                try:
                    answer_path.unlink()
                except OSError:
                    pass
                continue
            try:
                answers = InterviewAnswers.model_validate(
                    {
                        "interview_id": raw.get("interview_id", ""),
                        "answers": raw.get("answers", []),
                        "section_skipped": raw.get(
                            "section_skipped", False
                        ),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                print(
                    f"warn: failed to parse interview answers: {exc}",
                    file=sys.stderr,
                )
                # Treat as malformed: clean up + keep waiting in case
                # the TUI writes a corrected version, but realistically
                # the operator can't easily retry from their side.
                try:
                    answer_path.unlink()
                except OSError:
                    pass
                continue
            break
    finally:
        for path in (question_path, answer_path):
            try:
                path.unlink()
            except OSError:
                pass
    return answers


__all__ = [
    "Confidence",
    "Interview",
    "InterviewAnswer",
    "InterviewAnswers",
    "InterviewQuestion",
    "PENDING_INTERVIEW_ANSWERS_FILENAME",
    "PENDING_INTERVIEW_FILENAME",
    "QuestionKind",
    "RequirementKind",
    "RequirementPayload",
    "RequirementRecord",
    "RequirementRegistry",
    "REQUIREMENTS_DIRNAME",
    "await_interview_answers",
    "render_requirement",
    "write_pending_interview",
]
