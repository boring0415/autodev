import httpx
from autodev.providers.openai_compatible import OpenAICompatibleProvider


def test_openai_compatible_provider_with_mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer secret"
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleProvider("https://example.test/v1", "secret", "mock", client=client)
    assert provider.generate([{"role": "user", "content": "hi"}]) == "ok"
