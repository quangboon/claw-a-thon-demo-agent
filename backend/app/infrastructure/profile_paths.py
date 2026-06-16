"""Per-profile path resolution — the multi-tenant namespacing rule in one place.

Every tenant gets its own `profiles/<id>/…` namespace so teams never share termbase,
corrections or review-queue. The DEFAULT profile keeps the legacy v1 paths
(`backend/termbase.json`, …) so requests without an X-Profile-Id behave exactly as
before (backward compatibility). Definition assets (profile.json, tone/avoid/examples)
always live under `profiles/<id>/`, even for the default profile.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.settings import settings

# Legacy v1 tenant-data locations (used only by the default profile).
LEGACY_TERMBASE = "backend/termbase.json"
LEGACY_CORRECTIONS = "backend/corrections.jsonl"
LEGACY_QUEUE = "backend/review_queue.jsonl"
LEGACY_CANDIDATES = "backend/data/termbase.candidates.json"

# A profile_id becomes a directory name and is attacker-controlled (header/URL path),
# so it MUST NOT contain path separators or traversal — else a tenant could read/write
# another tenant's namespace (or escape `profiles/` entirely).
_VALID_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def is_valid_profile_id(profile_id: str) -> bool:
    return bool(profile_id) and profile_id not in (".", "..") and _VALID_ID.match(profile_id) is not None


@dataclass
class ProfilePaths:
    """Resolved filesystem locations for a single profile."""
    root: Path          # profiles/<id>/
    profile_json: Path  # profiles/<id>/profile.json
    termbase: Path      # tenant termbase (legacy for default)
    corrections: Path   # tenant correction flywheel (legacy for default)
    queue: Path         # tenant review queue (legacy for default)
    candidates: Path    # tenant term candidates (legacy for default)

    def tone(self, lang: str) -> Path:
        return self.root / "tone" / f"{lang}.md"

    def avoid(self, lang: str) -> Path:
        return self.root / "avoid" / f"{lang}.json"

    def examples(self, lang: str) -> Path:
        return self.root / "examples" / f"{lang}.json"


def profile_paths(profile_id: str) -> ProfilePaths:
    """Namespaced paths for `profile_id`; the default profile keeps legacy v1 paths.

    Raises ValueError on an unsafe id (path traversal / separators) — callers at the
    HTTP edge convert this to 400.
    """
    if not is_valid_profile_id(profile_id):
        raise ValueError(f"invalid profile_id: {profile_id!r}")
    root = Path(settings.profiles_dir) / profile_id
    if profile_id == settings.default_profile_id:
        termbase, corrections, queue, candidates = (
            LEGACY_TERMBASE, LEGACY_CORRECTIONS, LEGACY_QUEUE, LEGACY_CANDIDATES,
        )
    else:
        termbase = str(root / "termbase.json")
        corrections = str(root / "corrections.jsonl")
        queue = str(root / "review_queue.jsonl")
        candidates = str(root / "termbase.candidates.json")
    return ProfilePaths(
        root=root,
        profile_json=root / "profile.json",
        termbase=Path(termbase),
        corrections=Path(corrections),
        queue=Path(queue),
        candidates=Path(candidates),
    )
