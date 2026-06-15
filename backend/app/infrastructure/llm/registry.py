"""LLM provider registry.

Adapters self-register a builder under a name. Adding a new provider means
adding a file + `@register_llm("name")` — no edits to the core (Open/Closed).
"""
from typing import Callable

from app.domain.ports import LLMProvider

# name -> builder(settings) -> LLMProvider
_BUILDERS: dict[str, Callable[..., LLMProvider]] = {}


def register_llm(name: str):
    def deco(builder: Callable[..., LLMProvider]):
        _BUILDERS[name] = builder
        return builder
    return deco


def get_llm_provider(name: str, settings=None) -> LLMProvider:
    if name not in _BUILDERS:
        raise KeyError(f"Unknown LLM backend '{name}'. Available: {sorted(_BUILDERS)}")
    if settings is None:
        # Default to the app settings singleton so callers can do get_llm_provider(name).
        from app.settings import settings as settings  # local import: settings is leaf, no cycle
    return _BUILDERS[name](settings)


def available_backends() -> list[str]:
    return sorted(_BUILDERS)
