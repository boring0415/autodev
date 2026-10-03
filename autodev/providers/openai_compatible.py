import httpx
from .base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, base_url: str, api_key: str, model: str, client: httpx.Client | None = None):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model
        self.client = client or httpx.Client(timeout=60)

    def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        response = self.client.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": self.model, "messages": messages, **kwargs})
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
