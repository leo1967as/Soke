AI Customer Support Bot - Architecture & Implementation Plan
Overview
This document outlines the architecture and implementation strategy for a 24/7 Discord AI Support Bot. The bot will listen to a specific channel (1476345137419259956), retrieve context from Notion and Google Sheets, and use Google Gemini 1.5 Flash (free tier) to generate accurate, context-aware responses.

Architecture & Data Flow
The Flow
Trigger: User sends a message in the designated Discord channel.
Filter & Validation: The bot receives the event, checks the channel ID, and ignores messages from itself or other bots.
Intent & Cache Check (Optimization 1):
Does this exact/similar question exist in the Answer Cache?
If YES -> Return cached answer immediately (0 Tokens used, 0s latency).
If NO -> Proceed to context retrieval.
Context Retrieval (Optimization 2 - RAG):
The bot fetches necessary context. To save time/API calls, the bot maintains a Document Cache (Notion/Sheets) updated periodically (e.g., every 1 hour) or via webhooks.
It pulls relevant text snippets based on the user's question.
AI Generation:
The user's question + retrieved context + system prompt (persona guidelines) are sent to the Gemini API.
Response & Store:
The bot replies in the Discord channel.
The Answer Cache is updated with this new Q&A pair.
Addressing Potential Blind Spots & Solutions
Blind Spot 1: API Rate Limiting (Discord/Gemini/Notion).
Solution: Implement exponential backoff for API calls. Use aggressive caching for Notion/Sheets so we only read from the source when necessary, not on every user message.
Blind Spot 2: Excessive Token Usage.
Solution: Implement Semantic Caching (if possible) or Exact Match Caching. Only send relevant Notion paragraphs to Gemini, not the entire database workspace. Use a local vector store (ChromaDB) or simple keyword matching to find the right chunk.
Blind Spot 3: Outdated Information.
Solution: Background task that refreshes the Document Cache every X minutes, or a manual Discord command (e.g., !refresh_kb) for admins to force an update after editing Notion.
Blind Spot 4: Bot Crash/Downtime.
Solution: Containerize with Docker and use a host that restarts the container automatically on failure. Implement robust try-except blocks around all external API calls.
Project Structure (Prepared for Scale & Docker/GitHub)
text
ai_support_bot/
├── .venv/                  # Virtual environment (managed by uv)
├── src/
│   ├── main.py             # Entry point (runs the Discord bot)
│   ├── config.py           # Loads environment variables
│   ├── bot/
│   │   ├── client.py       # Discord bot setup and event handlers
│   │   └── commands.py     # Admin commands (e.g., !refresh)
│   ├── rag/
│   │   ├── notion.py       # Functions to fetch/parse Notion pages
│   │   ├── sheets.py       # Functions to fetch Google Sheets data
│   │   └── cache.py        # Logic for Document and Answer caching
│   └── ai/
│       └── gemini.py       # Gemini API integration and prompt construction
├── tests/
│   ├── test_rag.py         # Unit tests for data fetching
│   └── test_ai.py          # Unit tests for prompt generation
├── .env                    # Secrets (NOT committed to git)
├── .env.example            # Template for environment variables
├── .gitignore              # Ignores .venv, .env, __pycache__, etc.
├── pyproject.toml          # uv dependency definitions
├── Dockerfile              # Instructions to build the image for cloud hosting
└── run.bat                 # Local runner script
Proposed Changes
[NEW] Configuration & Setup
Initialize project with uv.
Create .env.example, pyproject.toml, and 
.gitignore
.
Create Dockerfile for seamless deployment to platforms like Render or Hugging Face.
[NEW] Core Bot Implementation (src/main.py, src/bot/)
Setup discord.py client.
Implement on_message event listener mapped to channel 1476345137419259956.
[NEW] RAG & Integration Layer (src/rag/)
Implement notion.py using notion-client to fetch page content.
Implement sheets.py using gspread and the existing service account JSON.
Implement an in-memory or file-based cache.py to prevent redundant API calls.
[NEW] AI Engine (src/ai/)
Implement gemini.py using google-generativeai.
Design system prompts to enforce the bot's persona and limit hallucination (e.g., "Answer ONLY based on the provided context").
User Review Required
IMPORTANT

Please review the proposed architecture, specifically the Caching Strategy and Folder Structure. Are you comfortable with this setup for scaling and uploading to GitHub/Docker?

Verification Plan
Automated Tests
Unit tests (pytest in tests/) to verify:
Cache hit/miss logic.
Parsing of Notion API responses into plain text.
Proper formatting of the Gemini prompt.
Manual Verification
Run the bot locally using run.bat.
Send a test message in Discord channel 1476345137419259956 asking a question whose answer exists in Notion.
Verify the bot replies correctly.
Ask the same question again and verify it pulls from the Cache (expect faster response time).
Verify the bot ignores messages in other channels.

