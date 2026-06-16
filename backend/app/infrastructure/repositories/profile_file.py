"""File-backed profile repository. Implements the ProfileRepository port.

Layout (per profile):
    profiles/<id>/profile.json          # {id, name, source_lang, target_langs, ...}
    profiles/<id>/tone/<lang>.md        # tone guide (plain markdown)
    profiles/<id>/avoid/<lang>.json     # [{term, category, severity, is_pattern}]
    profiles/<id>/examples/<lang>.json  # [{source, good, bad, lang}]

Missing files degrade gracefully (empty tone / [] avoid / [] examples) so a profile
never crashes the pipeline. The default profile is synthesised if its profile.json is
absent, keeping v1 working with zero seed files.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from app.domain.entities import AvoidEntry, Example, Profile
from app.infrastructure.profile_paths import profile_paths
from app.settings import settings


class FileProfileRepository:
    def __init__(self, profiles_dir: Optional[str] = None, default_profile_id: Optional[str] = None):
        self._dir = Path(profiles_dir or settings.profiles_dir)
        self._default_id = default_profile_id or settings.default_profile_id
        self._cache: dict[str, Profile] = {}

    # --- profile definition ---
    def get(self, profile_id: str) -> Optional[Profile]:
        if profile_id in self._cache:
            return self._cache[profile_id]
        path = profile_paths(profile_id).profile_json
        if not path.exists():
            # Synthesise the default profile so v1 runs without any seed file.
            if profile_id == self._default_id:
                prof = Profile(id=self._default_id, name="Default", target_langs=["vi"])
                self._cache[profile_id] = prof
                return prof
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        prof = Profile(
            id=data.get("id", profile_id),
            name=data.get("name", profile_id),
            source_lang=data.get("source_lang", "zh"),
            target_langs=data.get("target_langs", ["vi"]),
            char_name_convention=data.get("char_name_convention", ""),
            format_enabled=data.get("format_enabled", True),
            format_extra_tokens=data.get("format_extra_tokens", []),
        )
        self._cache[profile_id] = prof
        return prof

    def exists(self, profile_id: str) -> bool:
        return self.get(profile_id) is not None

    def list(self) -> list[Profile]:
        ids = set()
        if self._dir.exists():
            ids = {p.name for p in self._dir.iterdir() if (p / "profile.json").exists()}
        ids.add(self._default_id)  # always advertise the default profile
        return [p for p in (self.get(i) for i in sorted(ids)) if p]

    def upsert(self, profile: Profile) -> None:
        path = profile_paths(profile.id).profile_json
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(profile), ensure_ascii=False, indent=2), encoding="utf-8")
        self._cache[profile.id] = profile

    # --- per-language assets (lazy, graceful on missing files) ---
    def tone(self, profile_id: str, lang: str) -> str:
        path = profile_paths(profile_id).tone(lang)
        return path.read_text(encoding="utf-8").strip() if path.exists() else ""

    def avoid(self, profile_id: str, lang: str) -> list[AvoidEntry]:
        path = profile_paths(profile_id).avoid(lang)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [AvoidEntry(
            term=item.get("term", ""),
            category=item.get("category", ""),
            severity=item.get("severity", "warning"),
            is_pattern=item.get("is_pattern", False),
        ) for item in data if item.get("term")]

    def examples(self, profile_id: str, lang: str) -> list[Example]:
        path = profile_paths(profile_id).examples(lang)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [Example(
            source=item.get("source", ""),
            good=item.get("good", ""),
            bad=item.get("bad", ""),
            lang=item.get("lang", lang),
        ) for item in data if item.get("source")]

    # --- setters (used by the profile admin API) ---
    def set_tone(self, profile_id: str, lang: str, text: str) -> None:
        path = profile_paths(profile_id).tone(lang)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def set_avoid(self, profile_id: str, lang: str, entries: list[AvoidEntry]) -> None:
        path = profile_paths(profile_id).avoid(lang)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(e) for e in entries]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
