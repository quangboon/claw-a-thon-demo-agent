# Multi-Tenant Translate + QC Agent (ZH → VI/TH/EN)

**Nền tảng dịch thuật game đa team**: mỗi team = 1 **Profile** (termbase + tone + need-to-avoid + examples +
ngôn ngữ đích riêng), **dữ liệu cô lập**, dùng chung 1 deploy. Có **QC độc lập** (đầy đủ · thuật ngữ ·
trôi chảy · **need-to-avoid** · term-confidence), **tự sửa 1 vòng**, **human-in-the-loop** và **flywheel
học từ correction** — chạy trên GreenNode AgentBase. Profile = **dữ liệu/config**, thêm team không sửa core.

> **Claw-a-thon 2026** · Track: Agentic Assistant · Live demo (API + UI):
> https://endpoint-46484a3a-dbe3-48be-8d2f-e1388456bde8.agentbase-runtime.aiplatform.vngcloud.vn

---

## Mô tả use case (~150 từ)

Đội bản địa hoá game thường mất nhiều công để giữ **nhất quán thuật ngữ** khi dịch nội dung tiếng Trung
(vật phẩm, kỹ năng, cảnh giới tu luyện…) sang tiếng Việt — chỗ mà Google Translate và dịch tay hay sai.
Agent này giải quyết bằng quy trình: quét **termbase** để tìm thuật ngữ bắt buộc → **Translator** dịch và
ép dùng đúng glossary → **QC Reviewer độc lập** rà 3 trục (đầy đủ, tuân thủ thuật ngữ, trôi chảy) →
nếu chưa đạt thì **tự dịch lại 1 vòng** với feedback, vẫn chưa đạt thì **đẩy người duyệt**. Mỗi lần người
sửa, cặp *sai → đúng* được ghi lại (**flywheel**) và một **Term Curator** đề xuất bổ sung termbase — càng
dùng càng chuẩn. Người dùng là **biên dịch viên & reviewer** của đội game; giá trị: nhanh hơn, nhất quán
thuật ngữ, có kiểm soát chất lượng và vết người duyệt. Mọi bản dịch tự gắn nhãn *"Nội dung dịch bởi AI"*.

---

## Luồng hoạt động

```
Nguồn ZH → khớp termbase → Translator (+glossary +corrections) → QC 3 trục
  → pass: auto_approved
  → fail: tự sửa 1 vòng → vẫn fail: đẩy Review Queue (người duyệt)
       → Reject+sửa: lưu correction (flywheel) → Curator đề xuất term mới
```

4 vai LLM: **Term Extractor** (dựng termbase offline) · **Translator** · **QC Reviewer** (chấm trôi chảy) ·
**Term Curator** (học từ corrections). Trục QC #1 (đầy đủ) và #2 (tuân thủ thuật ngữ) là kiểm tra **tất định**;
chỉ trục #3 (trôi chảy) gọi LLM.

## Kiến trúc

Ports & Adapters (hexagonal-lite) — đổi LLM provider / storage / kênh duyệt **không sửa business logic**.
Chi tiết: [`docs/system-architecture.md`](docs/system-architecture.md).

```
backend/app/{domain,application,agents,infrastructure,api}  + cli/   # FastAPI, Python 3.11
profiles/<id>/  (profile.json, termbase, tone/, avoid/, examples/)   # Domain Pack per team (cô lập)
web/  (React + Vite + Tailwind + shadcn-style + TanStack Query)      # 6 màn → build vào backend/static
Dockerfile (multi-stage)  → 1 container serve API + UI trên cổng 8080
```

**Multi-tenant:** mọi request scoped theo header `X-Profile-Id` (thiếu → profile `default` = tương thích v1).
`profiles/<id>/` cô lập termbase/corrections/review-queue per team. UI 6 màn: Playground (+ chọn ngôn ngữ
đích) · Termbase Manager · Review Queue · Corrections · Dashboard · **Profile Admin** (tone/avoid editor).
Seed demo: `default`, `game-a` (cổ phong, vi), `game-b` (hiện đại, vi/th).

## Chạy thử

**Local — CLI (mock, không cần key):**
```bash
python3 -m venv .venv && ./.venv/bin/pip install -r backend/requirements.txt
PYTHONPATH=backend ./.venv/bin/python backend/cli/translate.py --source "灵石 +20%，开放传送阵" --mock
```

**Local — model thật + service:** cấu hình `.env` (xem `.env.example`: `LLM_BASE_URL/API_KEY/MODEL`), rồi:
```bash
PYTHONPATH=backend ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080 --app-dir backend
curl localhost:8080/health
curl -X POST localhost:8080/translate -H "Content-Type: application/json" -d '{"source":"灵石 +20%"}'
```

**UI (dev):** `cd web && npm install && npm run dev` (proxy API sang :8080). **Build:** `npm run build` → `backend/static`.

**Docker (1 container, UI+API):**
```bash
docker build -t translate-qc-agent .
docker run -p 8080:8080 -e LLM_BASE_URL=... -e LLM_API_KEY=... -e LLM_MODEL=qwen/qwen3-5-27b translate-qc-agent
```

## API

Mọi endpoint nghiệp vụ nhận header `X-Profile-Id` (mặc định `default`):
`GET /health` · `POST /translate {source, target_lang?}` · `GET/POST /terms`, `DELETE /terms/{source}`,
`GET /terms/candidates`, `POST /terms/candidates/approve` · `GET /review/pending`,
`POST /review/{id}/approve|reject` · `GET /corrections` · `GET /metrics`.
**Profiles:** `GET /profiles`, `GET /profiles/{id}`, `POST /profiles`, `PUT /profiles/{id}/tone/{lang}`,
`PUT /profiles/{id}/avoid/{lang}`.

**Access gate (login):** bật khi `AUTH_PASSWORD` khác rỗng → màn hình đăng nhập + chặn các endpoint tốn token
(401 nếu thiếu token). `GET /auth/status`, `POST /auth/login {username,password}` → trả bearer token. Public:
`/health`, `/auth/*`, UI tĩnh. Cấu hình `AUTH_USERNAME`/`AUTH_PASSWORD` (xem `.env.example`); rỗng = mở (dev).

**Eval/test:** `PYTHONPATH=backend python backend/cli/run_flowcheck.py --mock --profile game-b --target-lang th
--golden backend/eval/golden_set.game-b.th.jsonl` · pytest: `cd backend && PYTHONPATH=. pytest tests/`.

## Ràng buộc & tuân thủ

- **Dữ liệu giả/công khai**: `backend/data/zh_corpus.txt` + `backend/termbase.json` là dữ liệu **giả/công khai**,
  không dùng dữ liệu khách hàng/PII/nội bộ.
- **Khai báo AI**: mọi bản dịch tự gắn footer *"Nội dung dịch bởi AI"*.
- **Bảo mật**: API key MaaS **không** commit (nạp qua AgentBase credential / `.env` đã gitignore).
- **Model**: GreenNode AI Platform (MaaS) — `qwen/qwen3-5-27b` (cần `enable_thinking=false` để có content sạch).
- **IP**: sản phẩm dự thi thuộc sở hữu GreenNode.

## Open source sử dụng

FastAPI · Uvicorn · Pydantic · OpenAI SDK (client tương thích) · React · Vite · Tailwind CSS ·
Radix/shadcn patterns · TanStack Query · Recharts · lucide-react. Pattern kiến trúc (generator/evaluator,
curator learning-loop) tham khảo từ Hermes Agent (Nous Research, MIT) — **không** dùng lại mã nguồn.
