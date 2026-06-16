"""Phase 01/02 — profile loading, graceful fallback, and multi-tenant isolation."""
from app.infrastructure.profile_paths import profile_paths
from app.infrastructure.repositories.correction_file import FileCorrectionStore
from app.infrastructure.repositories.profile_file import FileProfileRepository
from app.infrastructure.repositories.termbase_file import FileTermbaseRepository


def test_load_profile_and_assets(make_profile):
    make_profile("team-x", name="Team X", target_langs=("vi", "th"),
                 tone={"vi": "Tone VI"}, avoid={"th": [{"term": "X", "severity": "error"}]})
    repo = FileProfileRepository()
    prof = repo.get("team-x")
    assert prof and prof.name == "Team X" and prof.target_langs == ["vi", "th"]
    assert repo.tone("team-x", "vi") == "Tone VI"
    assert repo.avoid("team-x", "th")[0].severity == "error"
    # Missing language degrades gracefully (no crash).
    assert repo.tone("team-x", "en") == ""
    assert repo.avoid("team-x", "en") == []


def test_default_profile_synthesised(isolated_profiles):
    repo = FileProfileRepository()
    prof = repo.get("default")  # no seed file
    assert prof and prof.id == "default" and prof.target_langs == ["vi"]
    assert repo.get("does-not-exist") is None


def test_termbase_isolation(make_profile):
    make_profile("a", termbase=[{"source": "灵石", "vi": "Linh Thạch"}])
    make_profile("b", termbase=[{"source": "金币", "vi": "Vàng"}])
    a = FileTermbaseRepository(str(profile_paths("a").termbase))
    b = FileTermbaseRepository(str(profile_paths("b").termbase))
    assert [t.source for t in a.match_in("灵石")] == ["灵石"]
    assert b.match_in("灵石") == []  # A's term never leaks into B
    assert [t.source for t in b.match_in("金币")] == ["金币"]


def test_corrections_isolation(make_profile):
    make_profile("a")
    make_profile("b")
    ca = FileCorrectionStore(str(profile_paths("a").corrections))
    cb = FileCorrectionStore(str(profile_paths("b").corrections))
    ca.save("源", "wrong", "right", note="t")
    assert len(ca.all()) == 1
    assert cb.all() == []  # B's flywheel stays empty — full isolation
