"""Shared pytest fixtures — isolate every test run from real profile/legacy files.

`isolated_profiles` points settings at a temp profiles dir and a temp default profile,
clears the API dependency lru_caches, and restores everything afterwards. Tests never
touch backend/termbase.json or the real profiles/ tree.
"""
import json
from pathlib import Path

import pytest

from app.settings import settings


def _write_profile(root: Path, pid: str, *, name="", target_langs=("vi",),
                   termbase=None, tone=None, avoid=None):
    pdir = root / pid
    (pdir).mkdir(parents=True, exist_ok=True)
    (pdir / "profile.json").write_text(json.dumps({
        "id": pid, "name": name or pid, "source_lang": "zh", "target_langs": list(target_langs),
    }, ensure_ascii=False), encoding="utf-8")
    if termbase is not None:
        (pdir / "termbase.json").write_text(json.dumps(termbase, ensure_ascii=False), encoding="utf-8")
    for lang, text in (tone or {}).items():
        (pdir / "tone").mkdir(exist_ok=True)
        (pdir / "tone" / f"{lang}.md").write_text(text, encoding="utf-8")
    for lang, entries in (avoid or {}).items():
        (pdir / "avoid").mkdir(exist_ok=True)
        (pdir / "avoid" / f"{lang}.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    return pdir


@pytest.fixture
def isolated_profiles(tmp_path, monkeypatch):
    """Redirect profiles_dir + legacy default paths into tmp_path; clear caches."""
    import app.infrastructure.profile_paths as pp
    from app.api import dependencies as deps

    monkeypatch.setattr(settings, "profiles_dir", str(tmp_path / "profiles"))
    # Default profile's legacy tenant-data paths → tmp (so default writes don't hit repo files).
    monkeypatch.setattr(pp, "LEGACY_TERMBASE", str(tmp_path / "legacy_termbase.json"))
    monkeypatch.setattr(pp, "LEGACY_CORRECTIONS", str(tmp_path / "legacy_corrections.jsonl"))
    monkeypatch.setattr(pp, "LEGACY_QUEUE", str(tmp_path / "legacy_queue.jsonl"))

    for fn in (deps.get_profiles, deps.termbase_for, deps.corrections_for,
               deps.queue_for, deps.translation_service_for, deps.review_service_for, deps._llm):
        fn.cache_clear()
    yield tmp_path
    for fn in (deps.get_profiles, deps.termbase_for, deps.corrections_for,
               deps.queue_for, deps.translation_service_for, deps.review_service_for, deps._llm):
        fn.cache_clear()


@pytest.fixture
def make_profile(isolated_profiles):
    """Factory to seed a profile under the isolated profiles dir."""
    root = isolated_profiles / "profiles"

    def _make(pid, **kw):
        return _write_profile(root, pid, **kw)

    return _make
