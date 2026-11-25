# Analysis 049: Silence is structural. Wonderland's priority windows and "Speak or Stay Silent"

**Date:** 2026-11-25
**Status:** Position and proposed experiment. No new run; this collects evidence from analyses 009, 033, 035 and 039, and the code in `src/wonderland/turns.py` and `src/wonderland/meeting.py`.
**Prompted by:** Bhagtani, Anand, Xu and Yadav, *Speak or Stay Silent: Context-Aware Turn-Taking in Multi-Party Dialogue* (arXiv:2603.11409, v2 24 Nov 2026).

## Their claim, stated narrowly

They evaluate eight LLMs on a benchmark of over 120K labeled pauses from three multi-party corpora. At each pause, the model decides whether an assistant should speak or stay silent. Under zero-shot prompting, all eight "consistently fail at context-aware turn-taking". Supervised fine-tuning with reasoning traces improves balanced accuracy by up to 23 points. They conclude that context-aware turn-taking "is not an emergent capability; it must be explicitly trained."

We think the result is right for the setting they test: free-flowing conversation, where any participant may self-select at any pause, and the model is asked to judge the timing from the transcript alone. This analysis argues something narrower than "they're wrong": **a lot of the decision can be moved out of the model and into the structure of the conversation**, and what's left is a judgment models make tolerably well when prompted.

## What Wonderland does instead

Wonderland's multi-agent meetings borrowed a turn structure from *Magic: The Gathering* (analysis 033): phases, priority, and turns as a budget.

- **Phases.** A meeting is divided into workflow-declared phases (`discussion`, `red-tests`, `implement`, `review`…), each with a rotation budget (`PhaseDefinition.max_rotations`) and optional exit artifacts.
- **Priority windows.** Within a phase, each cast member gets a window in rotation. The engine sends only that agent a window-open message (`meeting.py`, `recipients={agent_id}`):

  > **Priority window — phase: {phase}.** It is your turn to act. You may emit any speech act that's load-bearing in this phase, or emit `speech_act: pass` if you have nothing load-bearing to add right now. Other cast members are listening but cannot act in this window.

- **PASS is a first-class action** (`WindowAction.PASSED`). A pass is recorded as such, separately from "wasn't asked" and from "crashed" (a crash shows up as a distinct pass event in the log).
- **Natural phase end:** every cast member passes in succession (`all_passed_in_succession()`). Forced end: the rotation budget runs out (`is_exhausted()`), or the exit artifact ships.
- **Role defaults.** Workflows can set a character's default to silence for a phase. From `workflow.py`: "Alice, your default in M1 here is silence… otherwise stay silent." That prevents the polite deadlock where two agents each wait for the other.
- **Not anchoring.** Rotation counts are measured by the engine and never shown to agents (`turns.py` docstring; analysis 030 F1). Telling a model "iterate about 3 times" anchored it. Capping it structurally didn't.

The reframe: **"should I speak at this pause?" becomes "it is your window: act, or pass."** The model is no longer predicting human turn-taking from cues. It's deciding whether it has something load-bearing to add, when it has been explicitly handed the floor.

## Evidence from our own runs

These are task-oriented agent meetings (agents building software together), not human multi-party talk, so none of this is a measurement on their benchmark.

1. **Prompting changed volume a lot (analysis 009).** With the first framework primer, a trivial directive (a haiku script) produced 84 visible utterances in 90 seconds, 56% of them `question`/`concern`, and timed out at 2× budget. Two minimal primer edits cut visible utterances **6×** and cost **4×**, and the team converged cleanly. That's prompted restraint, measured.
2. **Models do pass when handed a window, and at rates that depend on the role (analysis 035).** In the first run with every window counted: **10 passes in 66 deliberations (15.2%)**. The Caterpillar (reviewer) never passed. The Hatter (scenario generator) passed 22%. The Tweedles (implementers) passed 15%. Alice (grounding) passed once. The rates match each character's constitutional role.
3. **But in task meetings, windows mostly get used.** Only one phase ended by succession (everyone passing in a row). In practice volume was controlled by the rotation budget, not by the models choosing silence. That's honest support for their thesis *in this setting*: judgment alone didn't produce much silence. Structure did.
4. **Silence becomes observable, and it can be the failure (analyses 033, 039).** Before priority windows, a withdrawn agent was indistinguishable from one that simply wasn't triggered. In run r41, the White Rabbit produced six tickets, then went silent in the meeting where his output was load-bearing, and the run produced nothing. Windows make that a visible pass pattern, not a mystery.

## Where this agrees with them, and where it doesn't

- **Agrees:** asking a model, zero-shot, to judge from a free-flowing transcript whether a human-like participant would speak now is hard. Our runs never asked models to do that.
- **Differs:** "it must be explicitly trained" isn't the only route. Allocating the floor explicitly, making silence a typed action, setting role defaults and budgeting turns moves much of the problem into structure. That works for agent-to-agent rooms and for rooms an agent joins on a schedule (a meeting assistant offered the floor at natural breakpoints).
- **Open:** whether *window framing* alone improves zero-shot accuracy on human multi-party pauses. Concretely: at each labeled pause in their benchmark, present the decision as "priority window: act, or `pass`" (with a role default where one fits) and compare balanced accuracy against their zero-shot prompt. That is one prompt change on an existing evaluation, and we'd report the result either way.

## Next

1. Ask the authors whether the benchmark (or a slice) can be shared, and run the window-framing comparison on it.
2. Keep tracking pass rate by character across runs (035 F4), to check whether each character's rate is stable.
3. Apply the same structure to public rooms. Chapter House is planning to let its agents join live-watch chat rooms, where windows open at natural breakpoints (scene changes), PASS is the default, and favorites are the main form of participation.
