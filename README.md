# 💰 Budget Bot

A Telegram bot that acts as your friendly personal budget assistant. Track expenses, set budgets, and get AI-powered spending advice — all through natural conversation.

## ✨ Features

- 💬 **Natural language input** — talk to the bot like a friend ("bought coffee for 200")
- 📊 **Budget tracking** — set monthly budgets and monitor spending
- 🏷️ **Auto-categorization** — expenses are automatically sorted into categories (food, transport, entertainment, etc.)
- ⚠️ **Smart alerts** — get warnings when approaching or exceeding your budget
- 📋 **Expense history** — view your recent transactions
- 🤖 **AI analysis** — get personalized financial tips powered by a local LLM (via Ollama)
- 🧹 **Clear history** — delete all expenses with confirmation

## 🛠 Tech Stack

- **Python 3.13+**
- **[aiogram](https://docs.aiogram.dev/)** — Telegram Bot framework
- **[asyncpg](https://magicstack.github.io/asyncpg/)** — Async PostgreSQL driver
- **[OpenAI SDK](https://github.com/openai/openai-python)** — For LLM integration (Ollama)
- **PostgreSQL** — Database
- **[Ollama](https://ollama.ai/)** — Local LLM runner (`qwen2.5:1.5b` model)

## 📋 Requirements

- Python 3.13 or higher
- PostgreSQL database
- [Ollama](https://ollama.ai/) running locally with the `qwen2.5:1.5b` model

## 🚀 Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd budget_bot
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

Create a database and user:

```sql
CREATE USER bot_user WITH PASSWORD 'bot_pass';
CREATE DATABASE budget_bot OWNER bot_user;
GRANT ALL PRIVILEGES ON DATABASE budget_bot TO bot_user;
```

Or update the `DATABASE_URL` environment variable to match your configuration.

### 5. Set up Ollama

Install [Ollama](https://ollama.ai/) and pull the required model:

```bash
ollama pull qwen2.5:1.5b
```

Ensure Ollama is running on `http://localhost:11434` (default).

### 6. Configure the bot

Set your Telegram Bot token:

```bash
export BOT_TOKEN="your_telegram_bot_token_here"
```

> Get a token from [@BotFather](https://t.me/BotFather) on Telegram.

### 7. Run the bot

```bash
python bot.py
```

## 💬 Usage Examples

Once the bot is running, start a conversation with `/start` and try these:

| You say | Bot responds |
|---------|--------------|
| `/start` | Welcome message with instructions |
| `/setbudget 15000` | Sets your monthly budget |
| `bought coffee for 200` | Logs 200 as a food expense |
| `paid 50 for taxi` | Logs 50 as a transport expense |
| `how much left?` | Shows remaining budget |
| `show history` | Lists recent expenses |
| `analyze spending` | Gets AI-powered financial advice |
| `/clear` | Clears all expenses (with confirmation) |

## 📁 Project Structure

```
budget_bot/
├── bot.py           # Main bot logic, handlers, and AI integration
├── database.py      # Database models and async operations
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## ⚙️ Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `BOT_TOKEN` | `YOUR_TOKEN_HERE` | Telegram Bot API token |
| `DATABASE_URL` | `postgresql://bot_user:bot_pass@localhost:5432/budget_bot` | PostgreSQL connection string |

## 🏷️ Expense Categories

The bot automatically categorizes expenses based on keywords:

| Category | Keywords |
|----------|----------|
| 🍔 **food** | food, coffee, tea, restaurant, cafe, pizza, burger, sushi |
| 🚗 **transport** | taxi, bus, metro, uber, tram, fuel, gas |
| 👕 **clothes** | clothes, jacket, tshirt, jeans, shoes |
| 📚 **study** | book, course, notebook, pen, printer |
| 🎮 **entertainment** | movie, game, concert, club, netflix, spotify |
| 💊 **health** | pharmacy, medicine, doctor, hospital, vitamins |
| 📦 **other** | anything else |

## 🤝 Contributing

Pull requests are welcome! Feel free to submit improvements, bug fixes, or new features.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
