"""Review channels: registry + auto-registered adapters (file queue now, Teams later)."""
from app.infrastructure.channels import file_queue  # noqa: F401  (side-effect: registration)
from app.infrastructure.channels.registry import get_channel, register_channel  # noqa: F401
