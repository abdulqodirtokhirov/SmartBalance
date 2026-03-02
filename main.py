# main.py - Telegram Bot using Aiogram 3

import asyncio
import logging
import re
import aiohttp
from datetime import datetime
from typing import Dict, Any

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, 
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from strings import get_text, get_utility_name, UTILITY_TYPES

# ===================== CONFIGURATION =====================

import os 
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Exchange rates (fallback values, updated from API)
EXCHANGE_RATES = {
    "UZS": 1,
    "USD": 12500,
    "RUB": 135,
    "CNY": 1750
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


# ===================== FSM STATES =====================

class UserStates(StatesGroup):
    # Language
    selecting_language = State()
    
    # Transactions
    entering_expense = State()
    entering_income = State()
    selecting_expense_currency = State()
    selecting_income_currency = State()
    
    # Daily report
    selecting_report_month = State()
    entering_report_day = State()
    
    # Debts
    entering_debt_owed_to_me = State()
    entering_debt_i_owe = State()
    selecting_debt_currency = State()
    entering_payment_amount = State()
    
    # Utilities
    selecting_utility_type = State()
    entering_utility_amount = State()
    selecting_utility_currency = State()
    selecting_utility_month = State()
    entering_utility_day = State()
    
    # Converter
    selecting_convert_currency = State()
    entering_convert_amount = State()


# ===================== KEYBOARDS =====================

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get language selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])


def get_main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text(lang, "btn_expenses")),
                KeyboardButton(text=get_text(lang, "btn_income"))
            ],
            [
                KeyboardButton(text=get_text(lang, "btn_statistics")),
                KeyboardButton(text=get_text(lang, "btn_monthly_report"))
            ],
            [
                KeyboardButton(text=get_text(lang, "btn_daily_report")),
                KeyboardButton(text=get_text(lang, "btn_debts"))
            ],
            [
                KeyboardButton(text=get_text(lang, "btn_utilities")),
                KeyboardButton(text=get_text(lang, "btn_converter"))
            ]
        ],
        resize_keyboard=True
    )


def get_currency_keyboard(prefix: str = "curr") -> InlineKeyboardMarkup:
    """Get currency selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 UZS", callback_data=f"{prefix}_UZS"),
            InlineKeyboardButton(text="🇺🇸 USD", callback_data=f"{prefix}_USD")
        ],
        [
            InlineKeyboardButton(text="🇷🇺 RUB", callback_data=f"{prefix}_RUB"),
            InlineKeyboardButton(text="🇨🇳 CNY", callback_data=f"{prefix}_CNY")
        ]
    ])


def get_debts_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Get debts menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "btn_owed_to_me"), callback_data="debt_owed_to_me")],
        [InlineKeyboardButton(text=get_text(lang, "btn_i_owe"), callback_data="debt_i_owe")],
        [InlineKeyboardButton(text=get_text(lang, "btn_debt_list"), callback_data="debt_list")],
        [InlineKeyboardButton(text=get_text(lang, "btn_main_menu"), callback_data="main_menu")]
    ])


def get_utilities_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Get utilities menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "btn_add_utility"), callback_data="utility_add")],
        [InlineKeyboardButton(text=get_text(lang, "btn_monthly_utilities"), callback_data="utility_monthly")],
        [InlineKeyboardButton(text=get_text(lang, "btn_daily_utilities"), callback_data="utility_daily")],
        [InlineKeyboardButton(text=get_text(lang, "btn_utility_stats"), callback_data="utility_stats")],
        [InlineKeyboardButton(text=get_text(lang, "btn_main_menu"), callback_data="main_menu")]
    ])


def get_utility_types_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Get utility types keyboard."""
    buttons = []
    for util_type in UTILITY_TYPES.keys():
        buttons.append([InlineKeyboardButton(
            text=get_utility_name(lang, util_type),
            callback_data=f"utiltype_{util_type}"
        )])
    buttons.append([InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="utilities_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_converter_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Get converter menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "btn_convert"), callback_data="convert_start")],
        [InlineKeyboardButton(text=get_text(lang, "btn_main_currency"), callback_data="main_currency")],
        [InlineKeyboardButton(text=get_text(lang, "btn_main_menu"), callback_data="main_menu")]
    ])


def get_months_keyboard(months: list, prefix: str = "month") -> InlineKeyboardMarkup:
    """Get months selection keyboard."""
    buttons = []
    for i in range(0, len(months), 2):
        row = [InlineKeyboardButton(text=months[i], callback_data=f"{prefix}_{months[i]}")]
        if i + 1 < len(months):
            row.append(InlineKeyboardButton(text=months[i + 1], callback_data=f"{prefix}_{months[i + 1]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_days_keyboard(prefix: str = "day", lang: str = "en") -> InlineKeyboardMarkup:
    """Get days selection keyboard (1-31)."""
    buttons = []
    # Create rows of 7 days each
    for row_start in range(1, 32, 7):
        row = []
        for day in range(row_start, min(row_start + 7, 32)):
            row.append(InlineKeyboardButton(text=str(day), callback_data=f"{prefix}_{day}"))
        buttons.append(row)
    # Add back button
    buttons.append([InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard(lang: str, callback: str = "main_menu") -> InlineKeyboardMarkup:
    """Get back button keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "btn_back"), callback_data=callback)]
    ])


# ===================== UTILITY FUNCTIONS =====================

async def get_exchange_rates():
    """Fetch exchange rates from CBU API."""
    global EXCHANGE_RATES
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cbu.uz/ru/arkhiv-kursov-valyut/json/") as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data:
                        if item["Ccy"] == "USD":
                            EXCHANGE_RATES["USD"] = float(item["Rate"])
                        elif item["Ccy"] == "RUB":
                            EXCHANGE_RATES["RUB"] = float(item["Rate"])
                        elif item["Ccy"] == "CNY":
                            EXCHANGE_RATES["CNY"] = float(item["Rate"])
                    logger.info(f"Exchange rates updated: {EXCHANGE_RATES}")
    except Exception as e:
        logger.error(f"Error fetching exchange rates: {e}")


def convert_to_main_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert amount from one currency to another."""
    try:
        # First convert to UZS
        amount_in_uzs = amount * EXCHANGE_RATES.get(from_currency, 1)
        # Then convert to target currency
        if to_currency == "UZS":
            return amount_in_uzs
        return amount_in_uzs / EXCHANGE_RATES.get(to_currency, 1)
    except Exception as e:
        logger.error(f"Error converting currency: {e}")
        return amount


def format_number(num: float) -> str:
    """Format number with thousand separators."""
    return f"{num:,.2f}".replace(",", " ")


async def get_lang(state: FSMContext, user_id: int) -> str:
    """Get user's language from state or database."""
    data = await state.get_data()
    lang = data.get("language")
    if not lang:
        lang = await db.get_user_language(user_id)
        await state.update_data(language=lang)
    return lang


# ===================== HANDLERS =====================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    try:
        user_id = message.from_user.id
        await db.create_user(user_id)
        await state.set_state(UserStates.selecting_language)
        await message.answer(
            "🌐 Please select a language / Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
            reply_markup=get_language_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer("An error occurred. Please try again.")


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Handle language selection."""
    try:
        await callback.answer()
        lang = callback.data.split("_")[1]
        user_id = callback.from_user.id
        
        await db.update_user_language(user_id, lang)
        await state.update_data(language=lang)
        await state.clear()
        
        await callback.message.edit_text(get_text(lang, "language_selected"))
        await callback.message.answer(
            get_text(lang, "welcome") + "\n\n" + get_text(lang, "main_menu"),
            reply_markup=get_main_menu_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Error in language selection: {e}")
        await callback.message.answer("An error occurred. Please try again.")


@router.callback_query(F.data == "main_menu")
async def process_main_menu(callback: CallbackQuery, state: FSMContext):
    """Handle main menu callback."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        await state.clear()
        await state.update_data(language=lang)
        await callback.message.edit_text(get_text(lang, "main_menu"))
    except Exception as e:
        logger.error(f"Error in main menu: {e}")


# ===================== EXPENSES/INCOME HANDLERS =====================

@router.message(F.text.in_([
    "💸 Xarajatlar", "💸 Расходы", "💸 Expenses",
    "💰 Daromad", "💰 Доходы", "💰 Income"
]))
async def process_transaction_button(message: Message, state: FSMContext):
    """Handle expense/income buttons."""
    try:
        lang = await get_lang(state, message.from_user.id)
        text = message.text
        
        if "💸" in text:  # Expenses
            await state.set_state(UserStates.entering_expense)
            await state.update_data(transaction_type="expense")
        else:  # Income
            await state.set_state(UserStates.entering_income)
            await state.update_data(transaction_type="income")
        
        await message.answer(get_text(lang, "enter_amount_goal"))
    except Exception as e:
        logger.error(f"Error in transaction button: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.message(UserStates.entering_expense)
@router.message(UserStates.entering_income)
async def process_transaction_input(message: Message, state: FSMContext):
    """Handle transaction input."""
    try:
        lang = await get_lang(state, message.from_user.id)
        text = message.text.strip()
        
        # Parse input: "Goal Amount" or "Amount Goal"
        match = re.match(r'^(.+?)\s+(\d+(?:[.,]\d+)?)$|^(\d+(?:[.,]\d+)?)\s+(.+)$', text)
        if not match:
            await message.answer(get_text(lang, "invalid_format"))
            return
        
        if match.group(1) and match.group(2):
            goal = match.group(1)
            amount = float(match.group(2).replace(",", "."))
        else:
            amount = float(match.group(3).replace(",", "."))
            goal = match.group(4)
        
        await state.update_data(goal=goal, amount=amount)
        await message.answer(
            get_text(lang, "select_currency"),
            reply_markup=get_currency_keyboard("trans")
        )
    except Exception as e:
        logger.error(f"Error in transaction input: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data.startswith("trans_"))
async def process_transaction_currency(callback: CallbackQuery, state: FSMContext):
    """Handle transaction currency selection."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        currency = callback.data.split("_")[1]
        
        data = await state.get_data()
        goal = data.get("goal")
        amount = data.get("amount")
        trans_type = data.get("transaction_type")
        
        date = await db.add_transaction(
            callback.from_user.id,
            trans_type,
            goal,
            amount,
            currency
        )
        
        if trans_type == "expense":
            msg_key = "expense_saved"
        else:
            msg_key = "income_saved"
        
        await callback.message.edit_text(
            get_text(lang, msg_key).format(
                goal=goal,
                amount=format_number(amount),
                currency=currency,
                date=date
            )
        )
        await state.clear()
        await state.update_data(language=lang)
    except Exception as e:
        logger.error(f"Error in transaction currency: {e}")
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.answer(get_text(lang, "error_message"))


# ===================== STATISTICS HANDLERS =====================

@router.message(F.text.in_(["📊 Statistika", "📊 Статистика", "📊 Statistics"]))
async def process_statistics(message: Message, state: FSMContext):
    """Handle statistics button."""
    try:
        lang = await get_lang(state, message.from_user.id)
        user_id = message.from_user.id
        
        transactions = await db.get_all_transactions(user_id)
        main_currency = await db.get_user_main_currency(user_id)
        
        if not transactions:
            await message.answer(get_text(lang, "no_data"))
            return
        
        await get_exchange_rates()
        
        total_income = 0
        total_expenses = 0
        
        for trans in transactions:
            converted = convert_to_main_currency(
                trans["amount"],
                trans["currency"],
                main_currency
            )
            if trans["type"] == "income":
                total_income += converted
            else:
                total_expenses += converted
        
        net_profit = total_income - total_expenses
        
        text = get_text(lang, "statistics_title")
        text += get_text(lang, "total_income").format(
            amount=format_number(total_income),
            currency=main_currency
        ) + "\n"
        text += get_text(lang, "total_expenses").format(
            amount=format_number(total_expenses),
            currency=main_currency
        ) + "\n"
        text += get_text(lang, "net_profit").format(
            amount=format_number(net_profit),
            currency=main_currency
        )
        
        await message.answer(text)
    except Exception as e:
        logger.error(f"Error in statistics: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


# ===================== MONTHLY REPORT HANDLERS =====================

@router.message(F.text.in_(["📅 Oylik hisobot", "📅 Месячный отчет", "📅 Monthly Report"]))
async def process_monthly_report(message: Message, state: FSMContext):
    """Handle monthly report button."""
    try:
        lang = await get_lang(state, message.from_user.id)
        user_id = message.from_user.id
        
        months = await db.get_available_months(user_id)
        
        if not months:
            await message.answer(get_text(lang, "no_months"))
            return
        
        await message.answer(
            get_text(lang, "select_month"),
            reply_markup=get_months_keyboard(months, "monthly")
        )
    except Exception as e:
        logger.error(f"Error in monthly report: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data.startswith("monthly_"))
async def process_monthly_selection(callback: CallbackQuery, state: FSMContext):
    """Handle month selection for monthly report."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        month = callback.data.replace("monthly_", "")
        
        transactions = await db.get_transactions_by_month(callback.from_user.id, month)
        main_currency = await db.get_user_main_currency(callback.from_user.id)
        
        if not transactions:
            await callback.message.edit_text(get_text(lang, "no_data"))
            return
        
        await get_exchange_rates()
        
        total_income = 0
        total_expenses = 0
        
        for trans in transactions:
            converted = convert_to_main_currency(
                trans["amount"],
                trans["currency"],
                main_currency
            )
            if trans["type"] == "income":
                total_income += converted
            else:
                total_expenses += converted
        
        net_profit = total_income - total_expenses
        
        text = get_text(lang, "monthly_report_title").format(month=month)
        text += get_text(lang, "total_income").format(
            amount=format_number(total_income),
            currency=main_currency
        ) + "\n"
        text += get_text(lang, "total_expenses").format(
            amount=format_number(total_expenses),
            currency=main_currency
        ) + "\n"
        text += get_text(lang, "net_profit").format(
            amount=format_number(net_profit),
            currency=main_currency
        )
        
        await callback.message.edit_text(text)
    except Exception as e:
        logger.error(f"Error in monthly selection: {e}")
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.answer(get_text(lang, "error_message"))


# ===================== DAILY REPORT HANDLERS =====================

@router.message(F.text.in_(["🔍 Kunlik hisobot", "🔍 Дневной отчет", "🔍 Daily Report"]))
async def process_daily_report(message: Message, state: FSMContext):
    """Handle daily report button."""
    try:
        lang = await get_lang(state, message.from_user.id)
        user_id = message.from_user.id
        
        # Clear any previous state
        await state.clear()
        await state.update_data(language=lang)
        
        months = await db.get_available_months(user_id)
        
        if not months:
            await message.answer(get_text(lang, "no_months"))
            return
        
        await message.answer(
            get_text(lang, "select_month"),
            reply_markup=get_months_keyboard(months, "dailym")
        )
    except Exception as e:
        logger.error(f"Error in daily report: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data.startswith("dailym_"))
async def process_daily_month_selection(callback: CallbackQuery, state: FSMContext):
    """Handle month selection for daily report."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        month = callback.data.replace("dailym_", "")
        
        await state.update_data(selected_month=month)
        await callback.message.edit_text(
            get_text(lang, "enter_day"),
            reply_markup=get_days_keyboard(f"dailyd_{month}", lang)
        )
    except Exception as e:
        logger.error(f"Error in daily month selection: {e}")
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data.startswith("dailyd_"))
async def process_daily_day_selection(callback: CallbackQuery, state: FSMContext):
    """Handle day selection for daily report."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        
        # Parse: dailyd_2024-03_15
        parts = callback.data.replace("dailyd_", "").rsplit("_", 1)
        month = parts[0]
        day = int(parts[1])
        
        transactions = await db.get_transactions_by_date(callback.from_user.id, month, day)
        
        if not transactions:
            await callback.message.edit_text(
                get_text(lang, "no_data"),
                reply_markup=get_back_keyboard(lang, "main_menu")
            )
            return
        
        date_str = f"{month}-{day:02d}"
        text = get_text(lang, "daily_report_title").format(date=date_str)
        
        for trans in transactions:
            emoji = "💰" if trans["type"] == "income" else "💸"
            text += f"{emoji} {trans['goal']}: {format_number(trans['amount'])} {trans['currency']}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard(lang, "main_menu")
        )
    except Exception as e:
        logger.error(f"Error in daily day selection: {e}")
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.answer(get_text(lang, "error_message"))


# ===================== DEBTS HANDLERS =====================

@router.message(F.text.in_(["🤝 Oldi-berdi", "🤝 Долги", "🤝 Debts"]))
async def process_debts_menu(message: Message, state: FSMContext):
    """Handle debts menu button."""
    try:
        lang = await get_lang(state, message.from_user.id)
        await message.answer(
            get_text(lang, "debts_menu"),
            reply_markup=get_debts_menu_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Error in debts menu: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data == "debt_owed_to_me")
async def process_debt_owed_to_me(callback: CallbackQuery, state: FSMContext):
    """Handle 'owed to me' button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        await state.set_state(UserStates.entering_debt_owed_to_me)
        await state.update_data(debt_type="owed_to_me")
        await callback.message.edit_text(get_text(lang, "enter_debt_info"))
    except Exception as e:
        logger.error(f"Error in debt owed to me: {e}")


@router.callback_query(F.data == "debt_i_owe")
async def process_debt_i_owe(callback: CallbackQuery, state: FSMContext):
    """Handle 'I owe' button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        await state.set_state(UserStates.entering_debt_i_owe)
        await state.update_data(debt_type="i_owe")
        await callback.message.edit_text(get_text(lang, "enter_debt_info"))
    except Exception as e:
        logger.error(f"Error in debt i owe: {e}")


@router.message(UserStates.entering_debt_owed_to_me)
@router.message(UserStates.entering_debt_i_owe)
async def process_debt_input(message: Message, state: FSMContext):
    """Handle debt input."""
    try:
        lang = await get_lang(state, message.from_user.id)
        text = message.text.strip()
        
        # Parse input: "Name Amount"
        match = re.match(r'^(.+?)\s+(\d+(?:[.,]\d+)?)$', text)
        if not match:
            await message.answer(get_text(lang, "invalid_format"))
            return
        
        name = match.group(1)
        amount = float(match.group(2).replace(",", "."))
        
        await state.update_data(debt_name=name, debt_amount=amount)
        await state.set_state(UserStates.selecting_debt_currency)
        await message.answer(
            get_text(lang, "select_currency"),
            reply_markup=get_currency_keyboard("debt")
        )
    except Exception as e:
        logger.error(f"Error in debt input: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data.startswith("debt_"), UserStates.selecting_debt_currency)
async def process_debt_currency(callback: CallbackQuery, state: FSMContext):
    """Handle debt currency selection."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        currency = callback.data.split("_")[1]
        
        data = await state.get_data()
        name = data.get("debt_name")
        amount = data.get("debt_amount")
        debt_type = data.get("debt_type")
        
        date = await db.add_debt(
            callback.from_user.id,
            name,
            amount,
            currency,
            debt_type
        )
        
        await callback.message.edit_text(
            get_text(lang, "debt_saved").format(
                name=name,
                amount=format_number(amount),
                currency=currency,
                date=date
            )
        )
        await state.clear()
        await state.update_data(language=lang)
    except Exception as e:
        logger.error(f"Error in debt currency: {e}")
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data == "debt_list")
async def process_debt_list(callback: CallbackQuery, state: FSMContext):
    """Handle debt list button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        
        debts = await db.get_all_debts(callback.from_user.id)
        
        if not debts:
            await callback.message.edit_text(
                get_text(lang, "no_debts"),
                reply_markup=get_back_keyboard(lang, "debts_menu")
            )
            return
        
        text = get_text(lang, "debt_list_title")
        
        owed_to_me = [d for d in debts if d["type"] == "owed_to_me"]
        i_owe = [d for d in debts if d["type"] == "i_owe"]
        
        buttons = []
        
        if owed_to_me:
            text += f"\n{get_text(lang, 'owed_to_me')}\n"
            for debt in owed_to_me:
                text += f"👤 {debt['name']}: {format_number(debt['amount'])} {debt['currency']}\n"
                buttons.append([InlineKeyboardButton(
                    text=f"✅ {debt['name']}",
                    callback_data=f"pay_{debt['id']}"
                )])
        
        if i_owe:
            text += f"\n{get_text(lang, 'i_owe')}\n"
            for debt in i_owe:
                text += f"👤 {debt['name']}: {format_number(debt['amount'])} {debt['currency']}\n"
                buttons.append([InlineKeyboardButton(
                    text=f"✅ {debt['name']}",
                    callback_data=f"pay_{debt['id']}"
                )])
        
        buttons.append([InlineKeyboardButton(
            text=get_text(lang, "btn_back"),
            callback_data="debts_menu"
        )])
        
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    except Exception as e:
        logger.error(f"Error in debt list: {e}")
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data == "debts_menu")
async def process_debts_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Handle debts menu callback."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.edit_text(
            get_text(lang, "debts_menu"),
            reply_markup=get_debts_menu_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Error in debts menu callback: {e}")


@router.callback_query(F.data.startswith("pay_"))
async def process_pay_debt(callback: CallbackQuery, state: FSMContext):
    """Handle pay debt button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        debt_id = int(callback.data.split("_")[1])
        
        await state.update_data(paying_debt_id=debt_id)
        await state.set_state(UserStates.entering_payment_amount)
        await callback.message.edit_text(get_text(lang, "enter_payment"))
    except Exception as e:
        logger.error(f"Error in pay debt: {e}")


@router.message(UserStates.entering_payment_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    """Handle payment amount input."""
    try:
        lang = await get_lang(state, message.from_user.id)
        
        try:
            payment = float(message.text.strip().replace(",", "."))
            if payment <= 0:
                raise ValueError()
        except ValueError:
            await message.answer(get_text(lang, "invalid_payment"))
            return
        
        data = await state.get_data()
        debt_id = data.get("paying_debt_id")
        
        debt = await db.get_debt_by_id(debt_id)
        if not debt:
            await message.answer(get_text(lang, "error_message"))
            return
        
        old_amount = debt["amount"]
        remaining = old_amount - payment
        
        if remaining <= 0:
            await db.delete_debt(debt_id)
            await message.answer(
                get_text(lang, "debt_cleared").format(name=debt["name"])
            )
        else:
            await db.update_debt_amount(debt_id, remaining)
            await message.answer(
                get_text(lang, "debt_updated").format(
                    name=debt["name"],
                    old_amount=format_number(old_amount),
                    currency=debt["currency"],
                    paid=format_number(payment),
                    remaining=format_number(remaining)
                )
            )
        
        await state.clear()
        await state.update_data(language=lang)
    except Exception as e:
        logger.error(f"Error in payment amount: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


# ===================== UTILITIES HANDLERS =====================

@router.message(F.text.in_(["🏠 Kommunal", "🏠 Коммунальные", "🏠 Utilities"]))
async def process_utilities_menu(message: Message, state: FSMContext):
    """Handle utilities menu button."""
    try:
        lang = await get_lang(state, message.from_user.id)
        await message.answer(
            get_text(lang, "utilities_menu"),
            reply_markup=get_utilities_menu_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Error in utilities menu: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data == "utilities_menu")
async def process_utilities_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Handle utilities menu callback."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.edit_text(
            get_text(lang, "utilities_menu"),
            reply_markup=get_utilities_menu_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Error in utilities menu callback: {e}")


@router.callback_query(F.data == "utility_add")
async def process_utility_add(callback: CallbackQuery, state: FSMContext):
    """Handle add utility button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        await state.set_state(UserStates.selecting_utility_type)
        await callback.message.edit_text(
            get_text(lang, "select_utility_type"),
            reply_markup=get_utility_types_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Error in utility add: {e}")


@router.callback_query(F.data.startswith("utiltype_"))
async def process_utility_type_selection(callback: CallbackQuery, state: FSMContext):
    """Handle utility type selection."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        utility_type = callback.data.replace("utiltype_", "")
        
        await state.update_data(utility_type=utility_type)
        await state.set_state(UserStates.entering_utility_amount)
        await callback.message.edit_text(get_text(lang, "enter_utility_amount"))
    except Exception as e:
        logger.error(f"Error in utility type selection: {e}")


@router.message(UserStates.entering_utility_amount)
async def process_utility_amount(message: Message, state: FSMContext):
    """Handle utility amount input."""
    try:
        lang = await get_lang(state, message.from_user.id)
        
        try:
            amount = float(message.text.strip().replace(",", "."))
            if amount <= 0:
                raise ValueError()
        except ValueError:
            await message.answer(get_text(lang, "invalid_format"))
            return
        
        await state.update_data(utility_amount=amount)
        await state.set_state(UserStates.selecting_utility_currency)
        await message.answer(
            get_text(lang, "select_currency"),
            reply_markup=get_currency_keyboard("util")
        )
    except Exception as e:
        logger.error(f"Error in utility amount: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data.startswith("util_"))
async def process_utility_currency(callback: CallbackQuery, state: FSMContext):
    """Handle utility currency selection."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        currency = callback.data.split("_")[1]
        
        data = await state.get_data()
        utility_type = data.get("utility_type")
        amount = data.get("utility_amount")
        
        date = await db.add_utility(
            callback.from_user.id,
            utility_type,
            amount,
            currency
        )
        
        await callback.message.edit_text(
            get_text(lang, "utility_saved").format(
                type=get_utility_name(lang, utility_type),
                amount=format_number(amount),
                currency=currency,
                date=date
            )
        )
        await state.clear()
        await state.update_data(language=lang)
    except Exception as e:
        logger.error(f"Error in utility currency: {e}")
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data == "utility_monthly")
async def process_utility_monthly(callback: CallbackQuery, state: FSMContext):
    """Handle monthly utilities button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        
        months = await db.get_utility_months(callback.from_user.id)
        
        if not months:
            await callback.message.edit_text(
                get_text(lang, "no_months"),
                reply_markup=get_back_keyboard(lang, "utilities_menu")
            )
            return
        
        await callback.message.edit_text(
            get_text(lang, "select_month"),
            reply_markup=get_months_keyboard(months, "utilmonth")
        )
    except Exception as e:
        logger.error(f"Error in utility monthly: {e}")


@router.callback_query(F.data.startswith("utilmonth_"))
async def process_utility_month_selection(callback: CallbackQuery, state: FSMContext):
    """Handle month selection for utilities."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        month = callback.data.replace("utilmonth_", "")
        
        utilities = await db.get_utilities_by_month(callback.from_user.id, month)
        
        if not utilities:
            await callback.message.edit_text(
                get_text(lang, "no_data"),
                reply_markup=get_back_keyboard(lang, "utilities_menu")
            )
            return
        
        text = get_text(lang, "monthly_report_title").format(month=month)
        
        for util in utilities:
            text += f"{get_utility_name(lang, util['utility_type'])}: {format_number(util['amount'])} {util['currency']}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard(lang, "utilities_menu")
        )
    except Exception as e:
        logger.error(f"Error in utility month selection: {e}")


@router.callback_query(F.data == "utility_daily")
async def process_utility_daily(callback: CallbackQuery, state: FSMContext):
    """Handle daily utilities button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        
        months = await db.get_utility_months(callback.from_user.id)
        
        if not months:
            await callback.message.edit_text(
                get_text(lang, "no_months"),
                reply_markup=get_back_keyboard(lang, "utilities_menu")
            )
            return
        
        await callback.message.edit_text(
            get_text(lang, "select_month"),
            reply_markup=get_months_keyboard(months, "utildailym")
        )
    except Exception as e:
        logger.error(f"Error in utility daily: {e}")


@router.callback_query(F.data.startswith("utildailym_"))
async def process_utility_daily_month(callback: CallbackQuery, state: FSMContext):
    """Handle month selection for daily utilities."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        month = callback.data.replace("utildailym_", "")
        
        await state.update_data(utility_month=month)
        await callback.message.edit_text(
            get_text(lang, "enter_day"),
            reply_markup=get_days_keyboard(f"utildailyd_{month}", lang)
        )
    except Exception as e:
        logger.error(f"Error in utility daily month: {e}")


@router.callback_query(F.data.startswith("utildailyd_"))
async def process_utility_daily_day(callback: CallbackQuery, state: FSMContext):
    """Handle day selection for daily utilities."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        
        # Parse: utildailyd_2024-03_15
        parts = callback.data.replace("utildailyd_", "").rsplit("_", 1)
        month = parts[0]
        day = int(parts[1])
        
        utilities = await db.get_utilities_by_date(callback.from_user.id, month, day)
        
        if not utilities:
            await callback.message.edit_text(
                get_text(lang, "no_data"),
                reply_markup=get_back_keyboard(lang, "utilities_menu")
            )
            return
        
        date_str = f"{month}-{day:02d}"
        text = get_text(lang, "daily_report_title").format(date=date_str)
        
        for util in utilities:
            text += f"{get_utility_name(lang, util['utility_type'])}: {format_number(util['amount'])} {util['currency']}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard(lang, "utilities_menu")
        )
    except Exception as e:
        logger.error(f"Error in utility daily day: {e}")
        lang = await get_lang(state, callback.from_user.id)
        await callback.message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data == "utility_stats")
async def process_utility_stats(callback: CallbackQuery, state: FSMContext):
    """Handle utility statistics button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        
        utilities = await db.get_all_utilities(callback.from_user.id)
        main_currency = await db.get_user_main_currency(callback.from_user.id)
        
        if not utilities:
            await callback.message.edit_text(
                get_text(lang, "no_data"),
                reply_markup=get_back_keyboard(lang, "utilities_menu")
            )
            return
        
        await get_exchange_rates()
        
        # Group by utility type
        stats: Dict[str, float] = {}
        for util in utilities:
            converted = convert_to_main_currency(
                util["amount"],
                util["currency"],
                main_currency
            )
            util_type = util["utility_type"]
            stats[util_type] = stats.get(util_type, 0) + converted
        
        text = get_text(lang, "utility_stats_title")
        total = 0
        
        for util_type, amount in stats.items():
            text += f"{get_utility_name(lang, util_type)}: {format_number(amount)} {main_currency}\n"
            total += amount
        
        text += f"\n💰 Total: {format_number(total)} {main_currency}"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_keyboard(lang, "utilities_menu")
        )
    except Exception as e:
        logger.error(f"Error in utility stats: {e}")


# ===================== CONVERTER HANDLERS =====================

@router.message(F.text.in_(["📈 Konverter/Valyuta", "📈 Конвертер/Валюта", "📈 Converter/Currency"]))
async def process_converter_menu(message: Message, state: FSMContext):
    """Handle converter menu button."""
    try:
        lang = await get_lang(state, message.from_user.id)
        await message.answer(
            get_text(lang, "converter_menu"),
            reply_markup=get_converter_menu_keyboard(lang)
        )
    except Exception as e:
        logger.error(f"Error in converter menu: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data == "convert_start")
async def process_convert_start(callback: CallbackQuery, state: FSMContext):
    """Handle convert button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        await state.set_state(UserStates.selecting_convert_currency)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇸 USD", callback_data="convfrom_USD"),
                InlineKeyboardButton(text="🇷🇺 RUB", callback_data="convfrom_RUB")
            ],
            [
                InlineKeyboardButton(text="🇨🇳 CNY", callback_data="convfrom_CNY")
            ]
        ])
        
        await callback.message.edit_text(
            get_text(lang, "select_from_currency"),
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in convert start: {e}")


@router.callback_query(F.data.startswith("convfrom_"))
async def process_convert_currency(callback: CallbackQuery, state: FSMContext):
    """Handle convert currency selection."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        currency = callback.data.replace("convfrom_", "")
        
        await state.update_data(convert_from=currency)
        await state.set_state(UserStates.entering_convert_amount)
        await callback.message.edit_text(get_text(lang, "enter_convert_amount"))
    except Exception as e:
        logger.error(f"Error in convert currency: {e}")


@router.message(UserStates.entering_convert_amount)
async def process_convert_amount(message: Message, state: FSMContext):
    """Handle convert amount input."""
    try:
        lang = await get_lang(state, message.from_user.id)
        
        try:
            amount = float(message.text.strip().replace(",", "."))
            if amount <= 0:
                raise ValueError()
        except ValueError:
            await message.answer(get_text(lang, "invalid_format"))
            return
        
        await get_exchange_rates()
        
        data = await state.get_data()
        from_currency = data.get("convert_from")
        
        result = amount * EXCHANGE_RATES.get(from_currency, 1)
        
        await message.answer(
            get_text(lang, "convert_result").format(
                amount=format_number(amount),
                from_curr=from_currency,
                result=format_number(result)
            )
        )
        await state.clear()
        await state.update_data(language=lang)
    except Exception as e:
        logger.error(f"Error in convert amount: {e}")
        lang = await get_lang(state, message.from_user.id)
        await message.answer(get_text(lang, "error_message"))


@router.callback_query(F.data == "main_currency")
async def process_main_currency_menu(callback: CallbackQuery, state: FSMContext):
    """Handle main currency button."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 UZS", callback_data="setcurr_UZS"),
                InlineKeyboardButton(text="🇺🇸 USD", callback_data="setcurr_USD")
            ],
            [
                InlineKeyboardButton(text="🇷🇺 RUB", callback_data="setcurr_RUB"),
                InlineKeyboardButton(text="🇨🇳 CNY", callback_data="setcurr_CNY")
            ]
        ])
        
        await callback.message.edit_text(
            get_text(lang, "select_main_currency"),
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in main currency menu: {e}")


@router.callback_query(F.data.startswith("setcurr_"))
async def process_set_main_currency(callback: CallbackQuery, state: FSMContext):
    """Handle main currency selection."""
    try:
        await callback.answer()
        lang = await get_lang(state, callback.from_user.id)
        currency = callback.data.replace("setcurr_", "")
        
        await db.update_main_currency(callback.from_user.id, currency)
        
        await callback.message.edit_text(
            get_text(lang, "main_currency_set").format(currency=currency)
        )
    except Exception as e:
        logger.error(f"Error in set main currency: {e}")


# ===================== MAIN =====================

async def main():
    """Main function to start the bot."""
    logger.info("Starting bot...")
    
    # Initialize database
    await db.init_db()
    
    # Fetch exchange rates
    await get_exchange_rates()
    
    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
