# Aidos — Telegram AI Assistant

A personal Telegram bot for English language learning and spontaneous voice thought journaling, powered by Google Gemini AI.

## Features

- **Voice thought journaling** — send short voice or audio notes (< 1 min) in Russian, English, or mixed language without any command prefix. The bot filters noise/filler words, structures thoughts (Title, Category, Summary, Key Points, Action Items, Tags), and tracks **Mood** and **Energy Level**.
- **Interactive category switching** — change any note's category after saving with a single tap on `[🏷 Category]`.
- **Action items tracker** — automatic extraction of tasks into a persistent dashboard (`/actions`). Check off items with interactive checkboxes and clean completed tasks.
- **Weekly & monthly digests** — AI-synthesized executive reflection (`/digest` or `/digest monthly`) and automated weekly digest sent every Sunday, summarizing themes, accomplishments, mood trends, and recommended focus areas.
- **Google Sheets cloud sync** — automatic background append to your personal Google Sheet or bulk sync existing thoughts via `/notes sync`.
- **Notes browsing & CSV export** — view recent thoughts with `/notes` or download your entire journal as a spreadsheet-ready `.csv` file (`/notes export`).
- **Dedicated AI model** — thought processing and digests run on an independently configurable model (`JOURNAL_MODEL`, default: `gemini-3.8-flash`).
- **Session-based translation** — type `/translate`, then send words one by one
- **Rich output** — translations to Russian and Kazakh, pronunciation, examples, collocations
- **Vocabulary builder** — type `/words` to learn advanced vocabulary
- **Daily Idioms** — type `/subscribe` to get a daily idiom at 14:00 UTC
- **Translation history** — review past lookups with `/history`
- **Access control** — whitelist-only, with admin commands to manage users
- **Dockerized** — runs on your laptop with a single command

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)
- *(Optional)* Google Cloud Service Account JSON key for Google Sheets sync

### Setup

```bash
git clone <repository-url>
cd aidos

# Configure
cp .env.example .env
# Edit .env with your tokens

# Run
docker compose up -d --build
```

### `.env` Configuration

```env
TELEGRAM_BOT_TOKEN=your_token_from_botfather
GEMINI_API_KEY=your_key_from_google_ai_studio

# AI Model Configuration
GEMINI_MODEL=gemini-3.7-flash        # Language learning, vocabulary, translations
JOURNAL_MODEL=gemini-3.8-flash       # Voice transcription, structuring, mood, & digests

ALLOWED_USER_IDS=your_telegram_user_id
ADMIN_USER_IDS=your_telegram_user_id

# Optional Google Sheets Integration
GOOGLE_SHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials/service_account.json
```

### Google Sheets Setup Guide (Optional)

To sync your thoughts automatically with a Google Sheet:

1. **Google Cloud Console**: Open [Google Cloud Console](https://console.cloud.google.com/) and create a project (or use the same one as your Gemini API key).
2. **Enable APIs**: Enable both the **Google Sheets API** and the **Google Drive API** under *APIs & Services > Library*.
3. **Service Account**: Go to *IAM & Admin > Service Accounts*, click **Create Service Account**, name it (e.g. `aidos-journal`), and create it.
4. **Download JSON Key**: Click on the created service account > *Keys* > *Add Key* > *Create new key* > **JSON**. Save this file into your project at `credentials/service_account.json` (do not commit this file).
5. **Share Your Google Sheet**: Create a new Google Sheet in your Google Drive. Copy the service account's email address (e.g. `aidos-journal@your-project.iam.gserviceaccount.com`) and click **Share** on your sheet, giving that email **Editor** access.
6. **Set Environment Variables**:
   - Extract the Spreadsheet ID from the URL (`https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit`).
   - Set `GOOGLE_SHEET_ID=<SPREADSHEET_ID>` and `GOOGLE_SHEETS_CREDENTIALS_FILE=credentials/service_account.json` in your `.env`.
   - New voice notes will now automatically append to the sheet, and running `/notes sync` will backfill all existing entries!


## Commands

| Command | Description |
|---------|-------------|
| *(Send voice/audio)* | Spontaneously record thought (< 1 min) — auto-transcribed, categorized, mood & tasks extracted |
| `/notes` | View recent thoughts or access export & sync buttons |
| `/notes <id>` | View full card and details of a specific note |
| `/notes export` | Download all notes as a UTF-8 CSV file |
| `/notes sync` | Sync all thoughts to Google Sheets |
| `/actions` | Interactive task dashboard (check off pending action items) |
| `/actions all` | View all action items including completed ones |
| `/actions clear`| Clear all completed action items |
| `/digest` | Weekly AI reflection & momentum digest (last 7 days) |
| `/digest monthly`| Monthly AI reflection & momentum digest (last 30 days) |
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/menu` | Interactive menu |
| `/translate` | Enter translate mode |
| `/stop` | Exit translate mode |
| `/words` | Generate vocabulary |
| `/subscribe` | Subscribe to daily idioms |
| `/unsubscribe` | Unsubscribe from idioms |
| `/history` | View translation history |
| `/history_words` | View generated vocabulary history |
| `/history_idioms`| View daily idioms history |
| `/history clear` | Clear history |
| `/allow <id>` | *(Admin)* Grant user access |
| `/revoke <id>` | *(Admin)* Revoke user access |
| `/users` | *(Admin)* List allowed users |


## Usage Example

```
You:  (sends 25s voice note: "Эээ, нужно завтра созвониться с клиентом по новому проекту...")
Bot:  💼 Встреча с клиентом по проекту
      🏷 Work • 📅 Sep 18 14:30 • ⏱️ 25s
      🎭 Focused • ⚡ High energy
      ────────────────────────────
      Summary:
      Необходимо организовать созвон с клиентом для обсуждения деталей нового проекта.

      Key Points:
      • Созвониться завтра с клиентом
      • Обсудить скоуп и этапы проекта

      Action Items:
      ☑ Назначить звонок на завтра

      🏷 #work #client #meeting

      💬 Clean transcript:
      "Нужно завтра созвониться с клиентом по новому проекту."

      [🗑 Delete] [🏷 Category] [📥 Export CSV]

You:  /actions
Bot:  📋 Pending Action Items
      ────────────────────────────
      ⬜ #1 Назначить звонок на завтра
      [✓ #1] [📋 Show All] [🧹 Clear Done]

You:  /digest
Bot:  📊 Weekly Digest
      Thoughts analyzed: 8
      ────────────────────────────
      Executive Summary:
      High momentum week focused on business expansion and strategic alignment.
      ...
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12+ |
| Bot framework | python-telegram-bot 21+ |
| AI (Translation & Words) | Google Gemini 3.7 Flash (`google-genai`) |
| AI (Thought Journaling & Digests) | Google Gemini 3.8 Flash (`google-genai`) |
| Database | SQLite (`aiosqlite`) |
| Cloud Sync | Google Sheets (`gspread`, `google-auth`) |
| Deployment | Docker + docker-compose |



## Docker Commands

```bash
docker compose up -d --build    # Build and start
docker compose logs -f          # View logs
docker compose down             # Stop
docker compose restart          # Restart
```

## Project Structure

```
aidos/
├── data/                    # SQLite database directory (mounted in Docker)
├── database/                # SQLite connection and data models
│   ├── db.py                # Schema initialization, connection context & migrations
│   └── models.py            # User, translation, vocabulary, idiom, journal & action items CRUD
├── handlers/                # Telegram command & callback handlers
│   ├── actions.py           # /actions task dashboard & toggle callbacks
│   ├── admin.py             # Admin access control (/allow, /revoke, /users)
│   ├── core.py              # /start, /help, /menu interactive navigation
│   ├── idiom.py             # Daily idiom broadcast & subscription handlers
│   ├── journal.py           # Audio thought recorder, /notes, /digest, category & sheets handlers
│   ├── translation.py       # Session-based word translation conversation
│   └── vocabulary.py        # /words advanced vocabulary generator
├── services/                # External API integrations
│   ├── gemini_service.py    # Google Gemini client & JSON response parser
│   ├── journal_service.py   # Audio thought structuring, CSV generator & digest AI
│   └── sheets_service.py    # Non-blocking Google Sheets sync via gspread
├── prompts/                 # Specialized system prompts for Gemini
│   ├── idiom.py             # Daily idiom generation prompt
│   ├── journal.py           # Chaotic audio transcription & reflection digest prompts
│   ├── translation.py       # English-to-Russian/Kazakh translation prompt
│   └── vocabulary.py        # Advanced vocabulary generation prompt
├── utils/                   # Shared utilities, decorators & formatters
│   ├── constants.py         # Static message templates, emojis & menus
│   ├── decorators.py        # @restricted, @send_typing, @rate_limit
│   └── formatting.py        # HTML formatting for translation cards, notes & digests
├── tests/                   # 54 automated pytest unit & integration tests
├── main.py                  # Bot entry point, startup migrations & APScheduler jobs
├── config.py                # Configuration dataclass & .env loader
├── Dockerfile               # Production Docker container
└── docker-compose.yml       # Container orchestration & volume bindings
```

## License

Private use only.
