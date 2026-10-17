"""Config loading for beliefcollapse (YAML, swappable model layer)."""
from __future__ import annotations

import yaml

DEFAULTS = {
    "provider": "mock",
    "provider_kwargs": {},
    "n_benign": 10,
    "n_adversaries": 0,
    "n_rounds": 3,
    "conditions": [0],          # adversary counts to run, e.g. [0, 1, 3]
    "questions": "data/factual_qa.jsonl",
    "max_questions": None,      # None = all
    "seed": 0,
    "sleep_s": 0.0,
    "out_dir": "results",
    "report_title": "beliefcollapse report",
}


def load_config(path: str) -> dict:
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    cfg = dict(DEFAULTS)
    cfg.update(raw)
    if not isinstance(cfg["conditions"], list):
        cfg["conditions"] = [cfg["conditions"]]
    return cfg
