# AI Customer Support Bot — Master Engineering Plan
> Version: 2.0 | Updated: 2026-02-26 | Status: Active

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Security Architecture](#2-security-architecture)
3. [GitHub Readiness & CI/CD](#3-github-readiness--cicd)
4. [Docker & Containerization](#4-docker--containerization)
5. [Scaling Strategy](#5-scaling-strategy)
6. [Data Storage & Indexing](#6-data-storage--indexing)
7. [Future Development Roadmap](#7-future-development-roadmap)
8. [Final Project Structure](#8-final-project-structure)
9. [Checklist (Go-Live Gates)](#9-checklist-go-live-gates)

---

## 1. Project Overview

**Goal:** A production-grade 24/7 Discord AI Support Bot backed by Notion + Google Sheets as a knowledge base, powered by Google Gemini, using RAG (Retrieval-Augmented Generation).

**Core Principles:**
- **Security First** — No secrets ever touch code or Git history.
- **Containerized** — Runs the same in dev, staging, and production.
- **Observable** — Every failure is logged, traced, and alertable.
- **Horizontally Scalable** — Adding more users requires adding more containers, not rewriting code.

---

## 2. Security Architecture

### 2.1 Secrets Management

**Rule: Zero secrets in code, ever.**

| Secret | Where to Store |
|---|---|
| `DISCORD_BOT_TOKEN` | `.env` (local) / GitHub Secrets / Docker Secret / Render Env Var |
| `GEMINI_API_KEY` | Same as above |
| `NOTION_TOKEN` | Same as above |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Base64-encoded env var or Docker Secret mount |

```
# .env.example  (committed to Git — no real values)
DISCORD_BOT_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
NOTION_TOKEN=secret_your_notion_token_here
GOOGLE_SA_BASE64=base64_encoded_service_account_json
ENVIRONMENT=development
LOG_LEVEL=INFO
CACHE_TTL_SECONDS=3600
ALLOWED_CHANNEL_IDS=1476345137419259956
```

**Google Service Account — Never mount the JSON file directly:**
```python
# core/config.py
import base64, json, os
from google.oauth2.service_account import Credentials

def load_google_credentials():
    b64 = os.environ["GOOGLE_SA_BASE64"]
    info = json.loads(base64.b64decode(b64))
    return Credentials.from_service_account_info(info, scopes=[...])
```

### 2.2 Input Sanitization & Prompt Injection Defense

All user messages MUST be sanitized before being inserted into the Gemini prompt.

```python
# core/security/sanitizer.py

MAX_MESSAGE_LENGTH = 500
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "you are now",
    "forget your rules",
    "system:",
    "```",
]

def sanitize_user_input(text: str) -> str | None:
    """Returns sanitized text or None if message is rejected."""
    text = text.strip()[:MAX_MESSAGE_LENGTH]
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in lower:
            return None  # Reject silently
    return text
```

### 2.3 Rate Limiting (Per User)

Prevents a single user from spamming the bot and exhausting Gemini quota.

```python
# core/security/rate_limiter.py
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_calls: int = 5, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window = window_seconds
        self._records: dict[int, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        now = time.monotonic()
        calls = self._records[user_id]
        self._records[user_id] = [t for t in calls if now - t < self.window]
        if len(self._records[user_id]) >= self.max_calls:
            return False
        self._records[user_id].append(now)
        return True
```

### 2.4 Discord Bot Permission Scoping

The bot should operate on **least-privilege**:

| Permission | Required? | Why |
|---|---|---|
| `Read Messages` | ✅ | To receive messages |
| `Send Messages` | ✅ | To reply |
| `Read Message History` | ✅ | For context threading |
| `Manage Messages` | ❌ | Not needed |
| `Administrator` | ❌ | **Never grant this** |

### 2.5 Audit Logging

Every AI response must be logged with full context for debugging and abuse detection.

```python
# core/logging/audit.py
import logging, json
from datetime import datetime, timezone

audit_logger = logging.getLogger("audit")

def log_interaction(user_id: int, user_input: str, bot_response: str, cache_hit: bool, tokens_used: int):
    audit_logger.info(json.dumps({
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "input_length": len(user_input),
        "cache_hit": cache_hit,
        "tokens_used": tokens_used,
        "response_length": len(bot_response),
    }))
```

Logs are written to `logs/audit.jsonl` — **never log the actual user message content** in production for privacy.

---

## 3. GitHub Readiness & CI/CD

### 3.1 Repository Structure for GitHub

```
.gitignore          # Covers .env, .venv, __pycache__, *.json (SA keys), logs/
.env.example        # Template — safe to commit
README.md           # Setup guide
CHANGELOG.md        # Version history (docs/)
```

### 3.2 `.gitignore` (Critical Entries)

```gitignore
# Secrets — NEVER commit these
.env
*.json
!pyproject.toml

# Python
.venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Logs & runtime artifacts
logs/
*.log
*.jsonl

# OS
.DS_Store
Thumbs.db
```

### 3.3 Branch Strategy (Git Flow Simplified)

```
main          ← Production-only. Protected. Requires PR + review.
  └── develop ← Integration branch. All features merge here first.
        ├── feature/rag-chromadb
        ├── feature/rate-limiter
        └── hotfix/gemini-timeout
```

**Branch Protection Rules on `main`:**
- Require pull request before merging
- Require status checks (CI) to pass
- No direct pushes

### 3.4 GitHub Actions — CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run pytest tests/ --cov=core --cov-report=xml -v
      - name: Check secrets not leaked
        run: grep -r "AKIA\|sk-\|secret_" src/ && exit 1 || exit 0

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv run ruff check .
      - run: uv run mypy core/
```

### 3.5 GitHub Actions — CD Pipeline (Auto-deploy to Render)

```yaml
# .github/workflows/cd.yml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy Hook
        run: curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
```

**GitHub Secrets to configure:**
- `RENDER_DEPLOY_HOOK_URL`
- All production env vars (referenced in Render dashboard, not directly in GH Actions for this bot)

---

## 4. Docker & Containerization

### 4.1 Multi-Stage Dockerfile

```dockerfile
# Dockerfile

# ── Stage 1: Builder ──────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: Runtime ─────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

# Non-root user for security
RUN useradd --create-home botuser
USER botuser

COPY --from=builder /app/.venv /app/.venv
COPY core/ ./core/
COPY main.py .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import core; print('ok')" || exit 1

CMD ["python", "main.py"]
```

**Why Multi-Stage?**
- Builder stage installs all build tools (larger image).
- Runtime stage is minimal (~150MB vs ~600MB) — no build tools, no dev dependencies.

### 4.2 `docker-compose.yml` (Local Dev + Staging)

```yaml
# docker-compose.yml
version: "3.9"

services:
  bot:
    build:
      context: .
      target: runtime
    env_file: .env
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs   # Persist logs outside container
    networks:
      - bot-net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - bot-net

networks:
  bot-net:
    driver: bridge
```

### 4.3 Docker Image Tagging & Publishing

```bash
# Tag by Git SHA for traceability
docker build -t sokeber-bot:$(git rev-parse --short HEAD) .
docker tag sokeber-bot:$(git rev-parse --short HEAD) ghcr.io/your-org/sokeber-bot:latest

# Push to GitHub Container Registry
docker push ghcr.io/your-org/sokeber-bot:latest
```

---

## 5. Scaling Strategy

### 5.1 Current Bottlenecks (Honest Assessment)

| Component | Bottleneck | Impact |
|---|---|---|
| Gemini API | Free tier: 15 RPM / 1M TPM | Hard ceiling |
| In-memory cache | Lost on restart | No persistence |
| Single process | One crash = total downtime | Availability |
| Notion API | 3 req/sec rate limit | Context fetch delay |

### 5.2 Phase 1 — Vertical + Persistent Cache (Now → 500 users)

Replace in-memory `dict` cache with **Redis**:

```python
# core/cache/redis_cache.py
import redis.asyncio as aioredis
import json, hashlib

class RedisCache:
    def __init__(self, url: str = "redis://redis:6379"):
        self.client = aioredis.from_url(url)

    def _key(self, text: str) -> str:
        return f"qa:{hashlib.sha256(text.encode()).hexdigest()[:16]}"

    async def get(self, question: str) -> str | None:
        val = await self.client.get(self._key(question))
        return val.decode() if val else None

    async def set(self, question: str, answer: str, ttl: int = 3600):
        await self.client.setex(self._key(question), ttl, answer)
```

**Benefits:** Cache survives bot restarts. Shared across multiple bot instances.

### 5.3 Phase 2 — Horizontal Scaling (500+ users)

Replace direct Gemini calls with a **Task Queue**:

```
Discord Bot (N instances)
        │
        ▼ (publish task)
  Redis Queue (rq / Celery)
        │
        ▼ (consume)
  Worker Pool (M instances)
        │
        ▼
   Gemini API
        │
        ▼ (publish result)
  Redis Pub/Sub
        │
        ▼ (subscribe)
  Discord Bot → Send reply
```

**Why a queue?**
- Bot instances can handle more concurrent messages without blocking.
- Workers can be scaled independently from the bot.
- Built-in retry logic for Gemini failures.

### 5.4 Discord Gateway Sharding (1000+ Guilds)

When the bot joins many servers, Discord requires **sharding**:

```python
# core/bot/client.py
import discord

class SokeberBot(discord.AutoShardedClient):
    """AutoShardedClient handles shard assignment automatically."""
    ...
```

`discord.py`'s `AutoShardedClient` manages this automatically — just swap the base class.

### 5.5 Scaling Decision Tree

```
< 100 users/day    → Single Docker container + in-memory cache
100–500 users/day  → Docker + Redis cache (Phase 1)
500–5000 users/day → Docker Compose + Redis Queue + Worker pool (Phase 2)
5000+ users/day    → Kubernetes (k8s) + managed Redis (Upstash) + PostgreSQL
```

---

## 6. Data Storage & Indexing

### 6.1 Storage Layer Overview

```
┌─────────────────────────────────────────────────────┐
│  Knowledge Sources (External, Read-Only)            │
│  ├── Notion API     → FAQ, Rules, Product Info      │
│  └── Google Sheets  → Pricing, Member Data          │
└──────────────┬──────────────────────────────────────┘
               │ Ingestion (background job, hourly)
               ▼
┌─────────────────────────────────────────────────────┐
│  Local Vector Store (ChromaDB)                      │
│  ├── Collection: "knowledge_base"                   │
│  │   ├── doc: notion_page_abc (embedding + text)    │
│  │   └── doc: sheets_row_42  (embedding + text)     │
│  └── Persistent: ./data/chromadb/                   │
└──────────────┬──────────────────────────────────────┘
               │ Semantic Search (on each query)
               ▼
┌─────────────────────────────────────────────────────┐
│  Cache Layer (Redis)                                │
│  ├── Answer Cache  → Hash(question) → answer (TTL) │
│  └── Doc Cache     → Raw Notion/Sheets pages (TTL) │
└─────────────────────────────────────────────────────┘
               │ Final context chunks
               ▼
           Gemini API
```

### 6.2 Vector Indexing with ChromaDB

```python
# core/rag/vector_store.py
import chromadb
from chromadb.utils import embedding_functions

class VectorStore:
    def __init__(self, persist_path: str = "./data/chromadb"):
        self.client = chromadb.PersistentClient(path=persist_path)
        ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=os.environ["GEMINI_API_KEY"],
            model_name="models/text-embedding-004"
        )
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, doc_id: str, text: str, metadata: dict):
        self.collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata]
        )

    def query(self, question: str, n_results: int = 3) -> list[str]:
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            include=["documents", "distances"]
        )
        return results["documents"][0]
```

**ChromaDB HNSW Index** — uses Hierarchical Navigable Small World graph for approximate nearest-neighbor search. Fast even at 100K+ documents.

### 6.3 Document Chunking Strategy

Notion pages should be chunked before indexing — not stored as whole pages.

```python
# core/rag/chunker.py

CHUNK_SIZE = 400       # characters
CHUNK_OVERLAP = 80     # characters overlap between chunks

def chunk_text(text: str, source_id: str) -> list[dict]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        chunks.append({
            "id": f"{source_id}_chunk_{start}",
            "text": chunk,
            "meta": {"source": source_id, "start": start}
        })
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks
```

**Why chunking?**
- Sending an entire Notion page to Gemini wastes tokens.
- Smaller, focused chunks = more relevant retrieval.

### 6.4 Ingestion Background Job

```python
# core/rag/ingestion.py
import asyncio

async def run_ingestion(notion_client, sheets_client, vector_store, interval: int = 3600):
    """Background task: re-indexes all knowledge sources every hour."""
    while True:
        pages = await notion_client.fetch_all_pages()
        for page in pages:
            chunks = chunk_text(page.content, source_id=page.id)
            for chunk in chunks:
                vector_store.upsert(chunk["id"], chunk["text"], chunk["meta"])
        
        rows = await sheets_client.fetch_all_rows()
        for row in rows:
            vector_store.upsert(row.id, row.to_text(), {"source": "sheets"})

        await asyncio.sleep(interval)
```

### 6.5 PostgreSQL (Optional, Phase 2+)

For persistent conversation history, user preferences, and analytics:

```sql
-- Conversation log for analytics & fine-tuning
CREATE TABLE interactions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL,
    guild_id    BIGINT,
    channel_id  BIGINT NOT NULL,
    question    TEXT NOT NULL,
    answer      TEXT NOT NULL,
    cache_hit   BOOLEAN DEFAULT FALSE,
    tokens_used INT,
    latency_ms  INT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_interactions_user_id  ON interactions(user_id);
CREATE INDEX idx_interactions_created_at ON interactions(created_at DESC);
```

---

## 7. Future Development Roadmap

### Phase 0 — Foundation (Current Sprint)
- [x] Project structure & uv setup
- [ ] `.env` + `.env.example` + `.gitignore`
- [ ] Core Discord bot (single channel listener)
- [ ] Notion + Sheets integration
- [ ] Gemini integration (basic prompt)
- [ ] In-memory cache
- [ ] Dockerfile + docker-compose

### Phase 1 — Hardening (Month 1–2)
- [ ] Prompt injection sanitization
- [ ] Per-user rate limiter
- [ ] Redis persistent cache (replace in-memory)
- [ ] ChromaDB vector store + chunker
- [ ] Ingestion background job
- [ ] Audit logging (`logs/audit.jsonl`)
- [ ] GitHub Actions CI (pytest + ruff)
- [ ] GitHub Actions CD (Render deploy hook)
- [ ] Structured logging (JSON format)

### Phase 2 — Intelligence Upgrade (Month 2–4)
- [ ] Conversation history per user (last N turns as context)
- [ ] Confidence scoring — if Gemini is uncertain, route to human
- [ ] Multi-language support (detect language, respond in kind)
- [ ] Slash commands (`/ask`, `/refresh_kb`, `/feedback`)
- [ ] Feedback loop — thumbs up/down reaction stores rating in PostgreSQL
- [ ] Admin dashboard (simple FastAPI web UI showing interaction stats)

### Phase 3 — Scale & Observability (Month 4–6)
- [ ] Redis task queue (rq) for async Gemini calls
- [ ] Worker pool (separate Docker service)
- [ ] Prometheus metrics endpoint (`/metrics`)
- [ ] Grafana dashboard for bot health
- [ ] PagerDuty / Discord alert on bot crash or high error rate
- [ ] PostgreSQL for interaction history
- [ ] Fine-tuning dataset export from PostgreSQL interactions

### Phase 4 — Enterprise (Month 6+)
- [ ] Kubernetes deployment manifests (k8s YAML)
- [ ] Multi-server (multi-guild) support with per-guild config
- [ ] Plugin system for new knowledge sources
- [ ] Swap Gemini → OpenAI / Anthropic with one config change
- [ ] GDPR compliance — user data deletion endpoint

---

## 8. Final Project Structure

```
ai_support_bot/
├── main.py                          # Entry point
├── pyproject.toml                   # uv dependencies
├── uv.lock                          # Lockfile (commit this)
├── Dockerfile                       # Multi-stage production build
├── docker-compose.yml               # Local dev + staging stack
├── .env.example                     # Safe template (committed)
├── .gitignore
├── README.md
│
├── core/
│   ├── config.py                    # Env var loading + validation
│   ├── bot/
│   │   ├── client.py                # discord.AutoShardedClient subclass
│   │   └── commands.py              # Slash/prefix admin commands
│   ├── rag/
│   │   ├── notion.py                # Notion page fetcher
│   │   ├── sheets.py                # Google Sheets fetcher
│   │   ├── chunker.py               # Text chunking
│   │   ├── vector_store.py          # ChromaDB wrapper
│   │   └── ingestion.py             # Background re-indexing job
│   ├── ai/
│   │   └── gemini.py                # Gemini prompt builder + caller
│   ├── cache/
│   │   └── redis_cache.py           # Redis answer + doc cache
│   ├── security/
│   │   ├── sanitizer.py             # Input sanitization
│   │   └── rate_limiter.py          # Per-user rate limiting
│   └── logging/
│       └── audit.py                 # Structured audit logger
│
├── tests/
│   ├── unit/
│   │   ├── test_sanitizer.py
│   │   ├── test_rate_limiter.py
│   │   ├── test_chunker.py
│   │   └── test_cache.py
│   └── integration/
│       ├── test_rag_pipeline.py
│       └── test_gemini_prompt.py
│
├── data/
│   └── chromadb/                    # Persisted vector index (gitignored)
│
├── logs/                            # Runtime logs (gitignored)
│   └── audit.jsonl
│
├── docs/
│   ├── MASTER_PLAN.md               # This file
│   ├── plan.md/plan.md              # Original architecture note
│   └── plan.md/task.md              # Original task checklist
│
└── .github/
    └── workflows/
        ├── ci.yml                   # Test + lint on push
        └── cd.yml                   # Auto-deploy to Render on main
```

---

## 9. Checklist (Go-Live Gates)

Before merging any feature to `main`, ALL must pass:

### Security Gates
- [ ] No `.env` or `*.json` (SA keys) in `git log`
- [ ] `GOOGLE_SA_BASE64` used — raw JSON file not mounted
- [ ] Prompt injection patterns tested
- [ ] Rate limiter tested (5 req/min per user enforced)
- [ ] Bot has no `Administrator` permission in Discord

### Code Quality Gates
- [ ] `uv run ruff check .` passes (0 errors)
- [ ] `uv run mypy core/` passes (0 errors)
- [ ] `uv run pytest tests/ --cov=core` ≥ 70% coverage

### Docker Gates
- [ ] `docker build .` succeeds on clean machine
- [ ] `docker-compose up` starts bot + redis with no manual steps
- [ ] Container runs as non-root user (`botuser`)
- [ ] Health check passes within 30s

### Operational Gates
- [ ] Bot restarts automatically on crash (`restart: unless-stopped`)
- [ ] `logs/audit.jsonl` is written correctly per interaction
- [ ] Graceful shutdown handled (`SIGTERM` → close Discord connection)

---

> **Maintained by:** Sokeber Dev Team
> **Next Review:** After Phase 1 completion
