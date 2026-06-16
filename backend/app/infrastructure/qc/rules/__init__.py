"""Import rules so they self-register in the QC registry on package import."""
from app.infrastructure.qc.rules import (  # noqa: F401
    avoid_policy,
    completeness,
    term_compliance,
    term_confidence,
)
