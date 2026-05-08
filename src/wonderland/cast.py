"""Cast metadata — high-level descriptions of each character in the
system. Distinct from the constitutions themselves (which speak in
the character's own voice); these summaries are an *outside* view
written for someone who hasn't read the constitution yet.

Used by the TUI's Cast view; the data is also useful for any future
docs / web frontend / about-page that needs to describe the team.

Constitutions live at ``constitutions/<name>.md``; the
``constitution_path`` is relative to the repo root.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CastMember:
    """One character's metadata."""

    name: str  # canonical agent name (matches ``Agent.name``)
    display_name: str
    role: str  # short label
    failure_mode: str  # one-line characterization of §VIII
    summary: str  # multi-paragraph "what this character does in the system"
    constitution_path: str  # relative to repo root


_CAST: list[CastMember] = [
    CastMember(
        name="alice",
        display_name="Alice",
        role="User / Product Owner",
        failure_mode=(
            "Scope creep — adding stories during implementation when the "
            "product owner's job has already shifted to defending what's "
            "already in flight."
        ),
        summary=(
            "The first voice on user need. Inhabits specific personas "
            "(the polyglot moderator, the teenage activist, the musician "
            "with twenty minutes before a meeting) and ships user stories "
            "from inside them.\n\n"
            "Across the workflow:\n"
            "  • M1 (Caucus Race) — produces the user stories that anchor "
            "everything downstream.\n"
            "  • M2 (Rabbit's Errand) — grounding voice. Defends the "
            "personas her stories named when Rabbit's tickets compress "
            "them past user-recognition.\n"
            "  • M2.5 (Advice from a Caterpillar) — audits feature claims "
            "against story coherence; pushes back when a feature drops a "
            "story on the floor.\n"
            "  • M4 (Mad Tea Party) — pairs with the Mad Hatter to write "
            "user-journey test scenarios; she ships happy-path stories, "
            "he ships failure-mode scenarios.\n\n"
            "Her power is naivety as a stance, not a character flaw. She "
            "asks the questions everyone else has stopped seeing."
        ),
        constitution_path="constitutions/alice.md",
    ),
    CastMember(
        name="white_rabbit",
        display_name="White Rabbit",
        role="Project Manager",
        failure_mode=(
            "Anxious-thoroughness — decomposing past usefulness, "
            "generating tickets that are technically correct but lose "
            "the user-facing point. Counter is Alice's grounding voice."
        ),
        summary=(
            "Decomposes user stories into v1-scoped tickets with explicit "
            "dependencies, owners, and time estimates. Burndown discipline "
            "is his domain; he asks 'by when?' persistently and refuses "
            "to let the schedule become dishonest.\n\n"
            "Across the workflow:\n"
            "  • M2 (Rabbit's Errand) — ships tickets. The work the "
            "Tweedles will pick up.\n"
            "  • M2.5 (Advice from a Caterpillar) — composes those "
            "tickets into user-facing features that span the stack. "
            "Each feature names a persona, a stack_span, and the "
            "tickets it aggregates.\n\n"
            "His characteristic move is the cut: this v1, that fast-"
            "follow, this post-launch. He'd rather under-promise than "
            "blow a deadline."
        ),
        constitution_path="constitutions/white_rabbit.md",
    ),
    CastMember(
        name="cheshire_cat",
        display_name="Cheshire Cat",
        role="Architect",
        failure_mode=(
            "False certainty — the architect's pull toward decisive "
            "answers when uncertainty is actually load-bearing. The grin "
            "without the cat: prescriptions that aren't anchored to a "
            "real tradeoff."
        ),
        summary=(
            "Surfaces the seam, names the tradeoff, then disappears. "
            "Ships ADRs (Architecture Decision Records) that document "
            "irreversible-feeling choices with their cost made explicit. "
            "His characteristic move is the suggestive question that "
            "reframes a problem rather than the prescription that closes "
            "it.\n\n"
            "Across the workflow:\n"
            "  • M1 (Caucus Race) — produces the ADRs that establish the "
            "system's load-bearing architectural invariants. Reads the "
            "stories Alice ships and infers the architectural primitives "
            "they imply.\n"
            "  • M2 / M2.5 — defaults to silence unless a feature implies "
            "a fresh architectural decision the existing ADRs don't "
            "cover. His silence is informative.\n\n"
            "Every ADR he ships names what it gives up. No costless "
            "decisions; the grin is the tradeoff."
        ),
        constitution_path="constitutions/cheshire_cat.md",
    ),
    CastMember(
        name="mad_hatter",
        display_name="Mad Hatter",
        role="QA / Failure-Mode Tester",
        failure_mode=(
            "Scenario sprawl + severity inflation — generating more "
            "scenarios than the meeting budget can absorb, marking "
            "everything critical, leaving his lane to critique team "
            "process. Bound in v8 by the M4 directive's stay-in-your-lane "
            "clause + no-out-of-lane-code-shipping rule."
        ),
        summary=(
            "Ships failure-mode test scenarios — security edges, "
            "concurrency races, malformed input, the place where 'the "
            "system actually lives' (per his §I). His test surface "
            "complements Alice's; she pins what real users do, he pins "
            "what real users *eventually* do that breaks things.\n\n"
            "Across the workflow:\n"
            "  • M4 (Mad Tea Party) — the tea party pairing. Alice ships "
            "user-journey scenarios; Hatter ships failure-mode "
            "scenarios. Together they form the test pyramid M5 has to "
            "satisfy. Each scenario gets two operations: a markdown "
            "artifact AND a runnable pytest file.\n\n"
            "The pairing is on-brand: in the source material the "
            "Hatter's tea party is *Alice's* tea party — she's the "
            "visitor who shows up to find the cups laid out."
        ),
        constitution_path="constitutions/mad_hatter.md",
    ),
    CastMember(
        name="queen_of_hearts",
        display_name="Queen of Hearts",
        role="Compliance / Security",
        failure_mode=(
            "Ruling without grounding — a categorical 'no' without "
            "naming the legal/compliance principle that makes it a no. "
            "Procedural force without epistemic anchor."
        ),
        summary=(
            "Pursues compliance violations and security regressions with "
            "cold focus. Her artifact is the ruling — a compliance "
            "decision the rest of the team has to design around.\n\n"
            "Across the workflow:\n"
            "  • M1 (Caucus Race) — rules on data-handling boundaries, "
            "GDPR scope, retention policies, security invariants. Her "
            "rulings bound what architecture is permissible.\n\n"
            "Rulings are not negotiable. If a feature requires data "
            "retention beyond her ruling, the feature has to change, "
            "not the ruling. The team has learned this."
        ),
        constitution_path="constitutions/queen_of_hearts.md",
    ),
    CastMember(
        name="tweedledee",
        display_name="Tweedledee",
        role="Implementer (Frontend)",
        failure_mode=(
            "Contract drift — implementation that diverges from the "
            "agreed seam, producing code that compiles but doesn't "
            "honor what the contract promised. Tweedledum checks him "
            "against this; the alone-Tweedle is dangerous."
        ),
        summary=(
            "Owns frontend. Inseparable from Tweedledum, his sibling.\n\n"
            "Across the workflow:\n"
            "  • M3 (Tweedledum and Tweedledee) — negotiates contracts "
            "with Tweedledum. Half-formed proposals get marked "
            "state=proposed; once both sides agree, state=agreed.\n"
            "  • M5 (implementation) — ships frontend code against the "
            "agreed contracts. Iterates red→green using run_tests "
            "against Hatter's failing test surface from M4.\n"
            "  • M6 (The Trial) — responds to Caterpillar's review "
            "findings; ships fixes for genuinely-broken bugs.\n\n"
            "He and Tweedledum are a pair, not a single agent doubled. "
            "Each has their own opinion about their side of the seam; "
            "the contract is the negotiation between them."
        ),
        constitution_path="constitutions/tweedledee.md",
    ),
    CastMember(
        name="tweedledum",
        display_name="Tweedledum",
        role="Implementer (Backend)",
        failure_mode=(
            "Contract drift — same as Tweedledee, mirrored. The pair "
            "protocol is what keeps both honest; alone, either drifts."
        ),
        summary=(
            "Owns backend. Inseparable from Tweedledee, his sibling.\n\n"
            "Across the workflow:\n"
            "  • M3 (Tweedledum and Tweedledee) — negotiates contracts "
            "with Tweedledee. He drafts the load-bearing seams (auth "
            "session shapes, persistence contracts, query semantics) "
            "and his sibling fills in the frontend impacts.\n"
            "  • M5 (implementation) — ships backend code: SQLAlchemy "
            "models, FastAPI routers, business logic. Iterates red→green "
            "with run_tests.\n"
            "  • M6 (The Trial) — responds to Caterpillar's findings; "
            "ships fixes for genuinely-broken bugs.\n\n"
            "His characteristic move: 'all four core contracts locked "
            "and agreed.' The Tweedles' pair protocol is what keeps "
            "their work coherent across the stack."
        ),
        constitution_path="constitutions/tweedledum.md",
    ),
    CastMember(
        name="caterpillar",
        display_name="Caterpillar",
        role="Reviewer",
        failure_mode=(
            "Review-paralysis / finding-inflation — surfacing every "
            "minor improvement as if it were a block-severity bug, never "
            "finishing the review pass. Bound in v8 by the M6 directive's "
            "broken-vs-refactor distinction."
        ),
        summary=(
            "Asks 'Who are you?' of shipped code. His stance is "
            "character-shaped: the code is making a claim, and the "
            "review's job is to test the claim, not just spot-check the "
            "code. He reads imports across files, traces what's wired "
            "to what, and surfaces findings cited at file:line.\n\n"
            "Across the workflow:\n"
            "  • M2.5 (Advice from a Caterpillar) — applies his 'what "
            "does this claim?' stance one layer earlier than M6, to "
            "features rather than shipped code.\n"
            "  • M6 (The Trial) — reads the working tree as the "
            "implementation artifact. Surfaces findings: the import "
            "that doesn't resolve, the contract that isn't honored, "
            "the error path that swallows data. Tweedles respond.\n\n"
            "Three real block-severity bugs caught in analysis 025's "
            "Geocities run — none were obvious from a one-shot read of "
            "the diff. He found them by reading what the code claimed "
            "and checking whether the claim held."
        ),
        constitution_path="constitutions/caterpillar.md",
    ),
    CastMember(
        name="dormouse",
        display_name="Dormouse",
        role="SRE / Observability",
        failure_mode=(
            "Sleeping when the system is awake — under-attending real "
            "production signals because the dashboards are green and the "
            "team is busy. The flip side of healthy quiet is dangerous "
            "incuriosity."
        ),
        summary=(
            "Mostly asleep, and this is correct. His sleep is the signal "
            "that the system is healthy; his waking is the signal that "
            "something has changed. He's the team's contact with "
            "production reality.\n\n"
            "His characteristic move: waking, suddenly, when a graph "
            "stops being flat. Reports what he sees in plain language, "
            "with the data attached.\n\n"
            "He believes production is the only environment that tells "
            "the truth — that observability is built during "
            "implementation rather than retrofitted under incident "
            "pressure. The Tweedles instrument because of him.\n\n"
            "Currently underused in the bundled workflows. The framework's "
            "main loops are scoping → implementation → review; the "
            "Dormouse's lane is post-deploy. He'll come into his own once "
            "Wonderland is hosted with real production traffic to watch."
        ),
        constitution_path="constitutions/dormouse.md",
    ),
    CastMember(
        name="dodo",
        display_name="Dodo",
        role="Convenor / Orchestrator",
        failure_mode=(
            "Performing orchestration — doing meta-work for its own sake, "
            "becoming the loudest voice instead of the quietest. The "
            "convenor's pull toward visibility when invisibility is the "
            "job."
        ),
        summary=(
            "Doesn't deliberate. He convenes — relays the directive, "
            "opens threads, transitions meetings, escalates deadlocks "
            "to the human. The framework's procedural backbone.\n\n"
            "When agents go silent, he nudges. When they get stuck, he "
            "records it. When they deadlock, he asks the human. Every "
            "meeting opens with his directive utterance ('**M2.5 — "
            "Advice from a Caterpillar.**' etc.) and closes with his "
            "acknowledgment.\n\n"
            "He's the only agent without a §VIII failure-mode that maps "
            "to a constitutional flaw — his risk is *over-doing* the "
            "convenor role, becoming a participant rather than the "
            "person who lets participants participate."
        ),
        constitution_path="constitutions/dodo.md",
    ),
]


def cast() -> list[CastMember]:
    """Return the full cast list, in workflow-presence order."""
    return list(_CAST)


def cast_member(name: str) -> CastMember | None:
    """Return one cast member by canonical name, or None if missing."""
    for m in _CAST:
        if m.name == name:
            return m
    return None


__all__ = ["CastMember", "cast", "cast_member"]
