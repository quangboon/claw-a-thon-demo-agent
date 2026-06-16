"""App configuration.

Priority: OS environment variables > .env (project root) > defaults.
No secrets are hardcoded here — LLM_API_KEY must come from env/.env.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Read .env from the current working directory (run from project root).
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Which LLM adapter to use (registry key). See infrastructure/llm/registry.py
    llm_backend: str = "openai-compat"

    # OpenAI-compatible endpoint (GreenNode MaaS by default).
    llm_base_url: str = "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1"
    llm_api_key: str = ""
    # Model identifier must use the endpoint's `path` form (e.g. "qwen/qwen3-5-27b"), not the short code.
    llm_model: str = "qwen/qwen3-5-27b"
    # Thinking-mode models (Qwen) emit text only in `reasoning` unless thinking is disabled.
    # Sending chat_template_kwargs.enable_thinking=false yields clean `content`.
    llm_disable_thinking: bool = True

    # Multi-tenant profiles (Domain Packs). Definitions live under profiles/<id>/.
    profiles_dir: str = "profiles"
    # Profile used when a request carries no X-Profile-Id — maps to legacy v1 paths.
    default_profile_id: str = "default"


settings = Settings()
