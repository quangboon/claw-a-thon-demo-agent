"""QC infrastructure: registry + auto-registered deterministic rules."""
from app.infrastructure.qc import rules  # noqa: F401  (side-effect: registers rules)
from app.infrastructure.qc.registry import all_qc_rules, register_qc_rule, rule_names  # noqa: F401
