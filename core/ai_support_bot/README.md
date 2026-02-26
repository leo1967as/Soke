# Sokeber AI Customer Support Bot

> 24/7 Discord AI Support Bot — powered by OpenRouter (any LLM), Notion, and Google Sheets.

## Features

- **Multi-Provider LLM Support** — Works with OpenRouter, OpenAI, Anthropic, or any OpenAI-compatible API
- **Configurable Models** — Switch between GPT-4, Claude, Llama, Cerebras, or any model via env vars
- **RAG Architecture** — Retrieves context from Notion pages & Google Sheets before generating AI responses
- **Prompt Injection Defense** — Sanitizes all user input against 18+ injection patterns
- **Per-User Rate Limiting** — Prevents abuse and quota exhaustion
- **Answer Caching** — Identical questions return cached responses (0 tokens, instant)
- **Structured Audit Logging** — JSON logs per interaction (no user content stored)
- **Docker Ready** — Multi-stage build, non-root user, health checks
- **CI/CD** — GitHub Actions for test, lint, and auto-deploy

## Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd ai_support_bot
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual tokens/keys
```

**Required variables:**
| Variable | Description |
|---|---|
| `DISCORD_BOT_TOKEN` | Your Discord bot token |
| `OPENROUTER_API_KEY` | OpenRouter API key (or your LLM provider key) |
| `ALLOWED_CHANNEL_IDS` | Comma-separated Discord channel IDs |
| `LLM_MODEL` | Model identifier (e.g., `openai/gpt-4o-mini`, `anthropic/claude-3.5-sonnet`) |
| `LLM_PROVIDER` | Provider name for logging (e.g., `openrouter`, `cerebras`, `openai`) |

**Optional variables:**
| Variable | Default | Description |
|---|---|---|
| `NOTION_TOKEN` | — | Notion integration token |
| `GOOGLE_SA_BASE64` | — | Base64-encoded Google SA JSON |
| `CACHE_TTL_SECONDS` | 3600 | Answer cache TTL |
| `RATE_LIMIT_MAX_CALLS` | 5 | Max requests per user per window |
| `LOG_LEVEL` | INFO | Logging verbosity |

### 3. Run Locally

```bash
python -m core.ai_support_bot
```

### 4. Run with Docker

```bash
cd core/ai_support_bot
docker-compose up --build
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=core/ai_support_bot --cov-report=term-missing

# Lint
ruff check core/ai_support_bot/
```

## Project Structure

```
core/ai_support_bot/
├── __main__.py          # Entry point
├── config.py            # Env var loading + validation
├── ai/
│   └── openrouter.py    # OpenRouter/OpenAI-compatible API client
├── bot/
│   ├── client.py        # Discord client + message handling
│   └── commands.py      # Admin slash commands
├── cache/
│   └── memory_cache.py  # Thread-safe TTL cache
├── rag/
│   ├── chunker.py       # Document text chunking
│   ├── notion_fetcher.py# Notion page retriever
│   └── sheets_fetcher.py# Google Sheets row fetcher
├── security/
│   ├── sanitizer.py     # Prompt injection defense
│   └── rate_limiter.py  # Per-user sliding window limiter
└── logging/
    └── audit.py         # Structured JSON audit logger
```

## Admin Commands

| Command | Description |
|---|---|
| `/admin refresh_kb` | Force re-index knowledge base |
| `/admin clear_cache` | Clear answer cache |
| `/admin status` | Show bot health (latency, cache size, etc.) |

## Security

- **No secrets in code** — All credentials via env vars / Docker secrets
- **Google SA as Base64** — Never mount raw JSON files
- **Prompt injection filtering** — 18+ patterns blocked
- **Rate limiting** — 5 req/60s per user (configurable)
- **Non-root Docker user** — Container runs as `botuser`
- **Least-privilege Discord permissions** — No Administrator

## Roadmap

See `docs/MASTER_PLAN.md` for the full 4-phase development roadmap covering:
- Phase 1: Redis cache + ChromaDB vector store + CI/CD
- Phase 2: Conversation history + feedback loop + multi-language
- Phase 3: Task queue + worker pool + Prometheus metrics
- Phase 4: Kubernetes + multi-guild + plugin system
