## Story 020: Kohl recalls a past note faster via search than her old scattered-files workflow

**GUID:** 01KRXX0XAA8ZSB79NXHYA2KW46

**Persona:** Kohl, 30, AI Researcher. She runs weekly ML experiments and takes detailed notes on results. Last week she wrote observations about attention-head variance. This week, her collaborator asked about the specifics — how did variance scale with model depth?

**Situation:**

Kohl is at her desk with Slack messages asking for specifics. She could search her scattered markdown files on disk (open file browser, grep across directories, skim multiple files). Or she could open the notebook app. The test of v1's success is whether the notebook is faster.

**Need:**

As Kohl, I want to find a past experimental note by search or tag, so that I can answer my collaborator's question faster than hunting through scattered files on disk.

**Acceptance:**
- Kohl opens the app and is in the search view within one click (from editor or inbox)
- Kohl types 'attention variance' and sees results within 300ms (no perceptible lag even with 100+ notes)
- Search results are accurate and relevant (the right note is in the top 3 results)
- Kohl can see the note's body preview without opening the full note editor
- After finding the note, Kohl can click to open it in the editor and skim the details
- Kohl perceives that this is faster and less frustrating than her old workflow (implies: finding a note in the notebook takes less than 30 seconds vs. 2-5 minutes with scattered files)

**Tier:** core

**Confusion-flags:**
- The acceptance criteria name a perception ('faster than old workflow') which is not directly testable via automated tests — this is a UX validation that probably requires Kohl's actual feedback or a timed user study. M2 testing should check the technical baselines (search latency, result accuracy), but the *success signal* requires human validation.
- If search latency is poor (e.g., >500ms with 100+ notes), the speed comparison will fail. The backend and frontend need to handle this scale without degradation. This may require caching, indexing, or pagination tuning — all plumbing that the foundation stories enable, but this story names the success condition.
- The 30-second threshold is arbitrary — I pulled it from the requirement's 'faster than scattered files' language. M2 contract negotiation should ground this in actual numbers from Kohl's old workflow (ask the operator: what was her old time?) so we can validate properly.

**Realizes requirements:**
- success-signal-faster-retrieval-than-scattered-files
- search-performance-target-500-notes-substring-match
- substring-search-across-note-titles-bodies-and-tags
