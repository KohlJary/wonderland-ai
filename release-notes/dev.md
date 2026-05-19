# Dev — unreleased

Active changes accumulating toward the next cut. On release, copy this file to `release-notes/<version>.md` and wipe back to header-only.

### `demo/` reorganized into `demo/<pilot>/` for multi-pilot artifacts

Mvp-demo2's shipped artifact moved from `demo/` to `demo/mvp/`. The `demo/` parent is now reserved for additional pilot reference applications (e.g. `demo/crm/` if/when the CRM pilot ships, future obol artifact at `demo/obol/`, etc.). Pyproject's sdist exclusion still prefix-matches everything under `demo/`, so the PyPi build remains unaffected.

Path references updated across:
- `paper/README.md` — repo layout section reflects the new convention
- `paper/artifacts/code-quality-mvp-demo2.md` — all 8 file:line citations
- `paper/artifacts/comparison-baselines/README.md` — wonderland-trail links + cold-reviewer references; also fixed one stale relative-path link that had been one `../` short
- `paper/artifacts/limitations-chapter-source.md`, `mvp-demo2-pilot-narrative.md`, `future-work-chapter-source.md`
- `src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md`
- `release-notes/0.8.1.md` — historical doc, but dead links updated so readers don't 404
- `demo/mvp/README.md` — self-references (header, run instructions, all 7 relative links retargeted from `../<path>` to `../../<path>`)

Git tracked all 700+ moves as renames (R) cleanly, so blame/log on the artifact files still threads through to the pre-rename commits.
