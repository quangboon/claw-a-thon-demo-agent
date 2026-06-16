"""Phase 03/04 — end-to-end pipeline per profile/lang (deterministic mock LLM)."""
from app.composition import build_translation_service


def test_default_vi_auto_approved(make_profile):
    make_profile("p-vi", termbase=[{"source": "灵石", "vi": "Linh Thạch"}])
    svc = build_translation_service(profile_id="p-vi", target_lang="vi", llm_backend="mock")
    r = svc.run("灵石 +20%")
    assert r["decision"] == "auto_approved"
    assert r["target_lang"] == "vi"
    assert r["output"].rstrip().endswith("Nội dung dịch bởi AI")


def test_th_target_uses_targets_and_footer(make_profile):
    make_profile("p-th", target_langs=("vi", "th"),
                 termbase=[{"source": "金币", "vi": "Vàng", "targets": {"th": "เหรียญทอง"}}])
    svc = build_translation_service(profile_id="p-th", target_lang="th", llm_backend="mock")
    r = svc.run("金币")
    assert r["terms_required"] == [{"source": "金币", "vi": "เหรียญทอง"}]
    assert r["output"].rstrip().endswith("แปลโดย AI")  # TH footer


def test_avoid_error_blocks_auto_approve(make_profile):
    # Mock draft always contains "giả"; ban it (error) → pipeline must NOT auto-approve.
    make_profile("p-block", avoid={"vi": [{"term": "giả", "severity": "error", "category": "compliance"}]})
    svc = build_translation_service(profile_id="p-block", target_lang="vi", llm_backend="mock")
    r = svc.run("测试")
    assert r["decision"] == "send_to_human"
    assert any(i["axis"] == "need-to-avoid" for i in r["qc"]["issues"])
