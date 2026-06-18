import pytest
from pydantic import BaseModel
import agents.base as base
from agents.base import call_structured, AgentError


class Toy(BaseModel):
    value: int


def test_returns_parsed_model(monkeypatch):
    monkeypatch.setattr(base, "call_llm", lambda *a, **k: '{"value": 7}')
    out = call_structured([{"role": "user", "content": "x"}], Toy)
    assert out.value == 7


def test_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake(*a, **k):
        calls["n"] += 1
        return "not json" if calls["n"] == 1 else '{"value": 3}'

    monkeypatch.setattr(base, "call_llm", fake)
    out = call_structured([{"role": "user", "content": "x"}], Toy, max_retries=2)
    assert out.value == 3
    assert calls["n"] == 2  # one bad, one good


def test_raises_agenterror_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr(base, "call_llm", lambda *a, **k: "still not json")
    with pytest.raises(AgentError):
        call_structured([{"role": "user", "content": "x"}], Toy, max_retries=1)
