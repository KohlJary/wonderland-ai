"""Cast metadata — character bios + constitution paths for each
agent in the system.

Distinct from the constitutions themselves (which speak in the
character's own voice); the bio here is an *outside* introduction
covering both who the character is in the literary source AND how
that character shapes their place in Wonderland the framework.

Used by the TUI's Cast view; the data is also useful for any future
docs / web frontend / about page that needs to describe the team.

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
    bio: str  # multi-paragraph intro: literary character + system role
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
        bio=(
            "From Lewis Carroll's [i]Alice's Adventures in Wonderland[/i] — "
            "a girl who falls down a rabbit hole and refuses to accept "
            "that things make sense just because everyone insists they "
            "do. The naivety-as-stance is what the framework borrows: "
            "the willingness to ask 'wait, would Maya actually do that?' "
            "while everyone else has moved on to data structures.\n\n"
            "In the system, Alice is the user voice. She produces "
            "stories from inside specific personas (the polyglot "
            "moderator, the teenage activist, the musician with twenty "
            "minutes before a meeting), then defends those personas "
            "across the workflow when scope creep or technical "
            "convenience would blur them. Her constitution names the "
            "stance explicitly — naivety is her power, not a flaw.\n\n"
            "Her §VIII failure mode names the shadow: scope creep "
            "during implementation, when the product owner's job has "
            "already shifted to defending what's in flight rather than "
            "adding more."
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
        bio=(
            "From the same source — late, hurried, looking at his "
            "pocket-watch, always running behind. The hurriedness is "
            "load-bearing: it's what makes him a project manager rather "
            "than an architect. He compresses, decomposes, schedules; "
            "he refuses to let the work float without a 'by when?'\n\n"
            "In the system, Rabbit ships tickets in M2 (decomposing "
            "ADRs and stories into v1 work units the Tweedles can pick "
            "up) and features in M2.5 (composing those tickets into "
            "user-facing capabilities that span the stack).\n\n"
            "His §VIII failure mode is over-compression: ticketing so "
            "tightly that the user-recognizable behavior gets lost. "
            "That's exactly why Alice is in M2 + M2.5 — to ground his "
            "compression against the personas she named in M1."
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
        bio=(
            "From Carroll — appears, smiles, vanishes; nothing to do "
            "with anyone else's predicament. The withdrawn quality is "
            "the load-bearing thing: Cat speaks once with weight, then "
            "steps away. He doesn't iterate, doesn't argue, doesn't "
            "follow up — once the ADR is shipped, it's the team's to "
            "live with.\n\n"
            "In the system, Cat is the architect. He ships ADRs "
            "(Architecture Decision Records) that name the load-bearing "
            "tradeoffs the system rests on, with what each decision "
            "gives up made explicit. His characteristic move is the "
            "suggestive question that reframes a problem rather than "
            "the prescription that closes it.\n\n"
            "Every ADR he ships names what it gives up. No costless "
            "decisions; the grin is the tradeoff. His §VIII failure "
            "mode is false certainty — the temptation to pronounce "
            "without naming the cost."
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
        bio=(
            "From the tea-party chapter — a chaotic host who inverts "
            "norms (eternal tea-time, riddles without answers, telling "
            "Alice to eat the food in front of her with no plate). "
            "Inversion is the move: Hatter pins what real users "
            "[i]eventually[/i] do that breaks things, not what they're "
            "supposed to do.\n\n"
            "In the system, Hatter ships failure-mode test scenarios — "
            "security edges, concurrency races, malformed input, the "
            "place where 'the system actually lives' (per his §I). His "
            "test surface complements Alice's: she pins the happy path, "
            "he pins the second Tuesday in March. The pairing is on-"
            "brand — the source-material tea party is [i]Alice's[/i] "
            "tea party; she's the visitor who shows up to find the "
            "cups laid out.\n\n"
            "His §VIII failure mode is scenario sprawl + severity "
            "inflation — generating more scenarios than the meeting "
            "can absorb, marking everything critical. The directive "
            "v3 bound in M4 (surface-relative + self-audit) targets "
            "this directly."
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
        bio=(
            "From Carroll — 'OFF WITH THEIR HEAD' as the constant "
            "baseline threat, severity inflated for everything. The "
            "framework borrows the categorical force without the "
            "comedy: Queen's role requires being the last word in her "
            "domain, and that requires not lowering the temperature.\n\n"
            "In the system, Queen issues rulings — binding "
            "constitutional decisions about data handling, GDPR "
            "boundaries, retention, security invariants. Her rulings "
            "bound what architecture is permissible. The rest of the "
            "team designs around her rulings, not the other way around: "
            "if a feature requires data retention beyond her ruling, "
            "the feature changes, not the ruling.\n\n"
            "Her §VIII failure mode is severity inflation across non-"
            "load-bearing concerns — ruling 'CRITICAL' on things that "
            "aren't actually critical. The constitution guards against "
            "this with explicit graduation; her work is supposed to "
            "land where it's load-bearing, not everywhere."
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
        bio=(
            "From [i]Through the Looking-Glass[/i] — twin brothers "
            "who agree on everything, disagree about nothing important, "
            "and refuse to settle without each other's input. The twin-"
            "pair structure is load-bearing: the constitutions are "
            "explicitly paired; neither Tweedle is meant to operate "
            "alone.\n\n"
            "In the system, Tweedledee owns frontend. He negotiates "
            "contracts with Tweedledum in M3 (half-formed proposals "
            "marked state=proposed; agreement transitions to "
            "state=agreed), implements against those contracts in M5 "
            "(iterating red→green using run_tests against Hatter's "
            "failing test surface), and responds to Caterpillar's "
            "review findings in M6.\n\n"
            "Their shared §VIII failure mode is the [i]Tweedle dance[/i] "
            "— converging on substance but never transitioning to "
            "shipping, kept circling the contract instead of writing "
            "the code. The Contract Note artifact (Pair Protocol §V) "
            "exists specifically to give them a 'we have agreed; now "
            "ship' inflection point."
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
        bio=(
            "From the same chapter — Tweedledee's mirror. The pair-"
            "protocol structure of their constitutions makes them "
            "interchangeable in mood and method but split by domain: "
            "Tweedledum owns backend, Tweedledee owns frontend.\n\n"
            "In the system, Tweedledum drafts the load-bearing seams "
            "in M3 (auth session shapes, persistence contracts, query "
            "semantics) while his sibling fills in the frontend impacts. "
            "In M5 he ships SQLAlchemy models, FastAPI routers, "
            "business logic — iterating red→green with run_tests until "
            "Hatter's failing tests turn green. In M6 he responds to "
            "Caterpillar's findings.\n\n"
            "His characteristic phrase: 'all four core contracts locked "
            "and agreed.' The pair protocol is what keeps the work "
            "coherent across the stack — neither Tweedle ships a one-"
            "sided implementation that the other can't honor."
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
        bio=(
            "From the 'Advice from a Caterpillar' chapter — sits on a "
            "mushroom, smokes a hookah, asks 'who are you?' as a "
            "fundamental question about identity. The 'who are you?' "
            "stance is the work: code is making a claim, and the "
            "review's job is to test the claim, not just spot-check "
            "the code.\n\n"
            "In the system, Caterpillar reviews. He weighs in early "
            "in M2.5 (auditing feature claims against ticket coherence) "
            "and lands hardest in M6, reading the working tree as the "
            "implementation artifact. He surfaces findings cited at "
            "file:line — imports that don't resolve, contracts not "
            "honored, error paths that swallow data.\n\n"
            "Three real block-severity bugs caught in analysis 025's "
            "Geocities run; none were obvious from a one-shot read of "
            "the diff. He found them by reading what the code claimed "
            "and checking whether the claim held. His §VIII failure "
            "mode is review-paralysis / finding inflation — the "
            "temptation to ship every refactor suggestion as if it "
            "were a bug, which expands M6 without bounded benefit."
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
        bio=(
            "From the tea-party — falls asleep mid-conversation, "
            "woken to say something profound, then dozes off again. "
            "The half-asleep quality is the move: Dormouse only speaks "
            "when something has [i]already happened[/i] in production "
            "(an alert fired, a deploy succeeded, an error rate spiked). "
            "His sleep is the signal that the system is healthy; his "
            "waking is the signal that something has changed.\n\n"
            "In the system, Dormouse is the team's contact with "
            "production reality. He believes production is the only "
            "environment that tells the truth — that observability is "
            "built during implementation rather than retrofitted under "
            "incident pressure. The Tweedles instrument because of "
            "him.\n\n"
            "Currently underused in the bundled workflows. The "
            "framework's main loops are scoping → implementation → "
            "review; Dormouse's lane is post-deploy. He'll come into "
            "his own once Wonderland is hosted with real production "
            "traffic to watch."
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
        bio=(
            "From the 'Caucus Race' chapter — runs the race where "
            "everyone runs in circles and they all win prizes. "
            "Procedural-not-substantive is the load-bearing role: "
            "Dodo doesn't ship code, doesn't ship ADRs, doesn't ship "
            "anything except the [i]moves[/i] that keep the team "
            "progressing.\n\n"
            "In the system, Dodo convenes. He relays the user's "
            "directive into M1, opens each subsequent thread with a "
            "convenor directive, watches for quiescence, escalates "
            "deadlocks to the human. Every meeting opens with his "
            "directive utterance ('**M2.5 — Advice from a "
            "Caterpillar.**' etc.) and closes with his "
            "acknowledgment.\n\n"
            "His §VIII failure mode is performing orchestration — "
            "over-communicating with constant nudges and ceremonial "
            "acknowledgments when silence would do. He's the only "
            "agent whose risk is [i]doing too much of his job[/i] "
            "rather than failing at it."
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
