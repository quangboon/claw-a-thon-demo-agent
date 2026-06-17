# Submission — Claw-a-thon 2026

> File gom sẵn nội dung để copy-paste vào form dự thi. Mục **[CẦN ĐIỀN]** là phần bạn tự bổ sung (video, team).

---

## Thông tin nhanh (copy từng trường)

| Trường | Giá trị |
|--------|---------|
| **Tên dự án** | Multi-Tenant Translate + QC Agent (ZH → VI/TH) |
| **Track** | Agentic Assistant |
| **Live demo (API + UI)** | https://endpoint-46484a3a-dbe3-48be-8d2f-e1388456bde8.agentbase-runtime.aiplatform.vngcloud.vn |
| **Health check** | `GET /health` → `{"status":"ok"}` |
| **GitHub repo** | https://github.com/quangboon/claw-a-thon-demo-agent |
| **Nền tảng** | GreenNode AgentBase (Custom Agent, PUBLIC, cổng 8080) |
| **Đăng nhập demo** | user: `admin` · pass: `ClawAThon@2026` |
| **Video demo** | [CẦN ĐIỀN] — link public, đúng track Agentic Assistant |
| **Team / Thành viên** | [CẦN ĐIỀN] |

---

## Mô tả use case — bản ngắn (≤300 ký tự, cho form rút gọn)

Agent dịch nội dung game tiếng Trung sang Việt/Thái bám termbase để giữ nhất quán thuật ngữ, có QC độc lập 3 trục (đầy đủ · tuân thủ thuật ngữ · trôi chảy), tự sửa 1 vòng, đẩy người duyệt khi chưa đạt, và học từ correction (flywheel). Đa team qua Profile, dữ liệu cô lập.

---

## Mô tả use case — bản đầy đủ (~150 từ)

Đội bản địa hoá game thường mất nhiều công để giữ **nhất quán thuật ngữ** khi dịch nội dung tiếng Trung (vật phẩm, kỹ năng, cảnh giới tu luyện…) sang tiếng Việt — chỗ mà Google Translate và dịch tay hay sai. Agent này giải quyết bằng quy trình: quét **termbase** để tìm thuật ngữ bắt buộc → **Translator** dịch và ép dùng đúng glossary → **QC Reviewer độc lập** rà 3 trục (đầy đủ, tuân thủ thuật ngữ, trôi chảy) → nếu chưa đạt thì **tự dịch lại 1 vòng** với feedback, vẫn chưa đạt thì **đẩy người duyệt**. Mỗi lần người sửa, cặp *sai → đúng* được ghi lại (**flywheel**) và một **Term Curator** đề xuất bổ sung termbase — càng dùng càng chuẩn. Người dùng là **biên dịch viên & reviewer** của đội game; giá trị: nhanh hơn, nhất quán thuật ngữ, có kiểm soát chất lượng và vết người duyệt. Mọi bản dịch tự gắn nhãn *"Nội dung dịch bởi AI"*.

---

## Mô tả ngắn về Agent (Tiếng Việt) — cho form (4 ý)

**(1) Vấn đề:** Đội bản địa hoá game tốn nhiều công để giữ **nhất quán thuật ngữ** khi dịch nội dung tiếng Trung (vật phẩm, kỹ năng, cảnh giới tu luyện…) sang tiếng Việt/Thái — nơi Google Translate và dịch tay hay sai và thiếu kiểm soát chất lượng.
**(2) Người dùng:** Biên dịch viên và reviewer (người duyệt) của các đội phát hành game.
**(3) Cách agent giải quyết:** Agent quét **termbase** tìm thuật ngữ bắt buộc → **Translator** dịch và ép dùng đúng glossary → **QC độc lập** rà nhiều trục (đầy đủ, tuân thủ thuật ngữ, trôi chảy, từ cần tránh, định dạng) → chưa đạt thì **tự dịch lại 1 vòng**, vẫn chưa đạt thì **đẩy người duyệt**. Mỗi lần người sửa, cặp *sai→đúng* được lưu (**flywheel**) và đưa ngược vào lần dịch sau, nên càng dùng càng chuẩn. Đa team qua **Profile**, dữ liệu cô lập.
**(4) Giá trị:** Dịch nhanh hơn, nhất quán thuật ngữ, có kiểm soát chất lượng và vết người duyệt; công sửa thủ công giảm dần theo thời gian. Mọi bản dịch gắn nhãn "Nội dung dịch bởi AI".

---

## Mô tả ngắn về Agent (Tiếng Anh) — cho form (4 ý)

**(1) Problem:** Game localization teams spend heavy effort keeping **terminology consistent** when translating Chinese game content (items, skills, cultivation realms…) into Vietnamese/Thai — exactly where Google Translate and manual translation get terms wrong and lack quality control.
**(2) Users:** Translators and reviewers (approvers) on game publishing teams.
**(3) How the agent solves it:** It scans a **termbase** for required terms → a **Translator** translates while enforcing the glossary → an **independent QC** checks multiple axes (completeness, term compliance, fluency, need-to-avoid, format) → if it fails, the agent **self-corrects once**; if still failing, it routes to a **human reviewer**. Each human fix is saved as a *wrong→right* **correction (flywheel)** and fed back into future translations, so quality improves with use. Multi-team via isolated **Profiles**.
**(4) Value:** Faster translation, consistent terminology, built-in quality control with a human audit trail, and steadily less manual rework over time. Every output is labeled "Translated by AI".

---

## Luồng hoạt động (nếu form hỏi "how it works")

```
Nguồn ZH → khớp termbase → Translator (+glossary +corrections) → QC 3 trục
  → pass: auto_approved
  → fail: tự sửa 1 vòng → vẫn fail: đẩy Review Queue (người duyệt)
       → Reject + sửa: lưu correction (flywheel) → Curator đề xuất term mới
```

4 vai LLM: **Term Extractor** (dựng termbase offline) · **Translator** · **QC Reviewer** (chấm trôi chảy) · **Term Curator** (học từ corrections). Trục QC #1 (đầy đủ) và #2 (tuân thủ thuật ngữ) là kiểm tra **tất định**; chỉ trục #3 (trôi chảy) gọi LLM.

---

## Tech stack

- **Backend:** Python + FastAPI, kiến trúc Ports & Adapters (hexagonal-lite) — đổi LLM provider / storage / kênh duyệt không sửa business logic.
- **Frontend:** React + Vite + Tailwind + shadcn-style + TanStack Query (6 màn: Playground · Termbase · Review Queue · Corrections · Dashboard · Profile Admin).
- **LLM:** GreenNode MaaS (OpenAI-compatible).
- **Đóng gói:** Dockerfile multi-stage → 1 container serve API + UI cổng 8080.
- **Multi-tenant:** mọi request scoped theo header `X-Profile-Id`; `profiles/<id>/` cô lập termbase/corrections/review-queue per team. Seed: `default`, `game-a`, `game-b`, `qa-demo`.

---

## Cách BTC kiểm tra nhanh (nếu cần)

```bash
# 1) Health (public, không cần auth)
curl https://endpoint-46484a3a-dbe3-48be-8d2f-e1388456bde8.agentbase-runtime.aiplatform.vngcloud.vn/health

# 2) Lấy token
curl -X POST .../auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"ClawAThon@2026"}'

# 3) Dịch (gắn Bearer token ở header Authorization)
curl -X POST .../translate -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"source":"灵石 +20%，开放传送阵。","target_lang":"vi"}'
```

Hoặc mở UI → đăng nhập `admin` / `ClawAThon@2026` → màn **Playground** → dán câu ZH → **Dịch + QC**.

---

## Checklist 3 điều kiện PASS

- [x] Agent chạy trên AgentBase, endpoint public, `/health` 200, gọi được `/translate`.
- [x] Repo GitHub public + README có mô tả use case.
- [ ] Video demo 2–3' (public, đúng track) — **[CẦN ĐIỀN]**
