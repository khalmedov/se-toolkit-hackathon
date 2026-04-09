import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bot_user:bot_pass@localhost:5432/budget_bot")

pool = None

async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                budget INTEGER DEFAULT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                amount INTEGER NOT NULL,
                category TEXT NOT NULL DEFAULT 'other',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

async def get_or_create_user(user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not row:
            await conn.execute("INSERT INTO users (user_id) VALUES ($1)", user_id)
            return {"user_id": user_id, "budget": None}
        return dict(row)

async def set_budget(user_id: int, budget: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET budget = $1 WHERE user_id = $2",
            budget, user_id
        )

async def add_expense(user_id: int, amount: int, category: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO expenses (user_id, amount, category) VALUES ($1, $2, $3)",
            user_id, amount, category
        )

async def get_expenses(user_id: int):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT amount, category, created_at FROM expenses WHERE user_id = $1 ORDER BY created_at DESC",
            user_id
        )
        return [dict(r) for r in rows]

async def get_total_spent(user_id: int) -> int:
    async with pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = $1",
            user_id
        )
        return int(result)
