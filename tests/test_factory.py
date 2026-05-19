"""Tests for top-level inference() / async_inference() factory helpers."""

from inferencesh import AsyncInference, Inference, async_inference, inference


def test_inference_factory_returns_inference_client():
    client = inference(api_key="test-key", base_url="https://api.example.com")
    assert isinstance(client, Inference)
    assert client._api_key == "test-key"
    assert client._base_url == "https://api.example.com"


def test_async_inference_factory_returns_async_client():
    client = async_inference(api_key="async-key")
    assert isinstance(client, AsyncInference)
    assert client._api_key == "async-key"
