# Analyses

This directory holds **field notes on the Wonderland thesis** as the system
gets built out — phase by phase, observation by observation.

## What lives here

Each entry is a numbered markdown file (`NNN-short-slug.md`) tied to a
specific moment in the build. Typical contents:

- **Demo transcripts** captured from `scripts/` runs against real LLMs
- **Observations** about what the run shows
- **Thesis-tracking** — does the Temple-Codex thesis (identity-native >
  generic) appear to hold so far? In what specific way?
- **Caveats** — n, sample size, what hasn't been measured yet
- **Predictions** — what we'd expect future runs to look like if the
  thesis is correct

These aren't formal evaluations. The eval harness lands in P7 with the
generic-vs-Wonderland comparison — that's where we get the compounding
curve. Until then, these are the qualitative observations that build
intuition for what the harness should measure.

## Numbering

Entries are numbered chronologically by phase milestone, not by date.
`001-first-voice.md` is the P2 closeout observation; `002-...` will land
when there's a new substantive thing to observe.

## Source artifacts

Demo scripts live in `../scripts/`. Each entry should name the script
that produced its transcript, the directive used, and the model/version
in the run header so the run is reproducible.
