"""Import adapters so they self-register in the registry on package import."""
from app.infrastructure.llm import openai_compat, mock  # noqa: F401  (side-effect: registration)
from app.infrastructure.llm.registry import (  # noqa: F401
    register_llm,
    get_llm_provider,
    available_backends,
)
