# Aidos — Product Requirements Document

## 1. Overview

**Product Name:** Aidos
**Type:** Telegram Bot
**Version:** 2.2 (Advanced Voice Journaling & Cloud Sync)
**Last Updated:** September 18, 2026

### 1.1 Vision

Aidos is a personal Telegram AI assistant that combines two core capabilities:
1. **Language Learning:** Helps users master English vocabulary with Russian and Kazakh translations, pronunciation, and contextual examples.
2. **Intelligent Voice Journaling:** Lets users record short (< 1 min) voice thoughts in Russian or English anytime without commands; Aidos cleans up fillers and noise, categorizes, tracks mood/energy, extracts action items into an interactive task tracker, synthesizes weekly/monthly digests, and syncs seamlessly with Google Sheets and CSV.



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
| FR-1.5 | Translation direction is always **English → Russian and Kazakh** |

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
| FR-3.5 | `/history_words` shows the user's recently generated vocabulary lists |
| FR-3.6 | `/history_idioms` shows the recently broadcasted daily idioms |

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

#### FR-8: Voice Journaling & Thought Structuring
| ID | Requirement |
|----|-------------|
| FR-8.1 | User can send audio or voice notes (< 60s) directly without any initiating command |
| FR-8.2 | Audio exceeding 60 seconds is rejected with an informative prompt |
| FR-8.3 | Speech in Russian, English, or bilingual code-switching is accurately transcribed |
| FR-8.4 | Verbal fillers ("эээ", "ммм", "ну", "типа", "like", "you know"), stuttering, and background noise are removed |
| FR-8.5 | Thoughts are structured into: Title, Category (Ideas, Work, Personal, Learning, Health, To-Do, Reflection, Other), Summary, Key Points, Action Items, Tags, and Clean Transcript |
| FR-8.6 | Entries are saved in SQLite (`journal_entries`) with duration, telegram file ID, and timestamps |
| FR-8.7 | Bot replies with a formatted summary card with inline delete and CSV export buttons |
| FR-8.8 | `/notes` displays the last 10 entries with quick inspection links |
| FR-8.9 | `/notes <id>` displays full detail for a single note |
| FR-8.10 | `/notes export` generates and delivers a UTF-8 CSV containing both summaries and full transcriptions |
| FR-8.11 | Dedicated `JOURNAL_MODEL` (Gemini 3.8 Flash) operates independently of translation model |

#### FR-9: Mood & Energy Tracking
| ID | Requirement |
|----|-------------|
| FR-9.1 | Emotional tone (mood) and energy level are inferred from voice thoughts |
| FR-9.2 | Values are saved in `journal_entries` table (`mood`, `energy_level`) |
| FR-9.3 | Displayed on note cards (e.g., `🎭 Mood: Focused • ⚡ High energy`) and included in CSV and Google Sheets |

#### FR-10: Action Items Tracker (`/actions`)
| ID | Requirement |
|----|-------------|
| FR-10.1 | Action items extracted from thoughts are auto-saved to dedicated `action_items` table |
| FR-10.2 | `/actions` displays interactive dashboard of pending tasks with completion checkboxes |
| FR-10.3 | `/actions all` displays both pending and completed tasks |
| FR-10.4 | `/actions clear` purges completed tasks from database |
| FR-10.5 | Users can toggle completion status in-place via inline callback buttons |

#### FR-11: Interactive Category Management
| ID | Requirement |
|----|-------------|
| FR-11.1 | Note card contains a `[🏷 Category]` button allowing post-save category modification |
| FR-11.2 | Users can pick from 8 standard categories (Ideas, Work, Personal, Learning, Health, To-Do, Reflection, Other) |
| FR-11.3 | Category is updated in SQLite database and card is instantly refreshed |

#### FR-12: Weekly & Monthly Reflection Digests (`/digest`)
| ID | Requirement |
|----|-------------|
| FR-12.1 | `/digest` generates an AI-synthesized executive summary of thoughts from the last 7 days |
| FR-12.2 | `/digest monthly` synthesizes thoughts from the last 30 days |
| FR-12.3 | Digest analyzes momentum, mood trends, standout insights, pending tasks, and recommendations |
| FR-12.4 | Automated weekly digest is scheduled via APScheduler job queue every Sunday at 18:00 UTC |

#### FR-13: Google Sheets Cloud Integration
| ID | Requirement |
|----|-------------|
| FR-13.1 | Service account authentication (`gspread`) connects bot directly to user Google Sheet |
| FR-13.2 | New thoughts are automatically appended to the target spreadsheet in the background |
| FR-13.3 | `/notes sync` performs bulk sync of all historical notes to Google Sheets |
| FR-13.4 | Integration is completely optional; operates gracefully in local SQLite mode if unconfigured |

### 2.2 Bot Commands

| Command | Description |
|---------|-------------|
| *(Send voice/audio)* | Record short thought (< 1 min) — auto-transcribed, categorized, mood & tasks extracted |
| `/notes` | View recent thoughts, filter, or access CSV & Sheets sync |
| `/notes <id>` | View details of note `#id` with category & delete options |
| `/notes export` | Download thoughts journal as CSV with BOM |
| `/notes sync` | Sync all thoughts to Google Sheets |
| `/actions` | View and check off pending action items |
| `/actions all` | View all action items including completed ones |
| `/actions clear`| Clear all completed action items |
| `/digest` | Weekly AI reflection & momentum digest (last 7 days) |
| `/digest monthly`| Monthly AI reflection & momentum digest (last 30 days) |
| `/start` | Welcome message with bot introduction |
| `/help` | Full command reference |
| `/menu` | Interactive inline keyboard menu |
| `/translate` | Enter translate mode |
| `/stop` | Exit translate mode |
| `/words` | Generate advanced vocabulary |
| `/subscribe` | Subscribe to daily idioms |
| `/unsubscribe` | Unsubscribe from daily idioms |
| `/history` | View translation history |
| `/history_words` | View generated vocabulary history |
| `/history_idioms` | View daily idioms history |
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

> **US-1:** As a user, I want to type `/translate` and then send English words one by one, so I can quickly learn their Russian and Kazakh meanings without typing a command prefix each time.

> **US-2:** As a user, I want to see example sentences for each word, so I can understand how the word is used in context.

> **US-3:** As a user, I want to type `/stop` to exit translate mode, so the bot stops interpreting my messages as words to translate.

> **US-4:** As a user, I want to see my translation history, so I can review words I've looked up before.

### Voice Journaling

> **US-7:** As a user, I want to send short voice notes (< 1 min) in Russian or English anytime without commands, so I can instantly capture fleeting thoughts.

> **US-8:** As a user, I want my voice notes cleaned of filler words and organized into categories and action items, so I don't have to listen back to chaotic audio.

> **US-9:** As a user, I want to download all my thoughts as a CSV file, so I can analyze them in a spreadsheet or import into my personal knowledge system.

> **US-10:** As a user, I want the bot to detect my mood and energy level from my thoughts, so I can track my emotional well-being over time.

> **US-11:** As a user, I want my action items automatically collected into an interactive task list (`/actions`), so I can check them off as I get things done.

> **US-12:** As a user, I want an AI-synthesized weekly reflection digest sent to me every Sunday or on demand (`/digest`), so I can review my accomplishments and plan ahead.

> **US-13:** As a user, I want to change a note's category after saving with a quick tap, so I can keep my journal properly organized.

> **US-14:** As a user, I want my notes automatically synced to my Google Sheet, so my data is backed up to the cloud and easily shareable.

### Access Control

> **US-5:** As an admin, I want to add new users via `/allow`, so I can grant access without restarting the bot.

> **US-6:** As an unauthorized user, I want to see a clear "Access denied" message, so I know the bot is private.

---

## 5. Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12+ |
| Bot framework | python-telegram-bot v21+ |
| AI (Translation & Words) | Google Gemini 3.7 Flash via `google-genai` SDK |
| AI (Thought Journaling & Digests) | Google Gemini 3.8 Flash (`JOURNAL_MODEL`) via `google-genai` SDK |
| Database | SQLite via `aiosqlite` |
| Cloud Sync | Google Sheets via `gspread` & `google-auth` |
| Config | python-dotenv + environment variables |
| Deployment | Docker + docker-compose on local machine |


---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Translation accuracy | Verified manually for 20 common words |
| Audio thought processing time | < 7 seconds per 1-minute audio note |
| Uptime | Bot stays running via Docker auto-restart |
| Error rate | No unhandled crashes in normal usage |

---

## 7. Out of Scope (Current Phase)

- Multi-language support beyond EN, RU, and KZ
- Paragraph translation in translation mode
- Real-time two-way voice conversation
- Inline mode (translation in other chats)
- Web dashboard
- Cloud deployment

