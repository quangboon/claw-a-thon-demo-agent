"""OpenAI-compatible LLM adapter (GreenNode MaaS). Implements the LLMProvider port."""
import logging

from openai import OpenAI

from app.infrastructure.llm.registry import register_llm

logger = logging.getLogger(__name__)


class OpenAICompatProvider:
    """Calls an OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, base_url: str, api_key: str, model: str,
                 disable_thinking: bool = True, timeout: float = 60.0):
        # timeout guards against a hung MaaS endpoint blocking the caller indefinitely.
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self._model = model
        self._disable_thinking = disable_thinking

    def chat(self, messages: list[dict], max_tokens: int = 1024, temperature: float = 0.2) -> str:
        # Disable thinking so the model returns clean `content` (Qwen would otherwise
        # put everything in `reasoning`). Endpoints that don't support it ignore it.
        extra_body = {"chat_template_kwargs": {"enable_thinking": False}} if self._disable_thinking else None
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            extra_body=extra_body,
        )
        msg = resp.choices[0].message
        content = (msg.content or "").strip()
        if not content:
            # Thinking-mode models (e.g. qwen3-5-27b) sometimes emit text in `reasoning`.
            reasoning = getattr(msg, "reasoning", None)
            if reasoning:
                logger.warning("LLM returned empty content; falling back to `reasoning` field")
                content = reasoning.strip()
        if not content:
            # Don't return "" silently — that would masquerade as a valid translation downstream.
            raise RuntimeError(
                f"LLM returned empty response (model={self._model}, "
                f"finish_reason={resp.choices[0].finish_reason})"
            )
        return content


@register_llm("openai-compat")
def _build(settings):
    return OpenAICompatProvider(
        settings.llm_base_url, settings.llm_api_key, settings.llm_model,
        disable_thinking=settings.llm_disable_thinking,
    )
