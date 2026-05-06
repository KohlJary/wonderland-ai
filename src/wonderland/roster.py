"""ThreadRoster — per-thread membership tracking for scoped meetings.

Per the P6.T36 prep architectural shift (analysis 011): the original
"every agent on every utterance" model produced a vertical pipeline
blockage where Cat refused to ship ADRs because Queen kept ratifying
the deferral. With a roster model, the Queen isn't in the scoping
meeting until something triggers a buzz-in, so she can't construct the
deferral chain in the first place.

Conceptual model:

- A **thread** has a roster (set of agent names) and an optional goal.
- An **open thread** (not registered) has no roster; everyone sees it.
  This is the backward-compatible default — existing demos that don't
  register thread rosters keep their current "everyone listens" shape.
- A **rostered thread** delivers utterances only to agents in its
  roster. Non-members never see the messages, so they don't engage,
  so they don't pay LLM cost.
- The **convenor** records who started the meeting (typically the
  Dodo for orchestration, but not always — Tweedles can convene a
  contract negotiation between themselves).

Mutability is intentional: rosters change as meetings buzz-in
participants. The roster is a live registry, not an immutable record.

This module owns *only* the data structure. Bus integration (filtering
on publish) lives in `Caucus`; convene/invite mechanics live in the
agents / Runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ThreadRoster:
    """Live registry mapping thread_id → (members, goal, convenor).

    Threads that haven't been registered are *open* — every agent sees
    them. This keeps existing single-thread demos working unchanged.
    Once a thread is registered, only its members see its utterances.

    All operations are synchronous; the registry holds in-process state
    that the bus and Runner consult during publish + lifecycle. If we
    ever distribute the bus (Redis), the roster will need a serialized
    representation too — for now it's local to the Runner instance.
    """

    _rosters: dict[str, set[str]] = field(default_factory=dict)
    _goals: dict[str, str] = field(default_factory=dict)
    _convenors: dict[str, str] = field(default_factory=dict)

    def register(
        self,
        thread_id: str,
        *,
        members: set[str] | list[str] | tuple[str, ...],
        goal: str = "",
        convenor: str = "",
    ) -> None:
        """Register a new rostered thread. Idempotent on identical input —
        a re-register with the same members + goal is a no-op rather than
        an error so callers don't have to track 'have I registered this
        thread' state. Different members on re-register raises ValueError
        so we surface accidental roster overwrites loudly.
        """
        new_members = set(members)
        if thread_id in self._rosters:
            if self._rosters[thread_id] != new_members:
                raise ValueError(
                    f"thread {thread_id!r} already has roster "
                    f"{sorted(self._rosters[thread_id])}; refusing to overwrite "
                    f"with {sorted(new_members)}. Use add_member / remove_member "
                    "for incremental changes."
                )
            return
        self._rosters[thread_id] = new_members
        self._goals[thread_id] = goal
        self._convenors[thread_id] = convenor

    def is_open(self, thread_id: str) -> bool:
        """True when ``thread_id`` has not been registered with a roster.

        Open threads deliver to all subscribers — the backward-compatible
        default that lets existing single-thread demos keep working.
        """
        return thread_id not in self._rosters

    def is_member(self, thread_id: str, agent_name: str) -> bool:
        """True when ``agent_name`` should receive utterances on ``thread_id``.

        Open threads return True for everyone. Rostered threads return
        True only when the agent is explicitly listed. The bus consults
        this on publish to decide who gets the utterance.
        """
        if self.is_open(thread_id):
            return True
        return agent_name in self._rosters[thread_id]

    def add_member(self, thread_id: str, agent_name: str) -> None:
        """Buzz-in: add an agent to a registered thread's roster.

        Raises KeyError if the thread isn't registered (you can't buzz
        into an open thread — open threads already include everyone).
        Idempotent if the agent is already a member.
        """
        if thread_id not in self._rosters:
            raise KeyError(
                f"thread {thread_id!r} is open (no roster registered); "
                "buzz-in only applies to scoped meetings"
            )
        self._rosters[thread_id].add(agent_name)

    def remove_member(self, thread_id: str, agent_name: str) -> None:
        """Drop an agent from a thread's roster (the inverse of buzz-in).

        Raises KeyError if the thread isn't registered. Idempotent if
        the agent isn't currently a member.
        """
        if thread_id not in self._rosters:
            raise KeyError(
                f"thread {thread_id!r} is open (no roster registered); nothing to remove from"
            )
        self._rosters[thread_id].discard(agent_name)

    def members(self, thread_id: str) -> frozenset[str]:
        """Snapshot of the current roster. Empty frozenset for open threads."""
        return frozenset(self._rosters.get(thread_id, set()))

    def goal(self, thread_id: str) -> str:
        """Goal string for a registered thread; empty string otherwise."""
        return self._goals.get(thread_id, "")

    def convenor(self, thread_id: str) -> str:
        """Name of the agent that convened the thread; empty string otherwise."""
        return self._convenors.get(thread_id, "")

    def threads(self) -> list[str]:
        """All registered thread ids, in registration order."""
        return list(self._rosters.keys())


__all__ = ["ThreadRoster"]
