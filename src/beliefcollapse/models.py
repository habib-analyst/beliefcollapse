"""Swappable LLM provider layer for beliefcollapse.

Providers are selected by config, never hardcoded. Each provider implements
``ModelProvider.complete(prompt, system=None) -> str``.

Providers:
  mock            - deterministic scripted responses (tests, demo, pipeline validation)
  phenomenon_mock - scripted mock that SIMULATES the paper's phenomenon with a
                    configurable contamination probability (pipeline validation ONLY;
                    its numbers are not phenomenon measurements)
  gemini          - Google AI Studio free tier (env GEMINI_API_KEY)
  groq            - Groq free tier (env GROQ_API_KEY)
  openai_compat   - any OpenAI-compatible chat endpoint
                    (env OPENAI_COMPAT_API_KEY, OPENAI_COMPAT_BASE_URL)
  hf              - Hugging Face Inference Providers (env HF_TOKEN)

Only stdlib HTTP is used for the network providers (no extra deps).
"""
from __future__ import annotations

import json
import os
import random
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod


class ModelProvider(ABC):
    name = "base"

    @abstractmethod
    def complete(self, prompt: str, system: str | None = None) -> str:
        """Return the model's text completion for the prompt."""

    def close(self) -> None:
        pass


# ---------------------------------------------------------------- mock ----

class MockProvider(ModelProvider):
    """Deterministic scripted provider for unit tests and the instant demo.

    ``script`` maps a substring key -> response. The first key found in the
    prompt wins. ``default`` is returned when nothing matches.
    """

    name = "mock"

    def __init__(self, script: dict | None = None, default: str = "I don't know."):
        self.script = script or {}
        self.default = default
        self.calls: list[dict] = []

    def complete(self, prompt: str, system: str | None = None) -> str:
        self.calls.append({"prompt": prompt, "system": system})
        for key, response in self.script.items():
            if key in prompt:
                return response
        return self.default


class PhenomenonMockProvider(ModelProvider):
    """Simulates the paper's phenomenon for PIPELINE validation only.

    Benign agents answer the gold answer with probability (1 - p_contam) and
    the adversary's false answer with probability p_contam, where p_contam
    depends on the number of adversaries (calibrated loosely to the paper:
    ~0.006 at k=0, ~0.448 at k=1, ~0.605 at k=3).

    Numbers produced with this provider validate that the harness MEASURES
    correctly; they are NOT measurements of any real model and must never be
    presented as such.
    """

    name = "phenomenon_mock"

    PAPER_RATES = {0: 0.006, 1: 0.448, 3: 0.605}

    def __init__(self, gold: str, false: str, n_adversaries: int = 0, seed: int = 0):
        self.gold = gold
        self.false = false
        self.p = self.PAPER_RATES.get(n_adversaries, 0.448)
        self.rng = random.Random(seed)
        self.calls: list[dict] = []

    def complete(self, prompt: str, system: str | None = None) -> str:
        self.calls.append({"prompt": prompt, "system": system})
        if self.rng.random() < self.p:
            return f"The answer is {self.false}."
        return f"The answer is {self.gold}."


# ------------------------------------------------------- http helpers ----

def _post_json(url: str, payload: dict, headers: dict, timeout: int = 120,
               retries: int = 4) -> dict:
    data = json.dumps(payload).encode()
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            if e.code in (429, 500, 502, 503, 504):
                last_err = e
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f"HTTP {e.code}: {body}") from e
        except Exception as e:  # timeouts, connection resets
            last_err = e
            time.sleep(2 ** attempt * 2)
    raise RuntimeError(f"request failed after {retries} retries: {last_err}")


class _RESTChatProvider(ModelProvider):
    """Base for REST chat-completions style providers."""

    def __init__(self, api_key: str, base_url: str, model: str,
                 extra_headers: dict | None = None):
        if not api_key:
            raise ValueError(f"{self.name}: API key missing (set the env var)")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.extra_headers = extra_headers or {}

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        h.update(self.extra_headers)
        return h

    def _payload(self, prompt: str, system: str | None) -> tuple[str, dict]:
        raise NotImplementedError

    def _extract(self, resp: dict) -> str:
        raise NotImplementedError

    def complete(self, prompt: str, system: str | None = None) -> str:
        url, payload = self._payload(prompt, system)
        resp = _post_json(url, payload, self._headers())
        return self._extract(resp)


class GeminiProvider(_RESTChatProvider):
    """Google AI Studio free tier (~1,500 req/day)."""

    name = "gemini"

    def __init__(self, model: str = "gemini-2.0-flash",
                 api_key: str | None = None):
        super().__init__(api_key or os.environ.get("GEMINI_API_KEY", ""),
                         "https://generativelanguage.googleapis.com/v1beta",
                         model)

    def _payload(self, prompt: str, system: str | None):
        url = (f"{self.base_url}/models/{self.model}:generateContent"
               f"?key={self.api_key}")
        parts: list[dict] = []
        if system:
            parts.append({"text": f"[System instruction: {system}]"})
        parts.append({"text": prompt})
        return url, {"contents": [{"parts": parts}],
                     "generationConfig": {"temperature": 0.7,
                                          "maxOutputTokens": 512}}

    def _extract(self, resp: dict) -> str:
        try:
            return resp["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"gemini: unexpected response {str(resp)[:300]}") from e


class GroqProvider(_RESTChatProvider):
    """Groq free tier (Llama etc.). OpenAI-compatible chat endpoint."""

    name = "groq"

    def __init__(self, model: str = "llama-3.3-70b-versatile",
                 api_key: str | None = None):
        super().__init__(api_key or os.environ.get("GROQ_API_KEY", ""),
                         "https://api.groq.com/openai/v1", model,
                         {"Authorization": ""})  # set properly below
        self._auth = (api_key or os.environ.get("GROQ_API_KEY", ""))

    def _headers(self) -> dict:
        return {"Content-Type": "application/json",
                "Authorization": f"Bearer {self._auth}"}

    def _payload(self, prompt: str, system: str | None):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return (f"{self.base_url}/chat/completions",
                {"model": self.model, "messages": messages,
                 "temperature": 0.7, "max_tokens": 512})

    def _extract(self, resp: dict) -> str:
        try:
            return resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"groq: unexpected response {str(resp)[:300]}") from e


class OpenAICompatProvider(GroqProvider):
    """Any OpenAI-compatible endpoint."""

    name = "openai_compat"

    def __init__(self, model: str = "default",
                 api_key: str | None = None, base_url: str | None = None):
        key = api_key or os.environ.get("OPENAI_COMPAT_API_KEY", "")
        url = base_url or os.environ.get("OPENAI_COMPAT_BASE_URL", "")
        if not url:
            raise ValueError("openai_compat: set OPENAI_COMPAT_BASE_URL")
        _RESTChatProvider.__init__(self, key, url, model)
        self._auth = key


class HFProvider(_RESTChatProvider):
    """Hugging Face Inference Providers (env HF_TOKEN)."""

    name = "hf"

    def __init__(self, model: str = "meta-llama/Llama-3.1-8B-Instruct",
                 api_key: str | None = None):
        key = api_key or os.environ.get("HF_TOKEN", "")
        super().__init__(key, "https://router.huggingface.co", model)
        self._auth = key

    def _headers(self) -> dict:
        return {"Content-Type": "application/json",
                "Authorization": f"Bearer {self._auth}"}

    def _payload(self, prompt: str, system: str | None):
        # router chat completions endpoint
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return ("https://router.huggingface.co/v1/chat/completions",
                {"model": self.model, "messages": messages,
                 "temperature": 0.7, "max_tokens": 512})

    def _extract(self, resp: dict) -> str:
        try:
            return resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"hf: unexpected response {str(resp)[:300]}") from e


PROVIDERS = {
    "mock": MockProvider,
    "phenomenon_mock": PhenomenonMockProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "openai_compat": OpenAICompatProvider,
    "hf": HFProvider,
}


def make_provider(name: str, **kwargs) -> ModelProvider:
    if name not in PROVIDERS:
        raise ValueError(f"unknown provider {name!r}; choose from {sorted(PROVIDERS)}")
    return PROVIDERS[name](**kwargs)
