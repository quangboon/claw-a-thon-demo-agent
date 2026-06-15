"""Review channel registry — adapters self-register by name (OCP).

Add a new channel (e.g. MS Teams) = new file + @register_channel (no core edits).
"""
from typing import Callable

_BUILDERS: dict[str, Callable[..., object]] = {}


def register_channel(name: str):
    def deco(builder: Callable[..., object]):
        _BUILDERS[name] = builder
        return builder
    return deco


def get_channel(name: str, settings=None):
    if name not in _BUILDERS:
        raise KeyError(f"Unknown review channel '{name}'. Available: {sorted(_BUILDERS)}")
    return _BUILDERS[name](settings)
