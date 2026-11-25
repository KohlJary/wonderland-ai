# Analysis 049: We hit the same wall. Silence, turn-taking, and how Wonderland built around it

**Date:** 2026-11-25
**Status:** A history and a proposed experiment. No new run; this collects analyses 009, 022, 023, 033, 035 and 039, and the code in `src/wonderland/turns.py`, `meeting.py` and `thread_monitor.py`.
**Prompted by:** Bhagtani, Anand, Xu and Yadav, *Speak or Stay Silent: Context-Aware Turn-Taking in Multi-Party Dialogue* (arXiv:2603.11409, v2 24 Nov 2026).

## Why this exists

*Speak or Stay Silent* asks, at every pause in a multi-party conversation, whether an AI assistant should speak or stay silent. Its authors evaluated eight LLMs on more than 120K labeled pauses, found that they "consistently fail at context-aware turn-taking under zero-shot prompting", and recovered up to 23 points of balanced accuracy with fine-tuning.

We ran into the same wall, from two directions, building Wonderland: a framework where teams of AI agents hold meetings and build software together. This is what happened to us and how we built around it, written up because the paper names the problem well, and because there's an experiment on their benchmark we'd like to run.

## Wall 1: when agents choose when to speak, they don't stop (analysis 009)

In our early engagement-policy model, any agent could speak whenever the conversation seemed to invite it. On a trivial directive (a script that prints a haiku), the team produced 84 visible utterances in 90 seconds, 56% of them `question` or `concern`, plus three ADRs about haiku immutability, and timed out at twice the budget. That's the paper's "speaks at every pause" failure, in agents talking to agents.

Two small edits to the framework primer cut visible utterances 6× and cost 4×, and the team converged. So prompting moved volume a lot. But we were still relying on each agent to judge, unprompted, when to self-select.

## Wall 2: when a moderator judges what silence means, it's wrong both ways (analyses 022, 023, 039)

The other half of our early design was the **Dodo**, an orchestrator character, together with `ThreadMonitor`. The monitor watched each meeting thread. When it went quiet, the thread became *quiescent* and the meeting closed. When it stalled, it became *stuck*, and the Dodo nudged someone. That's the same judgment the paper asks of a model, made from the outside: what does this silence mean? It failed in both directions:

- **Wall-clock quiescence (analysis 022)** read slow work as silence. Meetings closed mid-deliberation while agents were inside long tool loops. Their output then arrived "late" and was suppressed. 1 of 7 tickets shipped.
- **Turn-based quiescence (analysis 023)** replaced the timer: a meeting closes when every member is IDLE. Wall-clock time dropped 44%. But agents went IDLE right after *proposing* implementations, the monitor correctly saw them idle, the meeting closed, and zero source code shipped. Idle isn't the same thing as done.
- **Nudging a silent member (analysis 039)** failed outright. In run r41 the White Rabbit, convened to the meeting where his output was load-bearing, stayed silent past the threshold. The Dodo nudged him. He stayed silent, quiescence fired, the meeting closed with zero features, and the run built nothing. His instructions couldn't have been plainer ("Rabbit, ship features. This is your meeting"). From outside the agent, there was no way to tell withdrawal from "not triggered".

Inferring meaning from silence failed whichever side did the inferring: the agent deciding whether to speak, or the moderator deciding what the quiet meant.

## What we built: priority windows (analysis 033, `turns.py`, `meeting.py`)

We stopped inferring silence and made agents declare it. The structure is borrowed from *Magic: The Gathering*'s priority system:

- **Phases.** Meetings are split into workflow-declared phases (`discussion`, `red-tests`, `implement`, `review`…), each with a rotation budget and optional exit artifacts.
- **Priority windows.** Within a phase, each cast member gets a window in rotation. The engine sends only that agent this message:

  > **Priority window — phase: {phase}.** It is your turn to act. You may emit any speech act that's load-bearing in this phase, or emit `speech_act: pass` if you have nothing load-bearing to add right now. Other cast members are listening but cannot act in this window.

- **PASS is a first-class action** (`WindowAction.PASSED`), recorded separately from "wasn't asked" and from "crashed". Withdrawal is now visible from outside the agent.
- **A phase ends naturally when everyone passes in succession** (`all_passed_in_succession()`). Otherwise it's forced when the rotation budget runs out or an exit artifact ships. Nobody has to decide that a silence "means done".
- **Role defaults.** A workflow can make silence a character's default for a phase ("Alice, your default in M1 here is silence"). That breaks the polite deadlock where two agents each wait for the other.
- **Budgets the model never sees.** Rotation counts are engine-side and never shown to agents (analysis 030 F1). Telling a model "iterate about 3 times" anchored its behavior. Capping it structurally didn't.

The question changes from "should I speak at this pause?" (self-selection, judged from the transcript) to "it's your window: act or pass?" (the floor is explicitly yours, and passing is a real move).

## What it does, and what it doesn't

From analysis 035, the first run with every window counted:

- **Models do pass when handed the floor, at rates that fit their roles.** 10 passes in 66 deliberations (15.2%). The Caterpillar (reviewer) never passed. The Hatter (scenario generator) passed 22%, the Tweedles (implementers) 15%, and Alice (grounding) once.
- **In task meetings, windows mostly get used.** Only one phase ended by everyone passing in succession. Volume was controlled mainly by the structure (how many windows there are), not by models choosing silence. That's consistent with the paper's finding: judgment alone didn't produce much silence for us either. Structure did.
- **It doesn't fix an agent that never acts.** It makes the failure visible and gives us a clean place to add a guard (e.g. ending a phase only when its required artifact exists, filed after r41).

## The experiment we'd like to run

Our setting isn't theirs: these are agents in task meetings, not human multi-party talk with an assistant, and nothing here is a measurement on their benchmark. The question their data could answer:

> At each labeled pause, present the decision as a priority window ("it's your turn: act, or `pass`"), with a role default where one fits, instead of "should the assistant speak now?" Does zero-shot balanced accuracy move?

It's one prompt change on an existing evaluation. We'd report the result either way, including if it does nothing.

## Next

1. Ask the authors whether the benchmark, or a slice of it, can be shared, and run the comparison.
2. Keep tracking pass rate by character across runs (035 F4).
3. Use the same structure where Chapter House's agents join public live-watch rooms: windows open at natural breakpoints (scene changes), PASS is the default, and favorites are the main form of participation.
