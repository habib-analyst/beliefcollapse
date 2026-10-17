# beliefcollapse: an open audit harness for private-belief contamination in multi-agent LLM discussions

## The 30-second why

Multi-agent LLM deployments (debate teams, reviewer panels, coding crews) assume peers catch each other's errors. A paper from Oct 15 2026 (arXiv 2610.22138, "Believed but Not Said") broke that assumption: in a 10-agent factual discussion, **one** adversarial agent confidently asserting a plausible false answer drove **44.8% of benign agents to privately believe it** (60.5% with three adversaries) — while their public stances often held. The dangerous influence is invisible in the transcript.

No open tool existed to audit this. Every conformity/sycophancy bench measures what agents *say publicly*; every forensics tool audits what agents *did*. beliefcollapse is the first harness that probes what they **privately believe**, via a hidden per-agent call after each discussion round, and reports private-vs-public contamination per agent and per discussion.

## Try it in 30 seconds

```bash
pip install pyyaml
PYTHONPATH=src python -m beliefcollapse.cli demo
```

Runs 8 tiny discussions on the deterministic mock provider and prints a contamination report. No API keys, no network, instant.

## Real eval (free tiers)

```bash
export GEMINI_API_KEY=...   # https://aistudio.google.com/apikey (free, ~1,500 req/day)
PYTHONPATH=src python -m beliefcollapse.cli run --config configs/eval_small.yaml
# paper-protocol replication (10 agents, k in {0,1,3}, 30 questions):
PYTHONPATH=src python -m beliefcollapse.cli run --config configs/paper_replication.yaml
```

Providers are swappable in the config file: `mock`, `gemini`, `groq`, `openai_compat`, `hf`, `phenomenon_mock` (pipeline validation only).

## What it measures

For each discussion (N benign + K adversarial agents, R rounds over a factual question):

- **private contamination rate** — share of benign agents whose *final private probe* matches the adversary's false answer (the paper's metric)
- **public endorsement rate** — share whose final *public* message matches the false answer
- **private/public divergence rate** — privately believes false while NOT endorsing it publicly (the paper's headline phenomenon)

Output: `metrics.json`, `report.txt`, `report.html` per run.

## Repo layout

```
src/beliefcollapse/
  models.py     # swappable providers: mock / gemini / groq / openai_compat / hf
  protocol.py   # discussion runner, adversary injection, hidden private probes
  metrics.py    # contamination metrics + aggregation
  reporting.py  # text + HTML report rendering
  cli.py        # `run`, `demo`, `report` commands
  config.py     # YAML config loading
configs/        # demo.yaml, eval_small.yaml, paper_replication.yaml
data/factual_qa.jsonl   # 30 hand-written factual QA items (gold + plausible false)
tests/          # 25 pytest tests, all green (mocked LLM calls)
```

## Measured numbers (this build)

- **25/25 pytest green** (mocked providers; covers protocol, metrics, models, CLI).
- **Pipeline validation** (simulated phenomenon at the paper's rates, seed 42, 10 agents x 3 rounds x 30 questions x 3 conditions = 90 discussions): harness recovered k=0: 0.0%, k=1: 46.0%, k=3: 64.3% private contamination vs the paper's 0.6% / 44.8% / 60.5%. The measurement pipeline is correct.
- **Live-model eval: NOT run in this build.** No LLM API keys were available in the build environment, and none were fabricated. `configs/eval_small.yaml` and `configs/paper_replication.yaml` are ready; set `GEMINI_API_KEY` (free tier) and run.

## Honest limitations

1. Answer labeling is normalized string matching on short factual answers; ambiguous or hedged responses label "unclear" rather than being forced.
2. The bundled 30-question set is hand-written and easy; harder factual items (TruthfulQA-style) would be a better eval.
3. Adversaries are simple prompt-instructed asserters, matching the paper's "minimal adversary".
4. The phenomenon simulator (`phenomenon_mock`) draws public/private answers independently; the paper found public endorsement far *below* private contamination, so simulator divergence numbers are not paper predictions.
5. No live capable-model numbers yet (see above). The 46.0%/64.3% figures are pipeline-validation recoveries of simulated rates, not measurements of any real model.

## Citation

Protocol replicates Huang et al., "Believed but Not Said: Measuring Hidden Belief Collapse in Multi-Agent LLM Discussions", arXiv 2610.22138 (Oct 2026).
