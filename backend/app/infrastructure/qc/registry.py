"""QC rule registry — deterministic rules self-register here.

Adding a new QC check = new rule file + @register_qc_rule (no core edits → OCP).
Each rule exposes: check(source, draft, matched_terms) -> list[QcIssue].
"""
_REGISTRY: dict[str, type] = {}


def register_qc_rule(name: str):
    def deco(cls):
        _REGISTRY[name] = cls
        return cls
    return deco


def all_qc_rules() -> list:
    """Instantiate every registered deterministic QC rule."""
    return [cls() for cls in _REGISTRY.values()]


def rule_names() -> list[str]:
    return sorted(_REGISTRY)
