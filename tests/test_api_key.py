"""api_key falls back to INFERENCE_API_KEY on every client constructor."""

import pytest

from inferencesh import AsyncInference, Inference, async_inference, inference

CONSTRUCTORS = [Inference, AsyncInference, inference, async_inference]


@pytest.mark.parametrize("make", CONSTRUCTORS)
def test_reads_env_when_api_key_omitted(make, monkeypatch):
    monkeypatch.setenv("INFERENCE_API_KEY", "env-key")
    client = make()
    assert client._api_key == "env-key"
    assert client._headers()["Authorization"] == "Bearer env-key"


@pytest.mark.parametrize("make", CONSTRUCTORS)
def test_explicit_api_key_wins_over_env(make, monkeypatch):
    monkeypatch.setenv("INFERENCE_API_KEY", "env-key")
    assert make(api_key="arg-key")._api_key == "arg-key"


@pytest.mark.parametrize("make", CONSTRUCTORS)
def test_explicit_none_api_key_falls_back_to_env(make, monkeypatch):
    monkeypatch.setenv("INFERENCE_API_KEY", "env-key")
    assert make(api_key=None)._api_key == "env-key"


@pytest.mark.parametrize("make", CONSTRUCTORS)
@pytest.mark.parametrize("env", [None, ""])
def test_missing_key_names_the_env_var(make, env, monkeypatch):
    if env is None:
        monkeypatch.delenv("INFERENCE_API_KEY", raising=False)
    else:
        monkeypatch.setenv("INFERENCE_API_KEY", env)
    with pytest.raises(ValueError, match="INFERENCE_API_KEY"):
        make()


def test_base_url_still_passes_through_factory(monkeypatch):
    monkeypatch.setenv("INFERENCE_API_KEY", "env-key")
    assert inference(base_url="http://localhost:3021")._base_url == "http://localhost:3021"
