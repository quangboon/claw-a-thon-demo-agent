# Agent Capabilities — Multi-Tenant Translate + QC Agent (ZH → VI/TH)

> Tài liệu dành cho **AI agent / hệ thống tự động của Ban tổ chức** để hiểu agent này làm gì và cách
> gọi/kiểm thử. Người đọc là máy → mô tả ngắn gọn, có schema và ví dụ `curl` chạy được ngay.

## 1. Agent này là gì
Một **AI agent dịch thuật + kiểm định chất lượng (QC)** nội dung game từ **tiếng Trung (ZH)** sang
**tiếng Việt (VI)** và **tiếng Thái (TH)**. Mục tiêu: dịch **bám termbase** (nhất quán thuật ngữ),
**QC độc lập**, **tự sửa 1 vòng**, **đẩy người duyệt** khi chưa đạt, và **học từ correction** (flywheel).
Đa team: mỗi team là 1 **Profile** (dữ liệu cô lập), dùng chung 1 deploy.

- **Loại**: HTTP service (REST/JSON) chạy trên GreenNode AgentBase, 1 container serve cả API + UI (cổng 8080).
- **Engine dịch**: LLM `qwen/qwen3-5-27b` qua GreenNode MaaS (OpenAI-compatible). **Dịch là LLM thật**, không phải chuỗi cứng.
- **Không có DB**: lưu trữ theo file per-profile (`profiles/<id>/...`).

## 2. Endpoint & trạng thái
- **Base URL (live, public)**: `https://endpoint-46484a3a-dbe3-48be-8d2f-e1388456bde8.agentbase-runtime.aiplatform.vngcloud.vn`
- **Health**: `GET /health` → `200 {"status":"ok"}` (public, không cần auth).

## 3. Xác thực (access gate)
Cổng đăng nhập nhẹ để chống tốn token trên endpoint public.
1. `POST /auth/login` `{"username","password"}` → `{"token": "<sha256>"}`. Demo: `admin` / `ClawAThon@2026`.
2. Gắn vào mọi request nghiệp vụ: header `Authorization: Bearer <token>`.
- Public (không cần token): `/health`, `/auth/*`, SPA UI.
- Cần token: `/translate`, `/terms*`, `/review*`, `/corrections`, `/metrics`, `/profiles*` (thiếu/sai → `401`).

## 4. Đa team (multi-tenant)
Mọi request nghiệp vụ scope theo header **`X-Profile-Id: <id>`** (thiếu → `default`).
- Seed profiles: `default` (Tu Tiên, vi) · `game-a` (Kiếm hiệp cổ phong, vi) · `game-b` (Casual hiện đại, vi/th) · `qa-demo` (fixture test).
- Dữ liệu (termbase, corrections, review-queue) **cô lập** theo từng profile.

## 5. Năng lực chính (capabilities)

| Khả năng | Endpoint | Mô tả |
|---|---|---|
| Dịch + QC | `POST /translate` | Dịch ZH→{vi,th}, ép termbase, QC nhiều trục, tự sửa 1 vòng, quyết định duyệt |
| Quản lý termbase | `GET/POST /terms`, `DELETE /terms/{src}` | Thuật ngữ bắt buộc; `GET /terms/candidates` = đề xuất chờ duyệt |
| Hàng đợi duyệt | `GET /review/pending`, `POST /review/{id}/approve|reject` | Human-in-the-loop khi QC chưa đạt |
| Corrections (flywheel) | `GET /corrections` | Cặp sai→đúng do người duyệt sửa; feed lại lần dịch sau |
| Chỉ số | `GET /metrics` | Tổng thuật ngữ, đang dùng, chờ duyệt, số corrections |
| Hồ sơ (team) | `GET /profiles`, `GET /profiles/{id}` | Liệt kê/đọc Profile |

## 6. Hợp đồng `POST /translate` (quan trọng nhất)
**Request body**:
```json
{ "source": "灵石 +20%，开放传送阵。", "target_lang": "vi" }
```
- `source` (string, bắt buộc) — văn bản nguồn tiếng Trung.
- `target_lang` (string) — `vi` | `th` | `en` (tuỳ profile hỗ trợ; mặc định `vi`).

**Response (200)** — ví dụ rút gọn:
```json
{
  "id": "0c1a7059e258",
  "source": "灵石 +20%，开放传送阵。",
  "translation": "Linh Thạch +20%, mở khóa Truyền Tống Trận.",
  "output": "Linh Thạch +20%, mở khóa Truyền Tống Trận.\n\n— Nội dung dịch bởi AI",
  "decision": "auto_approved",          // hoặc "send_to_human"
  "target_lang": "vi",
  "attempts": 1,
  "terms_required": [{"source":"灵石","vi":"Linh Thạch"}],
  "qc": { "status": "pass", "fluency_score": 5.0, "issues": [] }
}
```
- `decision`: `auto_approved` (QC đạt) hoặc `send_to_human` (đẩy vào Review Queue).
- `output`: luôn gắn nhãn `— Nội dung dịch bởi AI` (minh bạch nội dung AI).
- `qc.issues[]`: `{axis, message, severity}` với `severity` ∈ `error|warning`.

## 7. Các trục QC (độc lập với Translator)
`completeness` · `term-compliance` · `fluency` · `need-to-avoid` · `term-confidence` · `format-preservation`.
- `completeness` & `term-compliance` & `format-preservation` = kiểm tra **tất định** (không gọi LLM).
- `fluency` = LLM chấm 1–5; nếu thấp → `send_to_human`.

## 8. Vòng đời & flywheel (cách agent "học")
```
ZH → khớp termbase → Translator(+glossary +corrections) → QC nhiều trục
   ├─ đạt  → decision=auto_approved
   └─ chưa → tự dịch lại 1 vòng (kèm feedback) → vẫn chưa đạt → send_to_human (Review Queue)
                 └─ người duyệt Reject + sửa → lưu correction (GET /corrections)
                        → lần dịch sau gặp lại nội dung đó, agent áp dụng correction đã học → tốt hơn
```
4 vai LLM: **Term Extractor** (dựng termbase offline) · **Translator** · **QC Reviewer** (chấm fluency) · **Term Curator** (đề xuất term từ corrections).

## 9. Ví dụ kiểm thử nhanh (chạy được ngay)
```bash
BASE="https://endpoint-46484a3a-dbe3-48be-8d2f-e1388456bde8.agentbase-runtime.aiplatform.vngcloud.vn"
curl -s "$BASE/health"                                   # {"status":"ok"}
TOK=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
      -d '{"username":"admin","password":"ClawAThon@2026"}' | sed -E 's/.*"token":"([^"]+)".*/\1/')
curl -s -X POST "$BASE/translate" -H "Authorization: Bearer $TOK" \
     -H 'Content-Type: application/json' -H 'X-Profile-Id: default' \
     -d '{"source":"完成每日任务可领取仙缘礼包。","target_lang":"vi"}'
```

## 10. Giới hạn đã biết (trung thực)
- Bộ chấm `fluency` **thiên tiếng Việt phổ thông**: bản dịch **tiếng Thái** hoặc tông **cổ phong (game-a)**
  thường bị chấm thấp → `send_to_human` dù nội dung đúng (bảo thủ, không phải lỗi).
- Trạng thái `review_queue.jsonl` / `corrections.jsonl` **ephemeral theo container** (mất khi redeploy).
- Access gate là cổng tĩnh 1 tài khoản (chống tốn token), **không phải auth/RBAC thật**.

## 11. Tài liệu liên quan
- Kiến trúc chi tiết (Ports & Adapters, §10 multi-tenant): [`system-architecture.md`](system-architecture.md)
- Tổng quan + cách chạy/deploy: [`../README.md`](../README.md)
