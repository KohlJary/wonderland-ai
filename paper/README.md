# Paper notes

Working directory for the Wonderland paper. Source material lives in `artifacts/`, working notes in this directory's top level, drafts under a future `drafts/` once writing begins.

## Structure

```
paper/
├── README.md          # this file
├── artifacts/         # source data: cost breakdowns, pilot logs, code samples
└── (future: drafts/, figures/, references/)
```

## Source material elsewhere in the repo

The paper draws on several existing locations beyond `paper/`:

**Thesis observations** (`.claude/projects/-home-jaryk-wonderland-ai/memory/project_*.md`):
- `project_quality_cost_inversion.md` — quality and cost move together, not against
- `project_caterpillar_state_independence.md` — convergent self-repair (with memory limits)
- `project_caterpillar_no_hallucination.md` — schema-as-safety prevents hallucination
- `project_constraints_improve_quality.md` — counter to "give LLMs flexibility" advice
- `project_multi_lens_review_produces_quality_code.md` — identity-anchored multi-lens architecture
- `project_first_tier2_pilot_completion.md` — mvp-demo2 Wright Brothers moment
- `project_substrate_fixes_dont_propagate_through_memory.md` — memory bleed + branching as architectural fix
- `project_mvp_demo_m1_m2_overlap.md` — overshoot pattern across milestones
- `project_haiku_is_architecturally_optimal.md` — HYPOTHESIS only, not paper-evidence-grade
- `project_interviews_milestones_thesis.md` — structural foundation
- `project_failure_modes_thesis.md` — identity engineering origin
- `project_haiku_thesis.md` — small-model thesis statement
- `project_holmes_cast.md` — guest-cast extensibility

**Substrate evolution history**:
- `release-notes/0.7.0.md`, `0.8.0.md` — what shipped when, with rationales
- `src/wonderland/closet/analyses/` — numbered analysis docs from each iteration
- `.daedalus/design-memory-branching.md` — T-a2 design proposal for memory branching

**Pilot artifacts**:
- `projects/mvp-demo/` — pilot 1, partial completion, substrate-immature data
- `projects/mvp-demo2/` — pilot 2, full completion, paper's headline pilot
- Pilot run telemetry: `projects/mvp-demo2/.wonderland/telemetry/`

## Paper outline (provisional)

Not committed; subject to change.

1. **Thesis** — identity engineering as a discipline; failure-modes-as-identity; small-model thesis
2. **Architecture** — the substrate primitives (registries, bus, episodic memory, branching, snapshot semantics)
3. **Cast** — characters with characteristic failure modes; multi-lens review
4. **Methodology** — pilot-driven substrate development; categorization through failure
5. **Evidence**
   - Quality-cost coupling (cited from memory observations)
   - Convergent self-repair (with documented memory limit)
   - Schema-as-safety (no hallucinated findings on Haiku)
   - Constraints-improve-quality principle
6. **Economics** — mvp-demo2 cost breakdown (`artifacts/cost-breakdown-mvp-demo2.md`)
7. **Wright Brothers moment** — mvp-demo2 end-to-end pilot results
8. **Limitations** — substrate gaps still open (b3f440c8 cluster, sequencing experiments)
9. **Future work** — p19 existing-projects onramp; design-all-first vs interleaved comparison; per-feature impl branches
