# System Architecture — ZH→VI Translate + QC Agent

> Authoritative kiến trúc source. Mục tiêu: **SOLID + dễ mở rộng** mà vẫn **right-sized** cho hackathon
> (YAGNI/KISS). Nguồn nghiên cứu: `plans/reports/researcher-260615-2239-solid-extensible-architecture.md`.
> Plan thực thi: `plans/260615-2204-zh-vi-translate-qc-agent/plan.md`.

## 1. Nguyên tắc kiến trúc
- **Ports & Adapters (Hexagonal lite):** domain/application **không biết** hạ tầng. Hạ tầng phụ thuộc domain
  qua interface (port). → đổi LLM provider / storage / review channel **không sửa business logic** (DIP + OCP).
- **Registry + decorator** cho phần cắm-thêm (QC rules, LLM providers, review channels) → thêm cái mới = thêm file,
  không sửa core (OCP).
- **Service layer** chứa use-case; **FastAPI `Depends()`** làm DI (không thêm lib DI — YAGNI).
- **Repository** trừu tượng hoá storage (file giờ → AgentBase Memory sau) qua 1 interface.
- 1 trách nhiệm / module (SRP); interface nhỏ gọn (ISP); adapter thay thế được qua port (LSP).

## 2. Tầng (layers)
| Tầng | Phụ thuộc | Vai trò |
|------|-----------|---------|
| `domain` | không import gì ngoài stdlib | entities (dataclass) + **ports** (Protocol) |
| `application` | chỉ `domain` (ports) | use-case/service: TranslationService, QCService, CuratorService |
| `agents` | `domain` + application ports | 4 vai LLM: extractor, translator, qc_reviewer, term_curator |
| `infrastructure` | implement ports của `domain` | adapters: LLM, repositories, qc rules, review channels + registries |
| `api` | application + infrastructure (wiring) | FastAPI routers + `Depends()` composition |

Quy tắc vàng: **mũi tên phụ thuộc luôn hướng vào trong** (api → application → domain). Domain không biết FastAPI/file/HTTP.

## 3. Cây thư mục
```
backend/
  app/
    main.py                 # FastAPI app + mount static web build (/), include routers
    settings.py             # đọc env (LLM_*, STORAGE_BACKEND, REVIEW_CHANNEL…)
    domain/
      entities.py           # Term, TranslationJob, QcIssue, QcVerdict, Correction (dataclass)
      ports.py              # Protocol: LLMProvider, TermbaseRepository, ReviewChannel, CorrectionStore
    application/
      translation_service.py  # match → translate → qc → self-correct → decision
      qc_service.py           # chạy chuỗi QC rule (deterministic + LLM fluency)
      curator_service.py      # gom corrections → đề xuất term + trust_score
    agents/
      term_extractor.py     # agent #1 (offline): corpus ZH → term candidates
      translator.py         # agent #2: dịch + inject glossary/corrections + footer AI
      qc_reviewer.py        # agent #3: chấm fluency (LLM) — trục #3
      term_curator.py       # agent #4 (offline): logic curate
    infrastructure/
      llm/
        registry.py         # @register_llm("openai-compat"), get_llm_provider(name)
        openai_compat.py    # adapter MaaS (OpenAI-compatible) — implement LLMProvider
        mock.py             # MockLLM cho --mock/test
      repositories/
        termbase_file.py    # FileTermbaseRepository (MVP, termbase.json)
        termbase_memory.py  # (sau) AgentBaseMemoryRepository — cùng port
        correction_file.py  # corrections.jsonl
      qc/
        registry.py         # @register_qc_rule(name)
        rules/
          completeness.py   # trục #1 (rỗng/placeholder/độ dài)
          term_compliance.py# trục #2 (deterministic, word-boundary match)
          # fluency.py dùng LLM → đặt ở qc_service gọi qc_reviewer agent
      channels/
        registry.py         # @register_channel(name)
        file_queue.py       # ReviewChannel MVP (review_queue.jsonl)
        teams.py            # (sau) MS Teams — cùng port
    api/
      dependencies.py       # Depends(): get_llm, get_termbase, get_review_channel…
      health.py  translate.py  terms.py  review.py  corrections.py  metrics.py
  cli/
    build_termbase.py       # chạy extractor offline → termbase.json
    run_curator.py          # chạy curator offline
    run_flowcheck.py        # golden-set eval
  data/zh_corpus.txt   termbase.json   corrections.jsonl
  eval/golden_set.jsonl
  tests/
  requirements.txt
web/                        # React + Vite + Tailwind + shadcn/ui → build ra backend/static/
Dockerfile                  # multi-stage: node build web → copy static → image Python (uvicorn app.main:app)
```
> Python files dùng **snake_case** (bắt buộc để import được — đè quy tắc kebab chung). React/TS theo convention JS.

## 4. Port/Adapter idiom (Python)
```python
# domain/ports.py — Protocol = structural typing, decouple tối đa
from typing import Protocol, Optional
from .entities import Term, QcIssue

class LLMProvider(Protocol):
    def chat(self, messages: list[dict], max_tokens: int = 1024, temperature: float = 0.2) -> str: ...

class TermbaseRepository(Protocol):
    def search(self, zh: str) -> Optional[Term]: ...
    def match_in(self, source: str) -> list[Term]: ...
    def upsert(self, term: Term) -> None: ...

class ReviewChannel(Protocol):
    def enqueue(self, job_id: str, payload: dict) -> None: ...

# application/translation_service.py — KHÔNG biết adapter cụ thể (DIP)
class TranslationService:
    def __init__(self, llm: LLMProvider, termbase: TermbaseRepository,
                 corrections: "CorrectionStore"):
        self.llm, self.termbase, self.corrections = llm, termbase, corrections
    def run(self, source: str) -> dict: ...   # match → translate → qc → self-correct → decision

# api/dependencies.py — wiring bằng FastAPI Depends (DI native, no lib)
from fastapi import Depends
from app.settings import settings
from app.infrastructure.llm.registry import get_llm_provider
def get_llm(): return get_llm_provider(settings.LLM_BACKEND)
def get_termbase(): return FileTermbaseRepository(settings.TERMBASE_PATH)
```

## 5. Registry idiom (OCP — thêm rule/provider không sửa core)
```python
# infrastructure/qc/registry.py
_REGISTRY: dict[str, type] = {}
def register_qc_rule(name):
    def deco(cls): _REGISTRY[name] = cls; return cls
    return deco
def all_qc_rules(): return [cls() for cls in _REGISTRY.values()]

# infrastructure/qc/rules/term_compliance.py
@register_qc_rule("term-compliance")
class TermComplianceRule:
    def check(self, source, draft, matched_terms) -> list[QcIssue]: ...
# Rule mới = file mới + decorator. Không đụng core.
```
Tương tự cho `llm/registry.py` (`@register_llm`) và `channels/registry.py` (`@register_channel`).

## 6. DI strategy
- **Chỉ dùng FastAPI `Depends()`** (request-scoped) — built-in, tích hợp OpenAPI, đủ cho scope này.
- Chỉ thêm lib DI (`dependency-injector`/`svcs`) nếu sau cần singleton app-scoped / dùng ngoài HTTP context. **Chưa cần.**

## 7. YAGNI cut-list (BỎ cho hackathon)
| Bỏ | Lý do |
|----|-------|
| CQRS | pipeline không tách read/write model |
| Event bus / event sourcing | không có async messaging giữa service; registry đủ cho pluggability |
| Unit-of-Work | chỉ ghi đơn (file). Thêm khi có transaction đa bảng |
| DDD đầy đủ (aggregate, bounded context) | dataclass entity + Protocol port là đủ |
| ORM (SQLAlchemy) | storage file; swap qua Repository khi cần DB |
| GraphQL / Redis | REST + dict in-memory đủ nhanh cho scope |

## 8. Giữ lại (minimum viable SOLID)
Ports (Protocol) + Adapters · Registry cho QC rules & providers · Service layer + `Depends()` ·
Repository abstraction · 1 container (FastAPI + static React).

## 9. Cách kiến trúc đáp ứng mở rộng tương lai
- **Đổi LLM provider:** thêm adapter trong `infrastructure/llm/` + `@register_llm` → set `LLM_BACKEND`.
- **Termbase lên AgentBase Memory:** thêm `termbase_memory.py` (cùng port) → đổi `get_termbase()`.
- **Human-review qua MS Teams:** thêm `channels/teams.py` (cùng `ReviewChannel`) → đổi `REVIEW_CHANNEL`.
- **Thêm trục QC mới:** thêm file rule + decorator.
- **Đa ngữ (en/th) sau này:** TranslationService nhận `target_lang`; termbase đã đa cột.

## Tham khảo (GitHub)
- cosmicpython/book (Repository/Service patterns) · zhanymkanov/fastapi-best-practices (feature structure)
- fastapi/full-stack-fastapi-template (1 container FE+BE) · ivan-borovets/fastapi-clean-example (DI)
- tomasanchez/cosmic-fastapi (clean + event-ready cho mở rộng)
