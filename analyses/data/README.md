# Analysis evidence

Each subdirectory holds the raw transcript, telemetry, and shipped
artifacts referenced from the corresponding `analyses/NNN-*.md` file.
The narrative analysis quotes the highlights; the data here is the
unedited record so anyone can verify the claims.

## Layout

Each per-analysis directory contains some subset of:

- `run.log` — the full transcript captured from the live run
- `run-YYYYMMDDTHHMMSS.json` — the telemetry record (per-agent token
  usage + cost, written by `Telemetry.write_run_record`)
- `architecture/`, `contract-notes/`, `implementations/`, `src/`, etc. —
  the artifacts the team produced during the run, copied verbatim from
  the run's `.wonderland/` directory and (for `src/`) the project root

## What's here

- `011-translation-chat-scoping/` — open-bus T36 baseline, $5.58 with no
  fixes. Telemetry shows the per-agent cost spread that motivated the
  roster architecture.
- `012-roster-scoping-rerun/` — same directive, scoped roster (Alice +
  Cat + Queen + Dodo). $0.058. No code yet — calibration needed first.
- `013-cat-calibrated-ships/` — first ADR shipped (`adr-001-third-party-
  translation-service-with-synchronous-on-read-model.md`).
- `014-cross-meeting-composition/` — Tweedles negotiate 5 contract notes
  from ADR-001 via the manual Block 2b simulation. All 5 reach agreed.
- `015-tweedles-ship-real-code/` — Tweedles ship `src/translation_handler.py`
  (6346 bytes of working Python honoring the contracts) using the tool
  surface. End-to-end "vague directive → working code" loop closed.

## Reproducing

The scripts that produced these runs are in
[`../../scripts/`](../../scripts/):

- `translation_chat_showcase.py` — analyses 011, 012, 013
- `contract_followon_demo.py` — analysis 014
- `translation_handler_demo.py` — analysis 015

All scripts cap cost via `--budget` (or hardcoded constant) and
require an Anthropic API key (see top-level README "Configuration").
LLM nondeterminism means re-runs will differ in detail but the
structural findings (cost shape, artifact production, failure modes)
have been stable across re-runs of the same scenario.
