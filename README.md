# Aidos — Telegram AI Assistant

A personal Telegram bot that translates English words to Russian with contextual usage examples, powered by Google Gemini AI.

## Features

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
ALLOWED_USER_IDS=your_telegram_user_id
ADMIN_USER_IDS=your_telegram_user_id
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/menu` | Interactive menu |
| `/translate` | Enter translate mode |
| `/stop` | Exit translate mode |
| `/words` | Generate vocabulary |
| `/subscribe` | Subscribe to daily idioms |
| `/unsubscribe` | Unsubscribe from idioms |
| `/history` | View translation history |
| `/history words` | View generated vocabulary history |
| `/history idioms`| View daily idioms history |
| `/history clear` | Clear history |
| `/allow <id>` | *(Admin)* Grant user access |
| `/revoke <id>` | *(Admin)* Revoke user access |
| `/users` | *(Admin)* List allowed users |

## Usage Example

```
You:  /translate
Bot:  🔤 Translate mode activated! Send me any English word...

You:  resilience
Bot:  📚 resilience
      ──────────────────────────────
      🗣️ Pronunciation: [rəˈzilyəns]

      🔤 Translations:
      • устойчивость — stability, resistance
      🇰🇿 Kazakh: төзімділік
      📝 Part of speech: noun
      💬 Examples:
      1. 🇬🇧 Her resilience inspired everyone.
         🇷🇺 Её стойкость вдохновила всех.
      ...

You:  /stop
Bot:  ✅ Translate mode deactivated.

You:  /words business
Bot:  🎯 Topic: business
      📖 Advanced Words
      meticulous /məˈtɪkjələs/ (adjective, C1)
      ...
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Bot framework | python-telegram-bot 21+ |
| AI | Google Gemini 2.5 Flash (`google-genai`) |
| Database | SQLite (`aiosqlite`) |
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
├── data/                # SQLite database directory (mounted in Docker)
├── database/            # SQLite schema and models
├── handlers/            # Telegram command handlers
├── services/            # External API integrations
├── prompts/             # Gemini prompt templates
├── utils/               # Shared utilities
├── tests/               # Unit tests
├── main.py              # Entry point
├── config.py            # Configuration
├── Dockerfile
└── docker-compose.yml
```

## License

Private use only.
