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
- `demo/` — pilot 2's shipped working application (copy of mvp-demo2's
  app code, frontend, tests). Cleanest path for paper readers to clone +
  run + verify the artifact. Excluded from the PyPi build.
- `projects/mvp-demo/` — pilot 1 full state, partial completion,
  substrate-immature data
- `projects/mvp-demo2/` — pilot 2 full state, including the substrate
  artifacts (.wonderland/, runs/, telemetry/, memory/) used as paper
  source material. The `demo/` copy is for reproducibility; this is
  for analysis.
- Pilot run telemetry: `projects/mvp-demo2/.wonderland/telemetry/`

**Substrate mechanics walkthrough**:
- `artifacts/workflow-walkthrough.md` — per-meeting breakdown of every
  major workflow (discovery, milestone-plan, tdd-design, tdd-implement):
  roster, why each agent is on the roster, intent, phase semantics,
  exit conditions, lifecycle transitions, substrate primitives. Source
  material for the architecture chapter — covers the "how it actually
  runs" half of the paper.
- `artifacts/cast-walkthrough.md` — per-character breakdown of every
  identity in the cast: role, characteristic move, what they ship,
  declared failure mode (§VIII), persistence shape (§IX), and where
  they appear across the four workflows. Source material for the cast
  chapter — failure-modes-as-identity, the small-cast principle, guest
  casts (Holmes / Watson), pair protocols.
- `artifacts/code-quality-mvp-demo2.md` — quantitative metrics + pattern
  receipts + independent cold-reviewer findings on the demo/ shipped
  artifact. The credibility-making evidence for the quality argument.
- `artifacts/evidence-chapter-source.md` — five-pillar synthesis of
  paper-grade observations: quality-cost coupling, multi-lens
  identity-anchored review, schema-as-safety, convergent self-repair
  (with documented memory limit), constraints-improve-quality. Each
  pillar with claim + mechanism + concrete pilot evidence + honest
  scope. Explicitly excludes untested hypotheses.
- `artifacts/thesis-chapter-source.md` — extends THESIS.md's canonical
  5-corollary argument with mvp-demo2 evidence + a sixth corollary
  (substrate constraint amplifies identity). Preserves the Sephirah/
  Qlipha framing and the literary-lineage discipline. Pairs with the
  evidence chapter as load path (architectural claim → corollaries →
  pillars → artifacts).
- `artifacts/methodology-chapter-source.md` — pilot-driven substrate
  development with categorization-through-failure as the discipline.
  The pilot → memory observation → substrate primitive → next pilot
  loop, walked out. Autonomy tiers (Tier 1 observer / Tier 2
  gate-approver / Tier 3 designer) as the maturity metric. Mid-pilot
  substrate fixes as Tier 2 violations with intent. Operator-noticed
  findings as research-grade signal alongside instrumented telemetry.
- `artifacts/limitations-chapter-source.md` — four classes of
  limitation (substrate gap / scope-bounded validation / sample-size
  limit / missing rigor) with the honest counterweight to thesis +
  evidence chapter claims. The b3f440c8-cluster theme
  (prior-milestone-awareness at every layer). N=2, one directive
  class, one model class. P7 generic-baseline eval still future work.
  Untested hypotheses explicitly excluded from claims.
- `artifacts/future-work-chapter-source.md` — forward-facing
  counterweight to limitations: near-term substrate evolution
  (cluster fixes, persona-anchoring, frontend test enforcement),
  comparative experiments that close rigor loops (single-shot
  Haiku/Sonnet baselines, P7 eval, design-all-first vs interleaved,
  cross-model comparative pilots), cross-shape transferability
  (different directive classes, model classes, atomic workflow
  chaining), new cast capabilities (Holmes/Watson workflows, pair
  protocols as primitive), architectural research questions (Tier
  3 autonomy, self-hosting, long-running collaboration substrate),
  identity engineering as research discipline beyond Wonderland.

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
