# database.py - Database operations with aiosqlite

import aiosqlite
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

DATABASE_NAME = "finance_bot.db"

logger = logging.getLogger(__name__)


async def init_db():
    """Initialize the database and create tables."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'en',
                    main_currency TEXT DEFAULT 'UZS',
                    created_at TEXT
                )
            ''')
            
            # Transactions table (expenses and income)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    goal TEXT,
                    amount REAL,
                    currency TEXT,
                    date TEXT,
                    month TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Debts table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    amount REAL,
                    currency TEXT,
                    type TEXT,
                    date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Utilities table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS utilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    utility_type TEXT,
                    amount REAL,
                    currency TEXT,
                    date TEXT,
                    month TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            await db.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


# ===================== USER OPERATIONS =====================

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


async def create_user(user_id: int, language: str = "en"):
    """Create a new user."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, language, main_currency, created_at) VALUES (?, ?, ?, ?)",
                (user_id, language, "UZS", datetime.now().isoformat())
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Error creating user {user_id}: {e}")


async def update_user_language(user_id: int, language: str):
    """Update user's language."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute(
                "UPDATE users SET language = ? WHERE user_id = ?",
                (language, user_id)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Error updating language for user {user_id}: {e}")


async def update_main_currency(user_id: int, currency: str):
    """Update user's main currency."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute(
                "UPDATE users SET main_currency = ? WHERE user_id = ?",
                (currency, user_id)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Error updating main currency for user {user_id}: {e}")


async def get_user_language(user_id: int) -> str:
    """Get user's language."""
    user = await get_user(user_id)
    return user["language"] if user else "en"


async def get_user_main_currency(user_id: int) -> str:
    """Get user's main currency."""
    user = await get_user(user_id)
    return user["main_currency"] if user else "UZS"


# ===================== TRANSACTION OPERATIONS =====================

async def add_transaction(user_id: int, trans_type: str, goal: str, amount: float, currency: str):
    """Add a new transaction (expense or income)."""
    try:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M")
        month_str = now.strftime("%Y-%m")
        
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute(
                """INSERT INTO transactions (user_id, type, goal, amount, currency, date, month)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, trans_type, goal, amount, currency, date_str, month_str)
            )
            await db.commit()
        return date_str
    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        return None


async def get_all_transactions(user_id: int) -> List[Dict[str, Any]]:
    """Get all transactions for a user."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return []


async def get_transactions_by_month(user_id: int, month: str) -> List[Dict[str, Any]]:
    """Get transactions for a specific month."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM transactions WHERE user_id = ? AND month = ? ORDER BY date DESC",
                (user_id, month)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting transactions by month: {e}")
        return []


async def get_transactions_by_date(user_id: int, month: str, day: int) -> List[Dict[str, Any]]:
    """Get transactions for a specific date."""
    try:
        date_pattern = f"{month}-{day:02d}%"
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM transactions WHERE user_id = ? AND date LIKE ? ORDER BY date DESC",
                (user_id, date_pattern)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting transactions by date: {e}")
        return []


async def get_available_months(user_id: int) -> List[str]:
    """Get all available months for a user."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            async with db.execute(
                "SELECT DISTINCT month FROM transactions WHERE user_id = ? ORDER BY month DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error getting available months: {e}")
        return []


# ===================== DEBT OPERATIONS =====================

async def add_debt(user_id: int, name: str, amount: float, currency: str, debt_type: str):
    """Add a new debt."""
    try:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute(
                """INSERT INTO debts (user_id, name, amount, currency, type, date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, name, amount, currency, debt_type, date_str)
            )
            await db.commit()
        return date_str
    except Exception as e:
        logger.error(f"Error adding debt: {e}")
        return None


async def get_all_debts(user_id: int) -> List[Dict[str, Any]]:
    """Get all debts for a user."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM debts WHERE user_id = ? ORDER BY date DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting debts: {e}")
        return []


async def get_debt_by_id(debt_id: int) -> Optional[Dict[str, Any]]:
    """Get a debt by ID."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM debts WHERE id = ?", (debt_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting debt: {e}")
        return None


async def update_debt_amount(debt_id: int, new_amount: float):
    """Update a debt's amount."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute(
                "UPDATE debts SET amount = ? WHERE id = ?",
                (new_amount, debt_id)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Error updating debt: {e}")


async def delete_debt(debt_id: int):
    """Delete a debt."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
            await db.commit()
    except Exception as e:
        logger.error(f"Error deleting debt: {e}")


# ===================== UTILITY OPERATIONS =====================

async def add_utility(user_id: int, utility_type: str, amount: float, currency: str):
    """Add a new utility payment."""
    try:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M")
        month_str = now.strftime("%Y-%m")
        
        async with aiosqlite.connect(DATABASE_NAME) as db:
            await db.execute(
                """INSERT INTO utilities (user_id, utility_type, amount, currency, date, month)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, utility_type, amount, currency, date_str, month_str)
            )
            await db.commit()
        return date_str
    except Exception as e:
        logger.error(f"Error adding utility: {e}")
        return None


async def get_utilities_by_month(user_id: int, month: str) -> List[Dict[str, Any]]:
    """Get utilities for a specific month."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM utilities WHERE user_id = ? AND month = ? ORDER BY date DESC",
                (user_id, month)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting utilities by month: {e}")
        return []


async def get_utilities_by_date(user_id: int, month: str, day: int) -> List[Dict[str, Any]]:
    """Get utilities for a specific date."""
    try:
        date_pattern = f"{month}-{day:02d}%"
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM utilities WHERE user_id = ? AND date LIKE ? ORDER BY date DESC",
                (user_id, date_pattern)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting utilities by date: {e}")
        return []


async def get_all_utilities(user_id: int) -> List[Dict[str, Any]]:
    """Get all utilities for a user."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM utilities WHERE user_id = ? ORDER BY date DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all utilities: {e}")
        return []


async def get_utility_months(user_id: int) -> List[str]:
    """Get all available months for utilities."""
    try:
        async with aiosqlite.connect(DATABASE_NAME) as db:
            async with db.execute(
                "SELECT DISTINCT month FROM utilities WHERE user_id = ? ORDER BY month DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"Error getting utility months: {e}")
        return []
