# Wonderland paper — assembly index

> The paper composed into chapter order with cross-references. Each
> chapter's source lives in `paper/artifacts/`; this index defines
> the sequence and the editorial scaffolding to strip when
> physically composing into a single document.
>
> To produce a single-file composition:
>
> ```bash
> # quick stitch (strips no scaffolding):
> cat paper/artifacts/intro-and-abstract-source.md \
>     paper/artifacts/thesis-chapter-source.md \
>     paper/artifacts/architecture-chapter-source.md \
>     paper/artifacts/cast-chapter-source.md \
>     paper/artifacts/methodology-chapter-source.md \
>     paper/artifacts/substrate-evolution-chapter-source.md \
>     paper/artifacts/evidence-chapter-source.md \
>     paper/artifacts/limitations-chapter-source.md \
>     paper/artifacts/future-work-chapter-source.md \
>     paper/artifacts/related-work-chapter-source.md \
>     paper/artifacts/bibliography.md \
>   > paper/drafts/wonderland-raw.md
> ```
>
> A polished single-file composition would additionally:
> - Strip each chapter's "> Source material for..." preamble
> - Strip each chapter's "## See also" section (replaced by inline
>   §X.Y references)
> - Strip each chapter's "## Notes for the paper writer" section
>   (those are meta-guidance, not paper content)
> - Demote `##` headers to `###` within chapters so chapter titles
>   sit at `##` and sections within sit at `###`
> - Renumber sections (each chapter source uses its own ## numbering;
>   composed version uses §1.1, §1.2, §2.1, etc.)

---

## Composed sequence

| § | Chapter | Source file | Lines | Status |
|---|---------|-------------|-------|--------|
| Frontispiece | Title + abstract | `intro-and-abstract-source.md` (Abstract section) | ~30 | Ready |
| §1 | Introduction | `intro-and-abstract-source.md` (§1-§4 + closing) | ~620 | Ready (dedup'd + worldview-as-integral added) |
| §2 | Thesis | `thesis-chapter-source.md` | ~810 | Refreshed (state-machine framing + cost trajectory + identity-engineering softened) |
| §3 | Architecture | `architecture-chapter-source.md` | 442 | New (compressed; 3 representative meetings); full walkthrough → Appendix A |
| §4 | Cast | `cast-chapter-source.md` | 593 | New (compressed; constitution structure + 4 in-workflow characters + §4.7 Daedalus substrate-builder); full registry → Appendix B |
| §5 | Methodology | `methodology-chapter-source.md` | 934 | Refreshed (falsifier table now carries pre-registered next-pilot prediction column; standalone predictions section merged in) |
| §6 | Substrate evolution | `substrate-evolution-chapter-source.md` | 1026 | New (four-phase iteration-cycle chronicle) |
| §7 | Evidence | `evidence-chapter-source.md` | 859 | Refreshed (post-mvp receipts + Theseus findings + Pillar 4 patched-twice engagement) |
| §8 | Limitations | `limitations-chapter-source.md` | 667 | Refreshed + tightened (publishing-snapshot defense reduced to one; cluster section collapsed to §6 pointer; missing-rigor section points to §11 future-work for experiment plans) |
| §9 | Future work | `future-work-chapter-source.md` | 768 | Refreshed (parallel coordination + template consolidation + LDR rerun + existing-codebase surface + Appendix C why-not-execute engagement) |
| §10 | Related work | `related-work-chapter-source.md` | 747 | New (now includes CAMEL/AutoAgents/AgentVerse paragraph) |
| Bibliography | References | `bibliography.md` | 288 | 25 verified citations (added CAMEL, AutoAgents, AgentVerse) |
| Appendix A | Architecture full walkthrough | `appendix-A-architecture-full.md` | 1451 | Full per-meeting walkthrough (was §3 in pre-compression draft; now the deep-reference companion to §3's body summary) |
| Appendix B | Cast full registry | `appendix-B-cast-full.md` | 778 | Full per-character walkthrough (was §4 in pre-compression draft; now the deep-reference companion to §4's body summary) |
| Appendix C | Caterpillar comparator experiment (pre-registered) | `appendix-C-caterpillar-comparator-experiment.md` | 385 | New (pre-registered narrow comparator design for identity-engineering claim; **not executed for this paper** — design is ready for follow-up paper or other researcher) |
| Appendix D | Adversarial review of single-shot baselines | `appendix-D-adversarial-review-of-baselines.md` | 323 | Stable; load-bearing receipt for §1's "single-shot doesn't produce working code" claim |
| Appendix E | Economics | `cost-breakdown-mvp.md` + `design-cost-three-pilot-comparison.md` | ~530 | Stable |
| Appendix F | Code quality | `code-quality-mvp.md` | 1075 | Stable (artifact-level analysis referenced from §7) |
| Appendix G | Comparison baselines | `comparison-baselines/README.md` + `adversarial-review-of-baselines.md` | substantial | Stable; cited from §2 + §10 |

**Composed paper estimated size:** 8500–10500 lines (depending on
scaffolding strip + appendix inclusion choices).

**arXiv-shaped subset estimate:** 6500–8000 lines if appendices are
shipped as supplementary material rather than inline.

---

## Cross-reference normalization

Each chapter source uses internal `[chapter-source-name](./file.md)`
links to refer to peer chapters. When composing into a single
document, these become §X.Y references:

| Source link | Composed reference |
|---|---|
| `[thesis-chapter-source.md]` | §2 |
| `[architecture-chapter-source.md]` | §3 |
| `[cast-chapter-source.md]` | §4 |
| `[methodology-chapter-source.md]` | §5 |
| `[substrate-evolution-chapter-source.md]` | §6 |
| `[evidence-chapter-source.md]` | §7 |
| `[limitations-chapter-source.md]` | §8 |
| `[future-work-chapter-source.md]` | §9 |
| `[related-work-chapter-source.md]` | §10 |
| `[appendix-A-architecture-full.md]` | Appendix A |
| `[appendix-B-cast-full.md]` | Appendix B |
| `[appendix-C-caterpillar-comparator-experiment.md]` | Appendix C |
| `[mvp-pilot-narrative.md]` | Appendix D |
| `[cost-breakdown-mvp.md]` | Appendix E.1 |
| `[design-cost-three-pilot-comparison.md]` | Appendix E.2 |
| `[code-quality-mvp.md]` | Appendix F |
| `[comparison-baselines/...]` | Appendix G |

In sub-section references where the source uses
`#some-anchor` fragments, those become `§X.Y.Z` references in
the composed paper. The substrate-evolution chapter's
"the pattern across all four phases" becomes §6.6, etc.

---

## Editorial scaffolding to strip

Per chapter source, the following sections are intended for the
paper writer (Daedalus / Kohl) but not for the published paper:

| Section pattern | Treatment |
|---|---|
| `> Source material for the paper's X chapter.` (chapter preamble) | Strip entirely |
| `## See also` (end of each chapter) | Strip (replaced by inline §X.Y refs throughout) |
| `## Notes for the paper writer` | Strip entirely |
| `## What counts as X here` (where it's editorial scoping) | Keep if substantive; trim if just procedural |
| Memory-pin links (`../../.claude/projects/...`) | Replace with citation footnotes referencing the memory pin's title |
| Internal task IDs (`T-ab51`, `T-ab64`, etc.) | Keep — these are the substrate's vocabulary and the iteration-cycle's identifiers; readers tracking the project recognize them |
| Roadmap item IDs (`b3f440c8`, `4a2597a4`, etc.) | Keep with one-line definition first time each appears |

---

## What's net new in this draft tree

Per the punch list addressed during this paper-assembly session:

- `intro-and-abstract-source.md` (654 lines, in `paper/artifacts/`)
- `substrate-evolution-chapter-source.md` (1109 lines, in `paper/artifacts/`)
- `paper/artifacts/INDEX.md` (this file)
- `paper/artifacts/related-work-chapter-source.md` (positioning against adjacent fields)
- `paper/artifacts/bibliography.md` (skeleton with verification notes)

Plus refreshes to existing chapters:
- thesis (+153 lines: state-machine framing + cost trajectory)
- methodology (+344 / -38: operator-in-loop falsification load-bearing)
- evidence (+197 / -37: post-mvp receipts + Theseus findings)
- limitations (+420 / -65: publishing-snapshot frame + iteration-cycle track record)
- future work (+323 / -71: post-redux substrate horizon)
- Plus the mvp-demo2 → mvp rename across 15 files

All on branch `paper/thesis-refresh-state-machine-framing`.

---

## Reading order for review

Recommend reading in composed order:

1. **Frontispiece + abstract** — `intro-and-abstract-source.md` top section
2. **§1 Introduction** — `intro-and-abstract-source.md` §1–§4 + closing
3. **§2 Thesis** — `thesis-chapter-source.md`
4. **§3 Architecture** — `workflow-walkthrough.md`
5. **§4 Cast** — `cast-walkthrough.md`
6. **§5 Methodology** — `methodology-chapter-source.md`
7. **§6 Substrate evolution** — `substrate-evolution-chapter-source.md`
8. **§7 Evidence** — `evidence-chapter-source.md`
9. **§8 Limitations** — `limitations-chapter-source.md`
10. **§9 Future work** — `future-work-chapter-source.md`
11. **§10 Related work** — `paper/artifacts/related-work-chapter-source.md`
12. **Bibliography** — `paper/artifacts/bibliography.md`

If you want a single-file flow without reading them in sequence,
run the cat command at the top of this file to produce
`wonderland-raw.md`. The result is ~9K lines of unified prose
with scaffolding intact (still readable; the scaffolding adds
maybe 200 lines of preambles + see-also sections).

A polished arXiv submission would do the additional cleanup
described in "Editorial scaffolding to strip" above plus
section renumbering.
