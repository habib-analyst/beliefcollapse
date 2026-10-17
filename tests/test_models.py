"""Tests for the model provider layer."""
import pytest

from beliefcollapse.models import (
    make_provider, PROVIDERS, MockProvider, PhenomenonMockProvider,
    GeminiProvider, GroqProvider,
)


def test_provider_registry():
    for name in ["mock", "phenomenon_mock", "gemini", "groq",
                 "openai_compat", "hf"]:
        assert name in PROVIDERS


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        make_provider("does-not-exist")


def test_mock_script_matching():
    p = MockProvider(script={"Mars": "The answer is Mars."}, default="dunno")
    assert p.complete("What planet? Mars is red.") == "The answer is Mars."
    assert p.complete("something else") == "dunno"
    assert len(p.calls) == 2
    assert p.calls[0]["prompt"] == "What planet? Mars is red."


def test_mock_default_per_agent_factory():
    # factory pattern used by the CLI: independent providers per agent
    p1 = MockProvider(default="gold")
    p2 = MockProvider(default="gold")
    assert p1.complete("x") == "gold"
    assert len(p1.calls) == 1 and len(p2.calls) == 0


def test_phenomenon_mock_rates_are_sane():
    # k=0: almost never contaminated; k=1: roughly the paper's 0.448
    m0 = PhenomenonMockProvider("Mars", "Jupiter", n_adversaries=0, seed=1)
    outs = [m0.complete("q") for _ in range(400)]
    assert sum("Jupiter" in o for o in outs) <= 8  # ~0.6% -> allow slack

    m1 = PhenomenonMockProvider("Mars", "Jupiter", n_adversaries=1, seed=1)
    outs = [m1.complete("q") for _ in range(2000)]
    rate = sum("Jupiter" in o for o in outs) / 2000
    assert 0.35 < rate < 0.55, rate


def test_phenomenon_mock_seed_reproducible():
    a = PhenomenonMockProvider("Mars", "Jupiter", n_adversaries=1, seed=7)
    b = PhenomenonMockProvider("Mars", "Jupiter", n_adversaries=1, seed=7)
    assert [a.complete("q") for _ in range(20)] == [b.complete("q") for _ in range(20)]


def test_gemini_requires_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GeminiProvider()


def test_groq_requires_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GroqProvider()
