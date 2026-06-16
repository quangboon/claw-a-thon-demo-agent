"""Phase 03/04 — QC rules: term compliance (multi-lang), need-to-avoid, term confidence."""
from app.domain.entities import AvoidEntry, Term
from app.infrastructure.qc.rules.avoid_policy import AvoidPolicyRule
from app.infrastructure.qc.rules.term_compliance import TermComplianceRule
from app.infrastructure.qc.rules.term_confidence import TermConfidenceRule


def test_avoid_error_is_flagged():
    rule = AvoidPolicyRule()
    ctx = {"avoid": [AvoidEntry(term="cờ bạc", category="compliance", severity="error")]}
    issues = rule.check("源", "Đây là nội dung cờ bạc.", [], ctx)
    assert len(issues) == 1
    assert issues[0].axis == "need-to-avoid" and issues[0].severity == "error"


def test_avoid_clean_draft_passes():
    rule = AvoidPolicyRule()
    ctx = {"avoid": [AvoidEntry(term="cờ bạc", severity="error")]}
    assert rule.check("源", "Nội dung lành mạnh.", [], ctx) == []


def test_avoid_pattern_match():
    rule = AvoidPolicyRule()
    ctx = {"avoid": [AvoidEntry(term=r"\d{4}", severity="warning", is_pattern=True)]}
    assert rule.check("源", "mã 1234", [], ctx)[0].severity == "warning"


def test_term_confidence_flags_untranslated_cjk():
    issues = TermConfidenceRule().check("源", "Bản dịch còn 灵石 chưa dịch", [], {"target_lang": "vi"})
    assert issues and issues[0].axis == "term-confidence" and issues[0].severity == "warning"


def test_term_confidence_skips_zh_target():
    assert TermConfidenceRule().check("源", "灵石", [], {"target_lang": "zh"}) == []


def test_term_compliance_uses_target_lang():
    rule = TermComplianceRule()
    term = Term(source="金币", vi="Vàng", targets={"th": "เหรียญทอง"})
    # TH draft missing the TH term → issue
    assert rule.check("金币", "ไม่มีคำ", [term], {"target_lang": "th"})
    # TH draft containing the TH term → clean
    assert rule.check("金币", "ได้ เหรียญทอง", [term], {"target_lang": "th"}) == []
    # lang with no known translation → skipped (no false positive)
    assert rule.check("金币", "nothing", [term], {"target_lang": "en"}) == []
