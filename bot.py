import asyncio
import os
import re
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from openai import OpenAI
import database as db

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="dummy",
)

CATEGORY_KEYWORDS = {
    "food": ["food", "coffee", "tea", "restaurant", "cafe", "pizza", "burger", "sushi", "snack"],
    "transport": ["taxi", "bus", "metro", "uber", "tram", "fuel", "gas"],
    "clothes": ["clothes", "jacket", "tshirt", "jeans", "shoes"],
    "study": ["book", "course", "notebook", "pen", "printer"],
    "entertainment": ["movie", "game", "concert", "club", "netflix", "spotify"],
    "health": ["pharmacy", "medicine", "doctor", "hospital", "vitamins"],
}

EXPENSE_TRIGGERS = [
    "bought", "spent", "paid", "cost", "spent", "gave", "took"
]

BALANCE_TRIGGERS = ["balance", "left", "remaining", "how much"]
HISTORY_TRIGGERS = ["history", "list", "expenses"]
ANALYZE_TRIGGERS = ["analyze", "analysis", "advice", "recommend"]
BUDGET_TRIGGERS = ["budget", "limit", "monthly"]

CLEAR_CONFIRM = {}


def detect_category(text: str) -> str:
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "other"


def detect_expense(text: str):
    has_trigger = any(w in text for w in EXPENSE_TRIGGERS)
    match = re.search(r'(\d+)', text)
    if has_trigger and match:
        amount = int(match.group(1))
        category = detect_category(text)
        return amount, category
    return None


def ai(prompt: str) -> str:
    response = client.chat.completions.create(
        model="qwen2.5:1.5b",
        messages=[
            {"role": "system", "content": "Always respond in English."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await db.get_or_create_user(message.from_user.id)
    await message.answer(
        "👋 Hi! I'm your budget assistant 💰\n\n"
        "Talk to me like a friend:\n"
        "- 'monthly budget 15000'\n"
        "- 'bought coffee for 200'\n"
        "- 'how much left?'\n"
        "- 'show history'\n"
        "- 'analyze spending'\n\n"
        "Commands:\n"
        "/setbudget 15000 — set budget\n"
        "/balance — check balance\n"
        "/history — show history\n"
        "/analyze — AI analysis\n"
        "/clear — clear history"
    )


@dp.message(Command("setbudget"))
async def cmd_setbudget(message: Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Use: /setbudget 15000")
        return
    user_id = message.from_user.id
    await db.get_or_create_user(user_id)
    await db.set_budget(user_id, int(args[1]))
    await message.answer(f"✅ Budget set: {args[1]}")


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    await show_balance(message)


@dp.message(Command("history"))
async def cmd_history(message: Message):
    await show_history(message)


@dp.message(Command("analyze"))
async def cmd_analyze(message: Message):
    await show_analyze(message)


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    user_id = message.from_user.id
    CLEAR_CONFIRM[user_id] = True
    await message.answer("⚠️ Are you sure you want to delete all expenses?\nReply 'yes' to confirm.")


@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    await db.get_or_create_user(user_id)
    text = message.text.lower().strip()

    # Clear confirm
    if CLEAR_CONFIRM.get(user_id):
        if text in ["yes", "ok"]:
            async with db.pool.acquire() as conn:
                await conn.execute("DELETE FROM expenses WHERE user_id = $1", user_id)
            CLEAR_CONFIRM.pop(user_id, None)
            await message.answer("🗑️ History cleared!")
        else:
            CLEAR_CONFIRM.pop(user_id, None)
            await message.answer("Cancelled.")
        return

    # Budget
    if any(w in text for w in BUDGET_TRIGGERS):
        match = re.search(r'(\d+)', text)
        if match:
            budget = int(match.group(1))
            await db.set_budget(user_id, budget)
            await message.answer(f"✅ Budget set: {budget}")
            return

    # Balance
    if any(w in text for w in BALANCE_TRIGGERS):
        await show_balance(message)
        return

    # History
    if any(w in text for w in HISTORY_TRIGGERS):
        await show_history(message)
        return

    # Analyze
    if any(w in text for w in ANALYZE_TRIGGERS):
        await show_analyze(message)
        return

    # Expense
    result = detect_expense(text)
    if result:
        amount, category = result
        await db.add_expense(user_id, amount, category)
        user = await db.get_or_create_user(user_id)
        total_spent = await db.get_total_spent(user_id)

        response = f"✅ Added: {amount} — {category}\n"
        response += f"💸 Total spent: {total_spent}"

        if user["budget"]:
            remaining = user["budget"] - total_spent
            percent = int(total_spent / user["budget"] * 100)

            if remaining < 0:
                response += f"\n🚨 Over budget by {abs(remaining)}!"
            elif percent >= 80:
                response += f"\n⚠️ {remaining} left — be careful!"
            elif percent >= 50:
                response += f"\n🟡 {remaining} left — stay focused!"
            else:
                response += f"\n✅ {remaining} left 👍"

        await message.answer(response)
        return

    # Just number
    if re.fullmatch(r'\d+', text):
        await message.answer(
            f"{text} — what did you spend it on?\nExample: 'bought food for {text}'"
        )
        return

    # AI chat
    chat_prompt = (
        "You are a friendly student budget assistant. "
        "Respond very briefly (1-2 sentences) with a bit of humor.\n"
        f"User said: \"{message.text}\""
    )

    reply = ai(chat_prompt)
    await message.answer(reply)


async def show_balance(message: Message):
    user_id = message.from_user.id
    user = await db.get_or_create_user(user_id)
    total_spent = await db.get_total_spent(user_id)

    if total_spent == 0 and not user["budget"]:
        await message.answer("No data yet. Set a budget with /setbudget 15000")
        return

    if user["budget"]:
        remaining = user["budget"] - total_spent
        percent = int(total_spent / user["budget"] * 100)

        await message.answer(
            f"🎯 Budget: {user['budget']}\n"
            f"💸 Spent: {total_spent}\n"
            f"✅ Left: {remaining}\n"
            f"{percent}% used"
        )
    else:
        await message.answer(f"💸 Spent: {total_spent}\nNo budget set.")


async def show_history(message: Message):
    user_id = message.from_user.id
    expenses = await db.get_expenses(user_id)

    if not expenses:
        await message.answer("No expenses yet.")
        return

    response = "📋 Expense history:\n\n"
    for i, e in enumerate(expenses[:10], 1):
        date_str = e["created_at"].strftime("%d.%m %H:%M")
        response += f"{i}. {date_str} — {e['amount']} ({e['category']})\n"

    total = sum(e["amount"] for e in expenses)
    response += f"\n💰 Total: {total}"
    await message.answer(response)


async def show_analyze(message: Message):
    user_id = message.from_user.id
    user = await db.get_or_create_user(user_id)
    expenses = await db.get_expenses(user_id)
    total_spent = await db.get_total_spent(user_id)

    if not expenses:
        await message.answer("No expenses to analyze.")
        return

    await message.answer("🤖 Analyzing...")

    category_totals = {}
    for e in expenses:
        cat = e["category"]
        category_totals[cat] = category_totals.get(cat, 0) + e["amount"]

    summary = f"Budget: {user['budget']}, spent: {total_spent}"
    summary += "\nCategories: " + ", ".join(f"{k}: {v}" for k, v in category_totals.items())

    prompt = (
        "Give exactly 3 short financial tips in English. "
        "Each must be one sentence with numbers. No intro.\n\n"
        f"{summary}"
    )

    advice = ai(prompt)
    await message.answer(f"🤖 Analysis:\n\n{advice}")


async def main():
    await db.init_db()
    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())