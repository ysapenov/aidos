# Aidos — Product Requirements Document

## 1. Overview

**Product Name:** Aidos
**Type:** Telegram Bot
**Version:** 2.0 (Phase 2 Complete)
**Last Updated:** July 3, 2026

### 1.1 Vision

Aidos is a personal Telegram AI assistant that helps users learn English vocabulary by providing rich Russian translations with contextual usage examples. The bot operates in an interactive session mode — users enter a translation session, type words one by one, and receive detailed breakdowns instantly.

### 1.2 Problem Statement

Looking up English words and understanding how to use them in context requires switching between multiple apps (dictionaries, translation tools, example databases). Aidos consolidates this into a single conversational interface inside Telegram.

### 1.3 Target Users

- **Primary:** Russian-speaking users learning or working with English vocabulary.
- **Access model:** Private, invite-only (whitelist of Telegram user IDs).

---

## 2. Functional Requirements

### 2.1 Translation Feature (Core — Phase 1)

#### FR-1: Translation Mode (Session-Based)

| ID | Requirement |
|----|-------------|
| FR-1.1 | `/translate` command enters **translate mode** |
| FR-1.2 | In translate mode, every plain text message is treated as a word to translate |
| FR-1.3 | `/stop` command exits translate mode |
| FR-1.4 | Only **single English words** are accepted; multi-word input is rejected with a helpful message |
| FR-1.5 | Translation direction is always **English → Russian** |

#### FR-2: Translation Output

For each word, the bot provides:

| ID | Requirement |
|----|-------------|
| FR-2.1 | Primary Russian translation(s) with English pronunciation (e.g., [rəˈzilyəns]) |
| FR-2.2 | Part of speech (noun, verb, adjective, etc.) |
| FR-2.3 | 2–3 example sentences in English, each with a Russian translation |
| FR-2.4 | 2–3 common collocations or phrases |

#### FR-3: Translation History

| ID | Requirement |
|----|-------------|
| FR-3.1 | Every translation is saved to the user's history |
| FR-3.2 | `/history` shows the last 20 translated words with dates |
| FR-3.3 | `/history clear` clears the user's translation history |
| FR-3.4 | History is capped at **1000 entries per user** (oldest entries are deleted when cap is exceeded) |
| FR-3.5 | `/history words` shows the user's recently generated vocabulary lists |
| FR-3.6 | `/history idioms` shows the recently broadcasted daily idioms |

#### FR-5: Kazakh Translation
| ID | Requirement |
|----|-------------|
| FR-5.1 | All translations include a brief Kazakh translation |
| FR-5.2 | Kazakh translations are stored in the database |

#### FR-6: Advanced Vocabulary (`/words`)
| ID | Requirement |
|----|-------------|
| FR-6.1 | `/words [topic]` generates 2 advanced words, 1 phrasal verb, 1 natural expression |
| FR-6.2 | Vocabulary is stored in DB to ensure no repeats |

#### FR-7: Daily Idiom (`/subscribe`)
| ID | Requirement |
|----|-------------|
| FR-7.1 | `/subscribe` opts user into daily idiom delivery at 14:00 UTC |
| FR-7.2 | Idioms include Kazakh translation and are tracked to avoid repeats |
| FR-7.3 | `/unsubscribe` opts user out |

### 2.2 Bot Commands (Phase 1)

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with bot introduction |
| `/help` | Full command reference |
| `/menu` | Interactive inline keyboard menu |
| `/translate` | Enter translate mode |
| `/stop` | Exit translate mode |
| `/words` | Generate advanced vocabulary |
| `/subscribe` | Subscribe to daily idioms |
| `/unsubscribe` | Unsubscribe from daily idioms |
| `/history` | View translation history |
| `/history words` | View generated vocabulary history |
| `/history idioms` | View daily idioms history |
| `/history clear` | Clear translation history |
| `/allow <user_id>` | *(Admin)* Grant access to a user |
| `/revoke <user_id>` | *(Admin)* Revoke a user's access |
| `/users` | *(Admin)* List all allowed users |

### 2.3 Access Control

| ID | Requirement |
|----|-------------|
| FR-4.1 | Bot access is **restricted** to whitelisted Telegram user IDs |
| FR-4.2 | Initial whitelist is configured via `ALLOWED_USER_IDS` in `.env` |
| FR-4.3 | Admins (configured via `ADMIN_USER_IDS`) can add/remove users at runtime using `/allow` and `/revoke` |
| FR-4.4 | Unauthorized users receive an "Access denied" message |
| FR-4.5 | Whitelist changes persist in the database |

### 2.4 Future Capabilities (Phase 3)

The following features are planned but **out of scope for Phase 2**:

- Weather forecasts (`/weather`)
- Wikipedia summaries (`/wiki`)
- Free-text AI chat (via Gemini)
- Image generation (`/image`)
- News (`/news`)
- Utility commands (`/qrcode`, `/calc`, `/fact`, `/quote`)

---

## 3. Non-Functional Requirements

### 3.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-1.1 | Translation response time ≤ 5 seconds (including Gemini API call) |
| NFR-1.2 | Bot shows "typing..." indicator while processing |
| NFR-1.3 | Bot handles errors gracefully without crashing |

### 3.2 Reliability

| ID | Requirement |
|----|-------------|
| NFR-2.1 | Bot auto-restarts on crash (Docker `restart: unless-stopped`) |
| NFR-2.2 | Database survives container restarts (Docker volume mount) |
| NFR-2.3 | Global error handler catches all unhandled exceptions |

### 3.3 Security

| ID | Requirement |
|----|-------------|
| NFR-3.1 | API keys and tokens stored in `.env`, never committed to git |
| NFR-3.2 | `.env` excluded via `.gitignore` |
| NFR-3.3 | User access restricted by Telegram user ID whitelist |

### 3.4 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-4.1 | Modular architecture: handlers, services, database, utils layers |
| NFR-4.2 | Each feature in its own handler file |
| NFR-4.3 | Structured logging via Python `logging` module |

---

## 4. User Stories

### Translation

> **US-1:** As a user, I want to type `/translate` and then send English words one by one, so I can quickly learn their Russian meanings without typing a command prefix each time.

> **US-2:** As a user, I want to see example sentences for each word, so I can understand how the word is used in context.

> **US-3:** As a user, I want to type `/stop` to exit translate mode, so the bot stops interpreting my messages as words to translate.

> **US-4:** As a user, I want to see my translation history, so I can review words I've looked up before.

### Access Control

> **US-5:** As an admin, I want to add new users via `/allow`, so I can grant access without restarting the bot.

> **US-6:** As an unauthorized user, I want to see a clear "Access denied" message, so I know the bot is private.

---

## 5. Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Bot framework | python-telegram-bot v21+ |
| AI engine | Google Gemini 2.5 Flash via `google-genai` SDK |
| Database | SQLite via `aiosqlite` |
| Config | python-dotenv + environment variables |
| Deployment | Docker + docker-compose on local machine |

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Translation accuracy | Verified manually for 20 common words |
| Response time | < 5 seconds per word |
| Uptime | Bot stays running via Docker auto-restart |
| Error rate | No unhandled crashes in normal usage |

---

## 7. Out of Scope (Phase 2)

- Multi-language support (only EN → RU)
- Sentence/paragraph translation
- Voice message translation
- Inline mode (translation in other chats)
- Web dashboard
- Cloud deployment
