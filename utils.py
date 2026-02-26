import aiohttp
import os
from datetime import datetime
from models import get_session, Transaction, Debt, Utility, User

EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "your_exchange_api_key")
ADSGRAM_URL = os.getenv("ADSGRAM_URL", "https://adsgram.ai/your_link")

_rate_cache = {}

async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get real-time exchange rate using exchangerate-api."""
    if from_currency == to_currency:
        return 1.0
    
    cache_key = f"{from_currency}_{to_currency}"
    cached = _rate_cache.get(cache_key)
    if cached and (datetime.utcnow() - cached["time"]).seconds < 3600:
        return cached["rate"]
    
    try:
        url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/{from_currency}/{to_currency}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                if data.get("result") == "success":
                    rate = data["conversion_rate"]
                    _rate_cache[cache_key] = {"rate": rate, "time": datetime.utcnow()}
                    return rate
    except Exception:
        pass
    return 1.0

async def convert_amount(amount: float, from_currency: str, to_currency: str) -> float:
    rate = await get_exchange_rate(from_currency, to_currency)
    return round(amount * rate, 2)

def get_user(telegram_id: int) -> User:
    session = get_session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user

def get_or_create_user(telegram_id: int) -> User:
    session = get_session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        session.add(user)
        session.commit()
        session.refresh(user)
    session.close()
    return user

def update_user(telegram_id: int, **kwargs):
    session = get_session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        for k, v in kwargs.items():
            setattr(user, k, v)
        session.commit()
    session.close()

def save_transaction(user_id: int, tx_type: str, amount: float, currency: str, description: str):
    session = get_session()
    tx = Transaction(user_id=user_id, type=tx_type, amount=amount,
                     currency=currency, description=description)
    session.add(tx)
    session.commit()
    session.close()

async def get_stats(user_id: int, main_currency: str) -> dict:
    session = get_session()
    txs = session.query(Transaction).filter_by(user_id=user_id).all()
    session.close()

    total_income = 0.0
    total_expense = 0.0

    for tx in txs:
        converted = await convert_amount(tx.amount, tx.currency, main_currency)
        if tx.type == "income":
            total_income += converted
        else:
            total_expense += converted

    return {
        "income": round(total_income, 2),
        "expense": round(total_expense, 2),
        "net": round(total_income - total_expense, 2),
    }

async def get_monthly_report(user_id: int, year: int, month: int, main_currency: str) -> dict:
    session = get_session()
    txs = session.query(Transaction).filter_by(user_id=user_id).filter(
        Transaction.date >= datetime(year, month, 1),
        Transaction.date < datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    ).all()
    utilities = session.query(Utility).filter_by(user_id=user_id).filter(
        Utility.date >= datetime(year, month, 1),
        Utility.date < datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
    ).all()
    session.close()

    income = 0.0
    expense = 0.0
    for tx in txs:
        converted = await convert_amount(tx.amount, tx.currency, main_currency)
        if tx.type == "income":
            income += converted
        else:
            expense += converted
    for u in utilities:
        converted = await convert_amount(u.amount, u.currency, main_currency)
        expense += converted

    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net": round(income - expense, 2),
    }

async def get_daily_report(user_id: int, year: int, month: int, day: int, main_currency: str) -> list:
    session = get_session()
    start = datetime(year, month, day)
    end = datetime(year, month, day, 23, 59, 59)
    txs = session.query(Transaction).filter_by(user_id=user_id).filter(
        Transaction.date >= start, Transaction.date <= end
    ).all()
    session.close()

    result = []
    for tx in txs:
        converted = await convert_amount(tx.amount, tx.currency, main_currency)
        emoji = "💰" if tx.type == "income" else "💸"
        result.append(f"{emoji} {tx.description}: {converted} {main_currency}")
    return result

def save_debt(user_id: int, person_name: str, amount: float, currency: str, debt_type: str):
    session = get_session()
    debt = Debt(user_id=user_id, person_name=person_name, amount=amount,
                currency=currency, debt_type=debt_type)
    session.add(debt)
    session.commit()
    session.close()

def get_debts(user_id: int, debt_type: str = None) -> list:
    session = get_session()
    q = session.query(Debt).filter_by(user_id=user_id, is_paid=False)
    if debt_type:
        q = q.filter_by(debt_type=debt_type)
    debts = q.all()
    result = [(d.id, d.person_name, d.amount, d.currency, d.debt_type) for d in debts]
    session.close()
    return result

def pay_debt(debt_id: int, amount: float = None):
    session = get_session()
    debt = session.query(Debt).filter_by(id=debt_id).first()
    if debt:
        if amount is None or amount >= debt.amount:
            debt.is_paid = True
        else:
            debt.amount -= amount
        session.commit()
    session.close()

def save_utility(user_id: int, category: str, amount: float, currency: str, description: str):
    session = get_session()
    u = Utility(user_id=user_id, category=category, amount=amount,
                currency=currency, description=description)
    session.add(u)
    session.commit()
    session.close()

async def get_utility_stats(user_id: int, main_currency: str) -> dict:
    session = get_session()
    utilities = session.query(Utility).filter_by(user_id=user_id).all()
    session.close()

    by_category = {}
    for u in utilities:
        converted = await convert_amount(u.amount, u.currency, main_currency)
        by_category[u.category] = by_category.get(u.category, 0) + converted
    return by_category

def format_currency(amount: float, currency: str) -> str:
    symbols = {"USD": "$", "RUB": "₽", "CNY": "¥", "EUR": "€", "UZS": "so'm",
               "KZT": "₸", "KGS": "с", "TJS": "SM", "TRY": "₺", "INR": "₹", "SAR": "﷼"}
    sym = symbols.get(currency, currency)
    return f"{amount:,.2f} {sym}"
