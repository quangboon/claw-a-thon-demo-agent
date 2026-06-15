"""Import rules so they self-register in the QC registry on package import."""
from app.infrastructure.qc.rules import completeness, term_compliance  # noqa: F401
