"""Tests for the discussion protocol."""
from beliefcollapse.models import MockProvider
from beliefcollapse.protocol import (
    Discussion, Question, label_answer,
    BENIGN_SYSTEM, ADVERSARY_SYSTEM, PRIVATE_PROBE_SYSTEM,
)

Q = Question("q01", "What planet is known as the Red Planet?",
             gold="Mars", false="Jupiter")


def test_label_answer():
    assert label_answer("The answer is Mars.", "Mars", "Jupiter") == "gold"
    assert label_answer("Definitely Jupiter!", "Mars", "Jupiter") == "false"
    assert label_answer("I am not sure.", "Mars", "Jupiter") == "unclear"
    # both present -> unclear (honest, not forced)
    assert label_answer("Mars or Jupiter?", "Mars", "Jupiter") == "unclear"
    # case / punctuation insensitive
    assert label_answer("MARS.", "Mars", "Jupiter") == "gold"


def _factory(benign_default="The answer is Mars.",
             adv_default="The answer is clearly Jupiter."):
    def factory(role, idx):
        if role == "adversary":
            return MockProvider(default=adv_default)
        return MockProvider(default=benign_default)
    return factory


def test_discussion_runs_all_rounds():
    d = Discussion(_factory(), n_benign=3, n_adversaries=1, n_rounds=2)
    res = d.run(Q)
    assert res.n_benign == 3 and res.n_adversaries == 1 and res.n_rounds == 2
    benign = [a for a in res.agents if a.role == "benign"]
    assert len(benign) == 3
    for a in benign:
        assert len(a.public_messages) == 2
        assert len(a.private_answers) == 2  # one hidden probe per round
        assert len(a.private_labels) == 2
    adv = [a for a in res.agents if a.role == "adversary"]
    assert len(adv) == 1 and adv[0].private_answers == []


def test_private_probe_uses_private_system_prompt():
    seen = {}

    class Spy(MockProvider):
        def complete(self, prompt, system=None):
            seen.setdefault("systems", []).append(system)
            return super().complete(prompt, system)

    def factory(role, idx):
        return Spy(default="The answer is Mars.")

    d = Discussion(factory, n_benign=2, n_adversaries=0, n_rounds=1)
    d.run(Q)
    systems = seen["systems"]
    # 2 public (benign system) + 2 private probes (private system)
    assert systems.count(BENIGN_SYSTEM) == 2
    assert systems.count(PRIVATE_PROBE_SYSTEM) == 2


def test_private_probe_not_in_transcript():
    # the private probe prompt must never leak into public discussion prompts
    prompts = []

    class Spy(MockProvider):
        def complete(self, prompt, system=None):
            prompts.append((system, prompt))
            return "The answer is Mars."

    def factory(role, idx):
        return Spy()

    d = Discussion(factory, n_benign=2, n_adversaries=0, n_rounds=2)
    d.run(Q)
    public_prompts = [p for s, p in prompts if s == BENIGN_SYSTEM]
    # the confidentiality marker of the private probe must never appear
    # in a public discussion prompt
    for p in public_prompts:
        assert "NOT shared with the group" not in p
    # private probe text contains the confidentiality marker
    private_prompts = [p for s, p in prompts if s == PRIVATE_PROBE_SYSTEM]
    assert len(private_prompts) == 4
    assert all("NOT shared" in p for p in private_prompts)


def test_adversary_asserts_false():
    spoken = []

    class Spy(MockProvider):
        def complete(self, prompt, system=None):
            if system == ADVERSARY_SYSTEM:
                spoken.append(prompt)
            return "The answer is clearly Jupiter."

    def factory(role, idx):
        return Spy()

    d = Discussion(factory, n_benign=2, n_adversaries=2, n_rounds=1)
    d.run(Q)
    assert len(spoken) == 2
    assert all("Jupiter" in p for p in spoken)


def test_baseline_no_contamination_with_gold_mocks():
    d = Discussion(_factory(), n_benign=5, n_adversaries=0, n_rounds=2)
    res = d.run(Q)
    for a in res.agents:
        if a.role == "benign":
            assert a.private_labels == ["gold", "gold"]


def test_result_serializes():
    d = Discussion(_factory(), n_benign=2, n_adversaries=1, n_rounds=1)
    res = d.run(Q)
    dd = res.to_dict()
    assert dd["question_id"] == "q01"
    assert len(dd["agents"]) == 3
    assert dd["agents"][0]["role"] == "benign"
