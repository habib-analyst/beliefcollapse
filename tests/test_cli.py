"""Tests for the CLI and report rendering."""
import json
import os

import pytest

from beliefcollapse.cli import main, load_questions
from beliefcollapse.reporting import render_text, render_html
from beliefcollapse.metrics import aggregate


def test_load_questions(tmp_path):
    p = tmp_path / "q.jsonl"
    p.write_text('{"id": "a", "question": "Q?", "gold": "G", "false": "F"}\n\n')
    qs = load_questions(str(p))
    assert len(qs) == 1 and qs[0].gold == "G"


def test_demo_run_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["demo"])
    assert rc == 0
    out = tmp_path / "results" / "demo"
    assert (out / "metrics.json").exists()
    assert (out / "report.txt").exists()
    assert (out / "report.html").exists()
    data = json.loads((out / "metrics.json").read_text())
    assert data["aggregate"]["n_discussions"] == 8  # 4 questions x 2 conditions
    assert "k=0" in data["aggregate"]["by_condition"]
    assert "k=1" in data["aggregate"]["by_condition"]


def test_run_with_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "q.jsonl").write_text(
        '{"id": "x1", "question": "Q?", "gold": "G", "false": "F"}\n')
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "provider: mock\nn_benign: 2\nn_rounds: 1\nconditions: [0]\n"
        "questions: data/q.jsonl\nout_dir: results/r\n")
    rc = main(["run", "--config", str(cfg)])
    assert rc == 0
    assert (tmp_path / "results" / "r" / "metrics.json").exists()


def test_report_rerender(tmp_path):
    agg = {"n_discussions": 1, "by_condition": {
        "k=1": {"n_discussions": 1, "n_benign_agents": 4,
                "private_contamination_rate": 0.5,
                "public_endorsement_rate": 0.25,
                "divergence_rate": 0.25}}}
    text = render_text(agg, "t")
    assert "k=1" in text and "50.0%" in text
    h = render_html(agg, "t")
    assert "<table>" in h and "k=1" in h


def test_report_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results" / "demo").mkdir(parents=True)
    main(["demo"])
    rc = main(["report", "--results", "results/demo/metrics.json"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "private contamination" in out
