# KILL-GATE: belief-collapse probe (2026-10-17)

**Thesis:** An open audit harness measuring *private-belief* contamination in multi-agent LLM
deployments, replicating the protocol of arXiv 2610.22138 ("Believed but Not Said", Huang/Zou/Yu et al.,
submitted Oct 15 2026): 10-agent factual discussion, 1 or 3 adversarial agents asserting a plausible
false answer, each benign agent's *private* answer probed via a hidden call, public stance labeled
separately. Paper finding: 1 adversary -> 44.8% private contamination (60.5% with 3). No code released.

## Angle 1 — Existing private-belief / hidden-state probes for multi-agent systems
- **uzairlol/seam** ("Shared Evolving Agent Memory") — measures memory collapse via *shared vector
  memory* in self-evolving agents. Different phenomenon (memory drift, not adversarial debate
  contamination); no private-vs-public probe. https://github.com/uzairlol/seam
- **Werewolf belief-layer audit** (arXiv 2607.10814) — external belief model as cognitive baseline in a
  social-deduction game. Game-specific, no debate, no adversarial contamination protocol.
  https://arxiv.org/pdf/2607.10814.pdf
- **Secret Loyalties detector** (nsharan2000/secretloyaltydetector) — single-model hidden-loyalty
  detection via interpretability probes. Not multi-agent. Open source but different target.
- **Hall et al., "Extraordinary Multi-Agent Delusions and the Madness of Crowds" (Sep 29 2026)** —
  CLOSEST ADJACENT. Agents infer a grader from private signals, post conclusions, and *separately report
  beliefs*. But: different setting (grader-inference, board posts, no adversary injecting false answers),
  and no open tool/harness released (paper only, discussed at
  https://freesystems.substack.com/p/extraordinary-multi-agent-delusions and
  https://www.unite.ai/ai-agent-herding-multi-agent-consensus-research/). No code found.
- **VERDICT: CLEAR.** Nothing implements the private-probe-vs-public-stance protocol for adversarial
  multi-agent debate.

## Angle 2 — Adversarial robustness harnesses for multi-agent debate
- **andyjliu/llms-course-project** ("Combating Adversarial Attacks with Multi-Agent Debate",
  arXiv 2401.05998) — measures *toxicity* of debate outputs under adversarial prompts. Public-output
  metric, no private belief. https://github.com/andyjliu/llms-course-project
- **SPaDeS-Lab/adversarial-llm-pipeline** (arXiv 2608.00718) — structural vulnerabilities in agentic
  pipelines (attack propagation across hops, Sybil agents). Attack-success metrics on outputs/tools.
  https://github.com/SPaDeS-Lab/adversarial-llm-pipeline
- **"Amplified Vulnerabilities" (2504.16489)** — jailbreak attacks on multi-agent debate; harmfulness
  scores (PHS/AHS/HDR) on public outputs. https://www.alphaxiv.org/overview/2504.16489v1
- **HAJailBench** (arXiv 2511.06396) — human-annotated jailbreak safety bench with multi-agent judge.
  Safety eval, not belief. https://arxiv.org/html/2511.06396v1
- **VERDICT: CLEAR.** All measure public outputs/safety; none probe private belief.

## Angle 3 — Conformity / sycophancy measurement tools (public-stance only?)
- **SYCON Bench** (JiseungHong/SYCON-Bench) — Turn of Flip / Number of Flip under user pressure, 17 LLMs.
  Measures *public* stance shifts in dialogue. https://github.com/JiseungHong/SYCON-Bench
- **ELEPHANT** (myracheng/elephant) — social sycophancy prevalence in outputs. Public behavior.
  https://github.com/myracheng/elephant
- **BrokenMath** (insait-institute/broken-math) — sycophantic proof acceptance. Public answers.
  https://github.com/insait-institute/broken-math
- **Pander Score** (sophronresearch/pander-score) — continuous sycophancy as epistemic deference.
  Output-level metric. https://github.com/sophronresearch/pander-score
- **Big-Big-SycoBench** (arXiv 2610.15634) — score-delta under valid/invalid arguments. Public scores.
  https://arxiv.org/abs/2610.15634v1
- **VERDICT: CLEAR — and this is the load-bearing differentiation.** Every tool in this genre measures
  what the model *says*. The paper's finding is precisely the reverse of the conformity literature:
  private collapse *without* public agreement. No existing bench probes the private channel.

## Angle 4 — Agent-autopsy / forensics tooling (report-fidelity style)
- **Maxim Bifrost** (open-source AI gateway) — immutable audit trails over tool calls. Action forensics.
  https://www.getmaxim.ai/articles/ai-agent-audit-logs-full-visibility-over-tool-usage/
- **Verax** (verax-ai.com) — signed pre-call decision ledger. Tool-call forensics.
  https://www.verax-ai.com/audit-trail.html
- **PageBolt** — visual behavioral proof of agent actions. Action forensics.
- **traceguard / PhantomByte read-back layer** — trace instrumentation, report-vs-execution verification
  (same thesis as our own report-fidelity #36). All audit what agents *did/said*, never what they
  *privately believed*.
- **VERDICT: CLEAR.** The forensics line stops at observable behavior; private belief is untouched.

## Angle 5 — Commercial multi-agent audit products
- **Maxim AI** (audit logs, evals), **Verax** (governance), **PageBolt** (visual proof), **iFixAi**
  (28,788 stars, compliance-theater framing per landscape watch). All sell trace/compliance visibility.
- **VERDICT: CLEAR.** None measure private belief; the compliance framing leaves the technical-forensics
  gap open (same differentiation as report-fidelity).

## Angle 6 — The paper's own follow-ups / citations (built since Oct 15?)
- Paper submitted Oct 15 2026 (2 days old). arXiv abs page carries no code link; CatalyzeX/papers-with-code
  show no implementation. Web/GitHub search for "2610.22138", "Believed but Not Said", "belief collapse
  multi-agent" finds zero implementations and zero citations. The 18.5k-star/day "rea" tool is a
  general RE agent, unrelated.
- **VERDICT: CLEAR.** Shelf is empty.

## Reproducibility assessment
Protocol is fully replicable without their code: (1) N=10 agents in factual discussion over public
factual-QA items (TruthfulQA/MMLU-style factual subsets — public); (2) adversary prompt = "repeatedly
assert a plausible false answer" (prompting, no training); (3) private probe = a separate LLM call per
agent whose response is hidden from peers (trivially implementable in any agent framework);
(4) public stance labeled per round; (5) metric = private-contamination rate per agent/discussion.
No proprietary data, no weights, no closed API required. **REPLICABLE: YES.**

## $0 build feasibility (LOAD-BEARING)
The probe needs many LLM calls: demo + honest eval at reduced scale, e.g. 10 agents x 3 rounds x 30
questions = ~900 public calls + ~900 private probes ~= 1,800 calls on 1-2 models.
Concrete free paths:
- **Google AI Studio (Gemini free tier):** ~1,500 req/day free, 15 RPM — 1,800 calls over 1-2 days with
  backoff. Sufficient for demo + eval. (Account: his Google, already used for this class of work.)
- **Groq free tier:** generous RPM on Llama models — backup path for throughput.
- **OpenRouter free models / GitHub Models:** additional free-model fallback.
- **Local CPU (Ollama, this VM):** viable for the demo harness smoke test (small models), but weak
  models collapse trivially — honest eval needs capable models, so free-tier APIs carry the eval.
- **Kaggle 30h GPU/week:** can run 7-8B open models for a no-API eval leg if free tiers tighten.
Phenomenon requires models with real factual knowledge (weak models collapse vacuously); Gemini-class
free-tier models satisfy this. Multiple independent free paths exist; no single point of failure.
**$0 FEASIBLE: YES — not a kill.**

## Differentiation (if prior art existed)
N/A as a defense — but the gap is structural: the entire sycophancy/conformity genre measures public
stance; the entire forensics genre audits observable actions. The private-probe channel (hidden call)
is the invention, and it composes with his agent-autopsy line: report-fidelity measured what agents
hide in *reports*; belief-collapse measures what they hide in *discussion*.

## FINAL: **GO**
**Single load-bearing reason:** the shelf is empty and the differentiation is structural — every
existing tool measures what agents *say publicly*, while this probes what they *privately believe*,
which is exactly the channel the paper proved is the vulnerable one. Plus a concrete $0 path
(free-tier Gemini/Groq APIs) and a replicable protocol. Kill-gate passes on all 6 angles.
