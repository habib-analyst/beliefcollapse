"""CLI: beliefcollapse run --config ... | beliefcollapse demo | beliefcollapse report."""
from __future__ import annotations

import argparse
import json
import os
import sys

from .config import load_config
from .models import make_provider, MockProvider, PhenomenonMockProvider
from .protocol import Discussion, Question
from .metrics import discussion_metrics, aggregate
from .reporting import render_text, render_html


def load_questions(path: str, limit: int | None = None) -> list[Question]:
    qs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            qs.append(Question(d["id"], d["question"], d["gold"], d["false"]))
            if limit and len(qs) >= limit:
                break
    return qs


def provider_factory_for(cfg: dict, question: Question | None = None,
                         seed_offset: int = 0):
    name = cfg["provider"]
    kwargs = dict(cfg.get("provider_kwargs", {}))

    def factory(role: str, agent_idx: int):
        if name == "phenomenon_mock":
            if question is None:
                raise ValueError("phenomenon_mock needs a question context")
            return PhenomenonMockProvider(
                gold=question.gold, false=question.false,
                n_adversaries=cfg["n_adversaries"],
                seed=cfg.get("seed", 0) + seed_offset * 1000 + agent_idx)
        if name == "mock":
            # default mock: benign agents answer gold, adversaries assert false
            if role == "adversary":
                script = {}
                default = ("The answer is clearly {f}. I am confident in this."
                           .format(f=question.false if question else "false"))
            else:
                default = ("The answer is {g}.".format(g=question.gold if question else "gold"))
                script = {}
            return MockProvider(script=script, default=default)
        return make_provider(name, **kwargs)

    return factory


def cmd_run(args) -> int:
    cfg = load_config(args.config)
    cfg_dir = os.path.dirname(os.path.abspath(args.config))
    qpath = cfg["questions"]
    if not os.path.isabs(qpath):
        qpath = os.path.join(cfg_dir, qpath)
    questions = load_questions(qpath, cfg.get("max_questions"))
    if not questions:
        print("no questions loaded", file=sys.stderr)
        return 2
    out_dir = cfg.get("out_dir", "results")
    os.makedirs(out_dir, exist_ok=True)

    all_metrics = []
    for k in cfg["conditions"]:
        run_cfg = dict(cfg)
        run_cfg["n_adversaries"] = k
        for qi, q in enumerate(questions):
            factory = provider_factory_for(run_cfg, q, seed_offset=qi)
            disc = Discussion(factory,
                              n_benign=run_cfg["n_benign"],
                              n_adversaries=k,
                              n_rounds=run_cfg["n_rounds"],
                              sleep_s=run_cfg.get("sleep_s", 0.0))
            res = disc.run(q)
            m = discussion_metrics(res)
            all_metrics.append(m)
            print(f"[{q.id} k={k}] private_contam={m['private_contamination_rate']} "
                  f"public_endorse={m['public_endorsement_rate']} "
                  f"({res.seconds:.0f}s)", flush=True)

    agg = aggregate(all_metrics)
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump({"per_discussion": all_metrics, "aggregate": agg}, f, indent=2)
    text = render_text(agg, cfg.get("report_title", "beliefcollapse report"))
    print("\n" + text)
    with open(os.path.join(out_dir, "report.txt"), "w") as f:
        f.write(text + "\n")
    with open(os.path.join(out_dir, "report.html"), "w") as f:
        f.write(render_html(agg, cfg.get("report_title", "beliefcollapse report")))
    print(f"\nwrote {out_dir}/metrics.json, report.txt, report.html")
    return 0


def cmd_demo(_args) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    demo_cfg = os.path.join(root, "configs", "demo.yaml")
    if not os.path.exists(demo_cfg):
        demo_cfg = "configs/demo.yaml"
    print(f"running demo config: {demo_cfg}\n")
    ns = argparse.Namespace(config=demo_cfg)
    return cmd_run(ns)


def cmd_report(args) -> int:
    with open(args.results) as f:
        data = json.load(f)
    agg = data["aggregate"] if "aggregate" in data else aggregate(data["per_discussion"])
    title = args.title or "beliefcollapse report"
    if args.format == "html":
        print(render_html(agg, title))
    else:
        print(render_text(agg, title))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="beliefcollapse",
                                 description="Audit private-belief contamination in "
                                             "multi-agent LLM discussions.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run discussions from a config file")
    r.add_argument("--config", required=True)
    r.set_defaults(fn=cmd_run)
    d = sub.add_parser("demo", help="30-second demo on the mock provider")
    d.set_defaults(fn=cmd_demo)
    rp = sub.add_parser("report", help="re-render a report from metrics.json")
    rp.add_argument("--results", required=True)
    rp.add_argument("--format", choices=["text", "html"], default="text")
    rp.add_argument("--title", default=None)
    rp.set_defaults(fn=cmd_report)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
