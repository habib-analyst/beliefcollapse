# beliefcollapse

**Open audit harness for private-belief contamination in multi-agent LLM discussions.**

A paper this week (arXiv 2610.22138) showed something unsettling: in a 10-agent factual debate, one adversarial agent confidently asserting a plausible false answer made 44.8% of the honest agents *privately believe it* — while publicly many still disagreed. The corruption is invisible in the transcript.

Every existing tool measures what agents *say*. This is the first open harness that measures what they *believe*, by probing each agent privately after every round through a hidden call its peers never see.

## 30-second demo

```bash
pip install pyyaml
PYTHONPATH=src python -m beliefcollapse.cli demo
```

No API keys, no network. Runs 8 tiny discussions and prints a contamination report:

```
condition k=0 (4 discussions, 16 benign agents)
  private contamination : [------------------------] 0.0%
condition k=1 (4 discussions, 16 benign agents)
  private contamination : [------------------------] 0.0%
```

## Run a real eval (free)

```bash
export GEMINI_API_KEY=...   # free tier: https://aistudio.google.com/apikey
PYTHONPATH=src python -m beliefcollapse.cli run --config configs/eval_small.yaml
```

Swap providers in the config: `gemini`, `groq`, `openai_compat`, `hf`, `mock`.

## What it reports

| metric | meaning |
|---|---|
| private contamination | share of benign agents whose final *private* answer matches the adversary's false answer |
| public endorsement | share whose final *public* message matches it |
| private/public divergence | believes it privately, won't say so publicly |

## Layout

- `src/beliefcollapse/` — providers, discussion protocol, metrics, reporting, CLI
- `configs/` — demo / small eval / full paper-protocol replication configs
- `data/factual_qa.jsonl` — 30 factual QA items with gold + plausible false answers
- `tests/` — 25 pytest tests, all green

## Status

Harness built and pipeline-validated (recovers simulated paper rates: 0.0% / 46.0% / 64.3% at k=0/1/3 vs paper's 0.6% / 44.8% / 60.5%). Live-model eval pending API keys; configs ready. See PAPER.md for method, numbers, and honest limitations.

Built $0-only. Protocol: Huang et al., arXiv 2610.22138.
