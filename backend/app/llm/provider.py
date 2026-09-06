from typing import Protocol
import os

import httpx

from app.core.config import Settings
from app.core.exceptions import LLMConfigurationError, LLMProviderError


class LLMProvider(Protocol):
    def generate_markdown(self, prompt: str) -> str: ...


class OpenAICompatibleProvider:
    """Minimal OpenAI-compatible chat-completions client kept on the server only."""

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate_markdown(self, prompt: str) -> str:
        try:
            with httpx.Client(timeout=httpx.Timeout(45.0, connect=10.0)) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "temperature": 0.2,
                        "messages": [
                            {"role": "system", "content": "你是严谨的 A 股投研助理。只根据给定资料总结，明确数据限制，不提供交易指令。"},
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as error:
            raise LLMProviderError(f"模型请求失败：{error}") from error
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise LLMProviderError("模型响应不包含可用文本。") from error
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("模型返回了空内容。")
        return content.strip()


def build_llm_provider(settings: Settings) -> LLMProvider:
    api_key = settings.llm_api_key or os.getenv(settings.llm_api_key_env)
    if settings.llm_provider != "openai_compatible" or not api_key:
        raise LLMConfigurationError(
            "请在项目根目录 .env 中配置 LLM_PROVIDER=openai_compatible、"
            f"LLM_API_KEY（或环境变量 {settings.llm_api_key_env}）、LLM_BASE_URL 与 LLM_MODEL。"
        )
    return OpenAICompatibleProvider(api_key=api_key, base_url=settings.llm_base_url, model=settings.llm_model)
