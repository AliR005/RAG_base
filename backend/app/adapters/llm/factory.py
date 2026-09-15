"""LLMProviderFactory + реестр моделей (models.yaml)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from app.adapters.llm.anthropic_provider import AnthropicProvider
from app.adapters.llm.ollama_provider import OllamaProvider
from app.adapters.llm.openrouter_provider import OpenRouterProvider
from app.ports.llm_provider import LLMProvider

REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "models.yaml"
)


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    model: str
    context_window: int


def load_registry(
    path: str | Path = REGISTRY_PATH, llm_model: str | None = None
) -> list[ModelInfo]:
    """Читать models.yaml. ${LLM_MODEL} подставляется из Settings
    (читает .env через pydantic), а не только из os.environ."""
    if llm_model is None:
        try:
            from app.core.config import settings

            llm_model = settings.LLM_MODEL
        except Exception:
            llm_model = os.environ.get("LLM_MODEL", "")
    raw = Path(path).read_text(encoding="utf-8")
    template = raw.replace("${LLM_MODEL}", llm_model or "")
    template = os.path.expandvars(template)
    data = yaml.safe_load(template) or {}
    return [ModelInfo(**item) for item in data.get("models", [])]


class LLMProviderFactory:
    """Выбор реализации LLMProvider по имени провайдера."""

    def __init__(
        self,
        providers: dict[str, LLMProvider] | None = None,
        openrouter_key: str = "",
        anthropic_key: str = "",
        ollama_model: str = "",
    ):
        self._providers = providers or {
            "openrouter": OpenRouterProvider(api_key=openrouter_key),
            "anthropic": AnthropicProvider(api_key=anthropic_key),
            "ollama": OllamaProvider(default_model=ollama_model),
        }

    def get(self, provider: str) -> LLMProvider:
        try:
            return self._providers[provider]
        except KeyError:
            raise ValueError(
                f"Unknown LLM provider: {provider!r}. "
                f"Available: {sorted(self._providers)}"
            ) from None

    def resolve(self, model_id: str) -> tuple[LLMProvider, ModelInfo]:
        """model-id из реестра -> (провайдер, ModelInfo)."""
        for info in load_registry():
            if info.id == model_id:
                return self.get(info.provider), info
        raise ValueError(f"Unknown model id: {model_id!r}")
