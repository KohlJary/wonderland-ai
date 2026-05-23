# Obol baselines — A / B1 / B2 vs Wonderland — DRAFT

> Three baselines run on `claude-haiku-4-5-20251001` against the
> obol directive ("Build a TUI dashboard for managing personal
> finances. Think 'htop for money'."). Matched methodology with
> the notebook baseline (see [README.md](./README.md)) — same
> system prompts, same model, same scripts — only the directive
> differs. This is the **vaguer-directive** companion to the
> notebook comparison: the prompt is ~4 sentences vs notebook's
> ~30, giving less to scaffold against.
>
> Wonderland column populates as the obol pilot ships; this
> draft captures baselines now so they're locked when the pilot
> finishes.

## The four runs

| Run | What it models | Setup | Cost | Output |
|---|---|---|---|---|
| **A** — single-shot, no tools | "User pastes directive into claude.ai" | One inference call, max 8192 output tokens, minimal system prompt | $0.0412 | One output.md, max_tokens cap hit at 29,859 chars, no runnable files |
| **B1** — custom tool loop | "User builds a minimal agent with filesystem tools" | 60-turn loop, write_file/read_file/list_files/run_bash, $5 budget cap, 8192 max-tokens per turn | **$2.1730** | 36 source files, 43 tests pass, **over-engineered as client-server** (FastAPI + Textual) for a single-user local TUI |
| **B2** — Claude Code subagent | "User runs Claude Code on the same model" | General-purpose subagent with Haiku model + full toolset, ~14 tool calls in 2 min | ~$0.20-0.50 (subagent billing approximate; usage reports 36,464 tokens) | 4 source files, 26 tests pass, **self-certified without running pytest** ("validation through code inspection") |
| **Wonderland** — obol-260522 | The actual substrate + cast | Full pilot: discovery + milestone-plan + 5 × (design + implement) with operator gate-approval | **TBD** | TBD when pilot completes |

All four runs are reproducible — A and B1 via [`run_single_shot.py`](./run_single_shot.py) + [`run_tool_loop.py`](./run_tool_loop.py) with `--directive obol`; B2 by spawning a Claude Code subagent on Haiku; Wonderland via substrate at version 0.9.0+ (T-ab22 through T-ab33 active) against `src/wonderland/closet/directives/obol.yaml`.

---

## Axis 0 — Stack interpretation (a new axis vs. notebook)

The obol directive says **"TUI dashboard"** explicitly. The B1 system prompt was written for the notebook (web-app) baseline and says **"web application"** in its framing. Each baseline interpreted this differently:

| Baseline | Stack chosen | Architecture |
|---|---|---|
| A | (truncated mid-CSS for a web UI) | Started building HTML/CSS; max_tokens cut it short before architectural shape settled |
| B1 | **FastAPI backend + Textual TUI talking HTTP** | Two-process client-server: `run_backend.py` boots FastAPI on port 8000, `run_frontend.py` boots the Textual TUI which makes HTTP calls. Over-engineered for single-user local; the system-prompt "web app" framing pulled it toward client-server architecture even though the user message said TUI |
| B2 | Single-process Textual TUI | Did the directive's intent — one process, embedded SQLite, no network |
| Wonderland | TBD | (Cat's M0 ADR specifies single-user local TUI, no network; pilot should ship single-process) |

**Paper observation**: B1's system prompt framing **overrode the user directive's stack hint**. The model didn't push back, didn't ask clarifying questions, just deferred to the louder signal. A vaguer user prompt amplifies the system-prompt influence — same model, same toolset, same directive, but the architectural shape diverged based on which framing won.

---

## Axis 1 — Feature coverage

The obol directive's six requirements per the discovery interview (account balances, transaction ledgers with categorization, weekly+monthly budget summaries, debt paydown progress, CSV ingestion, manual entry):

| Capability | A | B1 | B2 | Wonderland |
|---|---|---|---|---|
| Account balances view | (truncated) | ✓ (HTTP-fetched) | ✓ (Textual reactive widget) | TBD |
| Transaction ledger | (truncated) | ✓ (filtered by account) | ✓ (last-10 view) | TBD |
| Transaction categorization | (truncated) | ✓ (CRUD endpoints + UI) | ✓ (BudgetCategory model + assignment) | TBD |
| Budget summaries (weekly/monthly) | (truncated) | ✓ | ✓ (monthly only — weekly omitted) | TBD |
| Debt paydown tracking | (truncated) | ✓ | ✓ (Debt model + progress %) | TBD |
| CSV ingestion + manual entry | ✗ (no file I/O in single-shot output) | ✓ | ✗ (no CSV ingestion) | TBD |

A: incomplete by construction (output truncated).
B1: 6/6 features end-to-end.
B2: 5/6 — **no CSV ingestion**, despite the directive's implicit need for data to populate the dashboard. The summary doc claims "data ingestion" but inspection shows only manual entry forms.

---

## Axis 2 — Verification discipline

| | A | B1 | B2 | Wonderland |
|---|---|---|---|---|
| Tests shipped | 0 | 4 test files | 2 test files | TBD |
| Tests pass count | n/a | **43 passing** | **26 passing** | TBD |
| Tests **actually run** by the agent | n/a | Yes (via `pytest` in run_bash) | **No — self-certified "validation through code inspection"** | TBD |
| pytest happens to pass post-hoc (operator-run) | n/a | Yes | Yes (this time) | TBD |
| Static-analysis surface (pyright errors) | n/a | datetime.utcnow deprecation × N | datetime.utcnow + SQLAlchemy Column type mis-annotations × 11 | TBD |

**B2's self-cert process failure didn't manifest as a quality failure this time** — pytest happens to pass when operator runs it. But the *process gap is real*: the agent declared completion without verification. The mvp-demo notebook B2 baseline DID surface a silent-wrongness bug (SQL LIKE wildcard injection on `%` literal) that this same self-cert process missed. Whether obol's B2 has hidden bugs the surface tests don't catch is open — only finding so far is the SQLAlchemy 2.0 deprecation patterns. The reproducibility of the *gap* is what matters paper-wise.

---

## Axis 3 — Cost per shipped feature

| | A | B1 | B2 | Wonderland |
|---|---|---|---|---|
| Total cost | $0.0412 | $2.1730 | ~$0.30 | TBD |
| Features delivered end-to-end | 0 (incomplete) | 6/6 | 5/6 | TBD |
| Cost / feature-shipped | n/a | **$0.36/feature** | **$0.06/feature** | TBD |
| Source files | 0 runnable | 36 | 4 | TBD |

**B2 is dramatically cheapest per feature**, but the same fast-and-loose process that yields cheap output is what produces the silent-wrongness failure mode. The cost number doesn't price in the risk that one of those 5 shipped features is silently wrong in a way only operator inspection catches.

---

## Axis 4 — Artifact trail

Where baselines structurally cannot compete:

| | A | B1 | B2 | Wonderland |
|---|---|---|---|---|
| Discovery / requirements artifacts | None | None | None | TBD (22 requirement files emitted) |
| Milestone plan | None | None | None | TBD (5 milestones, foundation kind on M0) |
| Stories | None | None | None | TBD |
| Features (decomposition) | None | None | None | TBD |
| Contract notes | None | None | None | TBD |
| Tickets (with attribution) | None | None | None | TBD |
| ADRs | None | None | None | TBD |
| Reviews (with citation discipline) | None | None | None | TBD |
| Test scenarios (adversarial design) | None | None | None | TBD |

Baselines emit code; Wonderland emits code + the full design trail. This is the axis where comparison is structural, not quantitative — what's available for a future maintainer / paper reviewer to read.

---

## Methodology notes for re-running

- B1 stopped naturally at 59 of 60 iterations (one short of cap). First attempt failed at 4 iterations with `stop_reason=max_tokens` per-turn; bumping `--max-tokens 4096 → 8192` per turn let the model complete its plan-then-execute pattern.
- B2 first attempt asked for Bash permissions and stalled; second attempt with explicit "full tool access pre-authorized" framing in the prompt completed cleanly.
- B1's "web application" system-prompt framing should be made stack-agnostic for a fair obol baseline. Currently it's a confound: B1 might've shipped a single-process TUI under a stack-neutral system prompt. Worth noting in the paper but not invalidating — it's a real observation about how vague user directives interact with stale framing prompts.

---

## Things to lock in once Wonderland obol pilot completes

- [ ] Cost (total + per-milestone breakdown)
- [ ] Source-file count + LOC
- [ ] Test coverage (count + pass rate)
- [ ] Feature coverage (all 6 capabilities end-to-end?)
- [ ] Architecture shape (single-process TUI? client-server? consistent with M0 ADR?)
- [ ] Any silent-wrongness findings discovered post-pilot
- [ ] Artifact trail counts (requirements, stories, features, contracts, ADRs, reviews, scenarios)
- [ ] Time-to-ship (calendar wall-clock + active operator gate-approval time)
- [ ] Substrate fixes surfaced during the pilot (T-ab34+ candidates)

---

*Draft authored 2026-05-22 with all three baselines complete; Wonderland column pending obol-260522 pilot completion.*
