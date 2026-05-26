# Bibliography

> References cited throughout the paper. Each entry verified via
> web search during composition. URL stability varies — arXiv IDs
> and DOIs are stable; GitHub repos and corporate blog posts may
> shift. Bracketed citation keys (`[AutoGen]`) are used inline
> throughout the paper text.

## Multi-agent frameworks

**[AutoGen]** Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B.,
Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah,
A. H., White, R. W., Burger, D., & Wang, C. (2023). *AutoGen:
Enabling Next-Gen LLM Applications via Multi-Agent
Conversation*. arXiv:2308.08155. [arxiv.org/abs/2308.08155](https://arxiv.org/abs/2308.08155).
Microsoft Research. The original multi-agent conversation
framework paper.

**[MetaGPT]** Hong, S., Zhuge, M., Chen, J., Zheng, X., Cheng,
Y., Zhang, C., Wang, J., Wang, Z., Yau, S. K. S., Lin, Z., Zhou,
L., Ran, C., Xiao, L., Wu, C., & Schmidhuber, J. (2023).
*MetaGPT: Meta Programming for A Multi-Agent Collaborative
Framework*. arXiv:2308.00352. [arxiv.org/abs/2308.00352](https://arxiv.org/abs/2308.00352).
DeepWisdom. Standard Operating Procedures encoded into
prompts; assembly-line role assignment.

**[ChatDev]** Qian, C., Liu, W., Liu, H., Chen, N., Dang, Y.,
Li, J., Yang, C., Chen, W., Su, Y., Cong, X., Xu, J., Li, D.,
Liu, Z., & Sun, M. (2024). *ChatDev: Communicative Agents for
Software Development*. ACL 2024. arXiv:2307.07924. [arxiv.org/abs/2307.07924](https://arxiv.org/abs/2307.07924).
Tsinghua / OpenBMB. Chat-chain coordination; communicative
dehallucination; sub-$1 software generation in under seven
minutes.

**[CAMEL]** Li, G., Hammoud, H., Itani, H., Khizbullin, D., &
Ghanem, B. (2023). *CAMEL: Communicative Agents for "Mind"
Exploration of Large Language Model Society*. NeurIPS 2023.
arXiv:2303.17760. [arxiv.org/abs/2303.17760](https://arxiv.org/abs/2303.17760).
KAUST. Role-playing communicative agent framework; user/assistant
pair coordination; demonstrates role-conditioning effects on
solution paths.

**[AutoAgents]** Chen, G., Dong, S., Shu, Y., Zhang, G., Sesay,
J., Karlsson, B., Fu, J., & Shi, Y. (2023). *AutoAgents: A
Framework for Automatic Agent Generation*. arXiv:2309.17288.
[arxiv.org/abs/2309.17288](https://arxiv.org/abs/2309.17288).
Microsoft Research. Dynamic agent-generation framework;
synthesizes specialized agents per task at runtime; reduces
manual prompt-engineering load on the operator.

**[AgentVerse]** Chen, W., Su, Y., Zuo, J., Yang, C., Yuan, C.,
Chan, C.-M., Yu, H., Lu, Y., Hung, Y.-H., Qian, C., Qin, Y.,
Cong, X., Xie, R., Liu, Z., Sun, M., & Zhou, J. (2024).
*AgentVerse: Facilitating Multi-Agent Collaboration and Exploring
Emergent Behaviors*. ICLR 2024. arXiv:2308.10848.
[arxiv.org/abs/2308.10848](https://arxiv.org/abs/2308.10848).
Tsinghua. Multi-agent collaboration framework with expert
recruitment, decision-making, and action phases; demonstrates
multi-phase coordination outperforming flat collaboration.

**[LangChain]** Chase, H., et al. (2022–). *LangChain: The agent
engineering platform.* Open-source framework, GitHub: [github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain).
Launched October 2022.

**[LangGraph]** LangChain Inc. (2024–). *LangGraph: A framework
for stateful, multi-agent AI workflows.* GitHub: [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph).
Documentation: [langchain.com/langgraph](https://www.langchain.com/langgraph).
Graph-based stateful agent orchestration; durable execution;
human-in-the-loop primitives.

## Autonomous coding systems

**[Devin]** Cognition AI. (2024, March 12). *Introducing Devin,
the first AI software engineer.* [cognition.ai/blog/introducing-devin](https://cognition.ai/blog/introducing-devin).
13.86% on SWE-bench at launch (vs 1.96% prior SOTA); marketed
as the first fully-autonomous software engineering agent.

**[Cursor]** Anysphere, Inc. (2023–). *Cursor: AI code editor.*
[cursor.com](https://cursor.com/). VS Code fork with deep AI
integration; Cursor 3 (2026) introduced agent-first workspace
managing fleets of coding agents.

**[Aider]** Gauthier, P. (2023–). *Aider: AI pair programming in
your terminal.* GitHub: [github.com/Aider-AI/aider](https://github.com/Aider-AI/aider).
Open-source CLI tool for AI-driven edits in local git
repositories; commits with sensible messages; works with
multiple LLM backends.

**[GPT-Engineer]** Osika, A. (2023, April). *gpt-engineer: CLI
platform to experiment with codegen.* GitHub: [github.com/AntonOsika/gpt-engineer](https://github.com/AntonOsika/gpt-engineer).
One of the earliest autonomous-coding agents (55K+ stars).
One-prompt codebase generation; clarifying questions; technical
spec generation. Precursor to Lovable / [gptengineer.app](https://gptengineer.app/).

**[bolt.new]** StackBlitz. (2024–). *bolt.new: Prompt, run, edit,
and deploy full-stack web applications.* [bolt.new](https://bolt.new/);
GitHub: [github.com/stackblitz/bolt.new](https://github.com/stackblitz/bolt.new).
Browser-based AI development platform; AI agent controls
filesystem, package manager, terminal, browser console via
WebContainer technology.

**[Claude Code]** Anthropic. (2024–). *Claude Code: AI coding
assistant from Anthropic.* Documentation: [docs.claude.com/en/docs/claude-code](https://docs.claude.com/en/docs/claude-code).
Anthropic's CLI coding agent.

## Coding-agent benchmarks

**[SWE-bench]** Jimenez, C. E., Yang, J., Wettig, A., Yao, S.,
Pei, K., Press, O., & Narasimhan, K. (2024). *SWE-bench: Can
Language Models Resolve Real-World GitHub Issues?* ICLR 2024.
arXiv:2310.06770. [arxiv.org/abs/2310.06770](https://arxiv.org/abs/2310.06770).
Princeton Language and Intelligence. 2,294 software
engineering problems from 12 popular Python repositories;
each requires understanding and coordinating changes across
multiple functions, classes, or files. Established Claude 2's
1.96% baseline that Devin's 13.86% later surpassed.

**[SWE-bench Verified]** OpenAI. (2024, August). *Introducing
SWE-bench Verified.* [openai.com/index/introducing-swe-bench-verified](https://openai.com/index/introducing-swe-bench-verified/).
Filtered subset of 500 SWE-bench tasks verified for solvability;
the de-facto benchmark for autonomous coding agents in 2025.

## Workflow engines

**[Airflow]** The Apache Software Foundation. (2014–). *Apache
Airflow.* Documentation: [airflow.apache.org/docs](https://airflow.apache.org/docs/).
Workflow orchestration platform; "workflows as code" Python
DAG model; scheduler + worker + metadata DB architecture.

**[Temporal]** Temporal Technologies, Inc. (2019–). *Temporal:
Durable execution platform.* Documentation: [docs.temporal.io](https://docs.temporal.io/).
GitHub: [github.com/temporalio/temporal](https://github.com/temporalio/temporal).
Workflow durable execution: event-history replay; long-running
workflows that survive crashes; multi-language SDKs.

**[BPMN]** Object Management Group. (2014). *Business Process
Model and Notation (BPMN), Version 2.0.2.* OMG Document Number:
formal/2013-12-09. [omg.org/spec/BPMN](https://www.omg.org/spec/BPMN/).
The dominant industry standard for typed-state workflow
modeling; reference for "workflow engines with deterministic
transitions over typed state."

## Foundation models

**[Haiku-4.5]** Anthropic. (2025, October 15). *Introducing
Claude Haiku 4.5.* [anthropic.com/news/claude-haiku-4-5](https://www.anthropic.com/news/claude-haiku-4-5).
Pricing: $1/MTok input, $5/MTok output (October 2025 launch).
200K context window; 64K max output tokens; ~90% of Sonnet
4.5's performance at ~1/3 the cost on agentic-coding
benchmarks. Model ID: `claude-haiku-4-5-20251001`. Wonderland's
default model.

**[Claude-4-family]** Anthropic. (2024–2025). *Claude 4 model
family system cards.* Available via [anthropic.com/news](https://www.anthropic.com/news).
The model family Wonderland's substrate has been pilot-tested
on (Haiku 4.5 specifically).

## Software engineering

**[Beck-TDD]** Beck, K. (2002). *Test-Driven Development: By
Example.* Addison-Wesley Signature Series. ISBN
978-0-321-14653-3. The canonical reference for the red-green-
refactor cycle Wonderland's `tdd-design` + `tdd-implement`
workflows operationalize.

## Multi-agent and coordination theory

**[Contract-Net]** Smith, R. G. (1980). *The Contract Net
Protocol: High-Level Communication and Control in a Distributed
Problem Solver.* IEEE Transactions on Computers, C-29(12),
1104–1113. DOI: 10.1109/TC.1980.1675516. The classical
distributed-AI reference for negotiation-based task allocation;
ancestor of the contract-shaped negotiation Wonderland's
Tweedle pair operationalizes in M5.

**[Wooldridge-MAS]** Wooldridge, M. (2009). *An Introduction to
MultiAgent Systems* (2nd ed.). Wiley. ISBN 978-0-470-51946-2.
The standard textbook on multi-agent systems; reference for
the broader academic context Wonderland's substrate sits in.

## Literary and philosophical framing

**[Carroll-Alice]** Carroll, L. (1865). *Alice's Adventures in
Wonderland.* Macmillan. Public domain; Project Gutenberg:
[gutenberg.org/ebooks/11](https://www.gutenberg.org/ebooks/11).
The literary source for the Wonderland cast's character names
(Alice, White Rabbit, Cheshire Cat, Caterpillar, Mad Hatter,
Queen of Hearts, Tweedledee + Tweedledum, Dodo, Mock Turtle,
Dormouse).

**[Carroll-Looking-Glass]** Carroll, L. (1871). *Through the
Looking-Glass, and What Alice Found There.* Macmillan. Public
domain; Project Gutenberg: [gutenberg.org/ebooks/12](https://www.gutenberg.org/ebooks/12).
Source for the Tweedles' pair-protocol framing.

**[Scholem-Kabbalah]** Scholem, G. (1941). *Major Trends in
Jewish Mysticism.* Schocken Books, New York. The canonical
academic introduction to Kabbalistic tradition cited in
§2.2 (Corollary 2 — failure modes as identity) for the
Sephirah/Qlipha pairing framework. The framing of each
virtue carrying its specific shadow as a load-bearing
constitutional structure derives from this tradition.

## Wonderland project artifacts

**[Wonderland-Repo]** Jary, K. (2024–). *Wonderland.* Open-source
repository: [github.com/KohlJary/wonderland](https://github.com/KohlJary/wonderland).
The substrate implementation, pilot artifacts, analyses, memory
pins, release notes, and per-chapter source material that
underlie the paper's claims. Substrate version cited throughout
as 0.10.2 + T-ab62 + T-ab64.

**[Wonderland-Comparison]** Jary, K. (2026). *Comparison
Baselines.* In Wonderland repository under
`paper/artifacts/comparison-baselines/`. Includes single-shot
Haiku, single-shot Sonnet, and Claude-Code agentic baselines
against the notebook directive; adversarial-review-of-baselines
analysis finding 30 blocker-class bugs across 4 single-shot
baselines that ship code without any review pass.

**[Wonderland-Analyses]** Jary, K. (2024–). *Pilot analyses
directory.* In Wonderland repository under
`src/wonderland/closet/analyses/`. ~46 numbered chronological
analyses of pilot events and substrate iterations. Key
analyses cited: 004 (silence-as-settlement), 027 (visible
degradation + recovery via disk channel), 033 (mvp cost
breakdown), 034 (mvp Tier 2 autonomous pilot completion),
040 (tdd-design order rationale), 046 (mvp-redux cost
receipt — the $83.78 → $30.58 trajectory).

---

## Notes on bibliographic stability

URL stability rankings (most to least stable):
1. **arXiv IDs** — permanent; cite by ID, URL is convenience
2. **ISBNs** — permanent
3. **DOIs** — permanent
4. **GitHub repos** — stable while project active; org transfers
   possible (Aider's `paul-gauthier/aider` → `Aider-AI/aider`
   noted in citation)
5. **Corporate blog posts** — stable for well-maintained corps
   but not guaranteed (Anthropic, Cognition, Microsoft)
6. **Documentation sites** — generally stable but versions may
   shift

For an arXiv-shaped paper preparation, prefer arXiv IDs + ISBNs
where available; cite URLs as access vectors but treat the IDs
as the canonical identifier.

## Items deliberately omitted

- **Wonderland project memory pins** (`.claude/projects/...`)
  and **release notes** — internal project artifacts that
  shouldn't appear in the bibliography. The paper cites them
  inline as project-internal references with brief inline
  descriptions where needed.
- **Roadmap item IDs** (e.g., `b3f440c8`) — internal
  identifiers; not bibliography-worthy. First use of each in
  the paper text is accompanied by an inline definition.
- **T-ab task IDs** (e.g., `T-ab51`) — same treatment as
  roadmap items.
- **Hypothesis-grade observations** (e.g.,
  `project_haiku_is_architecturally_optimal.md`) — explicitly
  excluded from evidence chapter and bibliography both;
  surfaced in limitations / future work as honest open
  questions.

## Citation conventions used in paper text

- First mention of a system: full name with bracketed
  citation. *"Wonderland sits in a gap between three categories
  the field already names: multi-agent frameworks like AutoGen
  [AutoGen], MetaGPT [MetaGPT], and ChatDev [ChatDev]; workflow
  engines like Airflow [Airflow] and Temporal [Temporal]; and
  autonomous coding systems like Devin [Devin], Cursor
  [Cursor], Aider [Aider], GPT-Engineer [GPT-Engineer], and
  bolt.new [bolt.new]."*
- Subsequent mentions: short form, no re-citation.
- Substrate-version-specific claims about Anthropic models
  carry [Haiku-4.5] inline.
- TDD methodology mentions carry [Beck-TDD] on first
  meaningful invocation in §3 (architecture) where
  red-green-refactor is named.
- Carroll character references in §4 (cast) carry
  [Carroll-Alice] / [Carroll-Looking-Glass] as appropriate
  at first character introduction.
- Sephirah/Qlipha in §2 corollary 2 carries [Scholem-Kabbalah].
