"""
SmartBalance - AI Finance Manager Bot
Built with aiogram 3.x + PostgreSQL + Render (Webhook)
"""

import asyncio
import os
import logging
import csv
import re
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, FSInputFile
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from models import init_db, get_session, User, Transaction # models.py га мосланг
from locales import LANGUAGES, TEXTS, UTILITY_CATEGORIES, MONTHS, t
from utils import (
    get_or_create_user, update_user, get_user,
    save_transaction, get_stats, get_monthly_report, get_daily_report,
    save_debt, get_debts, pay_debt, save_utility, get_utility_stats,
    convert_amount, format_currency, ADSGRAM_URL
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://your-app.onrender.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

# PORT хатоси тузатилди: Render муҳитидан автоматик олади
WEB_SERVER_PORT = int(os.environ.get("PORT", 8080))

# Ўзингизнинг Телеграм ID рақамингизни шу ерга ёзинг ёки Render'дан беринг
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

MAIN_CURRENCIES = ["USD", "RUB", "EUR", "CNY", "UZS", "KZT", "SAR", "INR", "TRY"]

router = Router()

# ─────────────────────────────────────────────
# 1. Middlewares (Янги)
# ─────────────────────────────────────────────
class UserCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Ҳар бир сўровда фойдаланувчини базадан олиб, data'га қўшиб беради
        user = get_or_create_user(event.from_user.id)
        data['db_user'] = user
        return await handler(event, data)

router.message.middleware(UserCheckMiddleware())
router.callback_query.middleware(UserCheckMiddleware())

# ─────────────────────────────────────────────
# 2. FSM States
# ─────────────────────────────────────────────
class RegState(StatesGroup):
    choose_lang = State()
    choose_currency = State()

class TxState(StatesGroup):
    waiting_category = State() # Янги: Харажат категорияси учун
    waiting_input = State()
    waiting_currency = State()

class DebtState(StatesGroup):
    choose_type = State()
    waiting_input = State()
    paying = State()

class UtilityState(StatesGroup):
    choose_category = State()
    waiting_input = State()
    monthly_view = State()
    daily_view = State()

class ConverterState(StatesGroup):
    waiting_input = State()

class SettingsState(StatesGroup):
    choose_option = State()
    choose_lang = State()
    choose_currency = State()

class ReportState(StatesGroup):
    monthly_choose = State()
    daily_choose_month = State()
    daily_choose_day = State()

class AdminState(StatesGroup):
    waiting_broadcast = State() # Янги: Админ хабар юбориши учун

# ─────────────────────────────────────────────
# 3. Keyboard Helpers
# ─────────────────────────────────────────────
def lang_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    items = list(LANGUAGES.items())
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(text=v, callback_data=f"lang_{k}") for k, v in items[i:i+2]]
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def currency_keyboard(prefix="cur") -> InlineKeyboardMarkup:
    buttons = []
    for i in range(0, len(MAIN_CURRENCIES), 3):
        row = [InlineKeyboardButton(text=c, callback_data=f"{prefix}_{c}") for c in MAIN_CURRENCIES[i:i+3]]
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text=t(lang, "expense")), KeyboardButton(text=t(lang, "income"))],
        [KeyboardButton(text=t(lang, "stats")), KeyboardButton(text=t(lang, "monthly"))],
        [KeyboardButton(text=t(lang, "daily")), KeyboardButton(text=t(lang, "debts"))],
        [KeyboardButton(text=t(lang, "utilities")), KeyboardButton(text=t(lang, "converter"))],
        [KeyboardButton(text=t(lang, "settings"))],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def tx_category_keyboard() -> InlineKeyboardMarkup:
    cats = ["🍱 Овқат", "🚕 Транспорт", "🏠 Уй", "👕 Кийим", "🛠 Бошқа"]
    buttons = [[InlineKeyboardButton(text=c, callback_data=f"txcat_{c}")] for c in cats]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def tx_currency_keyboard(main_currency: str, tx_type: str) -> InlineKeyboardMarkup:
    currencies = list(dict.fromkeys(["USD", "RUB", "CNY", main_currency]))
    buttons = [
        [InlineKeyboardButton(text=c, callback_data=f"txcur_{tx_type}_{c}") for c in currencies]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def month_keyboard(lang: str, prefix: str) -> InlineKeyboardMarkup:
    months = MONTHS.get(lang, MONTHS["en"])
    buttons = []
    year = datetime.now().year
    for i in range(0, 12, 3):
        row = [InlineKeyboardButton(text=months[j], callback_data=f"{prefix}_{year}_{j+1}") for j in range(i, min(i+3, 12))]
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def debt_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "they_owe"), callback_data="debt_add_they_owe")],
        [InlineKeyboardButton(text=t(lang, "i_owe"), callback_data="debt_add_i_owe")],
        [InlineKeyboardButton(text=t(lang, "debt_list"), callback_data="debt_list")],
    ])

def utility_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "add_utility"), callback_data="util_add")],
        [InlineKeyboardButton(text=t(lang, "utility_monthly"), callback_data="util_monthly")],
        [InlineKeyboardButton(text=t(lang, "utility_daily"), callback_data="util_daily")],
        [InlineKeyboardButton(text=t(lang, "utility_stats"), callback_data="util_stats")],
    ])

def utility_category_keyboard(lang: str) -> InlineKeyboardMarkup:
    cats = UTILITY_CATEGORIES.get(lang, UTILITY_CATEGORIES["en"])
    buttons = [[InlineKeyboardButton(text=c, callback_data=f"utilcat_{c}")] for c in cats]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def ad_timer_keyboard(msg: Message, lang: str, result_text: str):
    ad_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "watch_ad", sec=5), callback_data="ad_wait")]
    ])
    sent = await msg.answer(result_text + "\n\n⬇️", reply_markup=ad_btn)
    await asyncio.sleep(5)
    open_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "open_result"), url=ADSGRAM_URL)]
    ])
    try:
        await sent.edit_reply_markup(reply_markup=open_btn)
    except Exception:
        pass

# ─────────────────────────────────────────────
# 4. Admin Panel & Broadcast (Янги)
# ─────────────────────────────────────────────
@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Хабар тарқатиш (Broadcast)", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="👥 Фойдаланувчилар сони", callback_data="admin_stats")]
    ])
    await msg.answer("👨‍✈️ **Админ панелга хуш келибсиз!**\nНима қилмоқчисиз?", reply_markup=kb)

@router.callback_query(F.data == "admin_stats", F.from_user.id == ADMIN_ID)
async def admin_users_count(cb: CallbackQuery):
    session = get_session()
    count = session.query(User).count()
    session.close()
    await cb.answer(f"📊 Ботда жами {count} та фойдаланувчи бор.", show_alert=True)

@router.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def admin_broadcast_start(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("📝 Хабар матнини, расм ёки видеосини юборинг.\nБекор қилиш учун /cancel босинг.")
    await state.set_state(AdminState.waiting_broadcast)

@router.message(AdminState.waiting_broadcast, F.from_user.id == ADMIN_ID)
async def admin_broadcast_send(msg: Message, state: FSMContext):
    session = get_session()
    users = session.query(User).all()
    session.close()
    
    count = 0
    await msg.answer("⏳ Хабар тарқатилмоқда, илтимос кутинг...")
    for u in users:
        try:
            await msg.copy_to(u.telegram_id)
            count += 1
            await asyncio.sleep(0.05) # Телеграм блок қилмаслиги учун
        except Exception:
            pass
            
    await msg.answer(f"✅ Хабар муваффақиятли {count} та фойдаланувчига етказилди.")
    await state.clear()

# ─────────────────────────────────────────────
# 5. CSV Export (Янги)
# ─────────────────────────────────────────────
@router.message(Command("export"))
async def export_data(msg: Message, db_user):
    lang = db_user.language or "uz"
    await msg.answer("⏳ Маълумотлар тайёрланмоқда...")
    
    session = get_session()
    txs = session.query(Transaction).filter_by(user_id=msg.from_user.id).all()
    session.close()
    
    if not txs:
        await msg.answer(t(lang, "no_data"))
        return
        
    file_path = f"report_{msg.from_user.id}.csv"
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Sana", "Tur", "Kategoriya/Izoh", "Summa", "Valyuta"])
        for tx in txs:
            writer.writerow([tx.date.strftime("%Y-%m-%d %H:%M"), tx.type, tx.description, tx.amount, tx.currency])
            
    await msg.answer_document(FSInputFile(file_path), caption="📊 Сизнинг тўлиқ молиявий ҳисоботингиз (Excel/CSV).")
    os.remove(file_path)

# ─────────────────────────────────────────────
# /start - Registration
# ─────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext, db_user):
    if db_user.language and db_user.main_currency:
        await msg.answer(t(db_user.language, "welcome"), reply_markup=main_menu_keyboard(db_user.language))
    else:
        await msg.answer("🌐 Choose your language / Tilni tanlang:", reply_markup=lang_keyboard())
        await state.set_state(RegState.choose_lang)

@router.callback_query(RegState.choose_lang, F.data.startswith("lang_"))
async def reg_choose_lang(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split("_")[1]
    await state.update_data(lang=lang)
    await cb.message.edit_text(t(lang, "choose_currency"), reply_markup=currency_keyboard("regcur"))
    await state.set_state(RegState.choose_currency)

@router.callback_query(RegState.choose_currency, F.data.startswith("regcur_"))
async def reg_choose_currency(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    currency = cb.data.split("_")[1]
    update_user(cb.from_user.id, language=lang, main_currency=currency)
    await state.clear()
    await cb.message.delete()
    await cb.message.answer(t(lang, "welcome"), reply_markup=main_menu_keyboard(lang))

# ─────────────────────────────────────────────
# Expense / Income (Категориялар қўшилди)
# ─────────────────────────────────────────────
@router.message(TxState.waiting_input)
async def tx_get_input(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    text = msg.text.strip()
    
    # 1. Матн ичидан ҳамма рақамларни қидирамиз
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", text.replace(" ", ""))
    
    if not numbers:
        await msg.answer("❌ Суммани киритмадингиз. Масалан: 'Обед 50000'")
        return

    amount = float(numbers[0]) # Биринчи топилган рақамни оламиз
    
    # 2. Рақамдан ташқари қолган матнни "Изоҳ" сифатида оламиз
    # Рақамни матндан ўчириш (бутун ёки қолдиқли бўлишига қараб)
    amount_str = str(int(amount) if amount.is_integer() else amount)
    description = text.replace(amount_str, "").strip()
    
    if not description:
        description = "Бошқа"

    # Маълумотларни FSM хотирасига сақлаймиз
    await state.update_data(amount=amount, description=description)
    
    # Валюта танлаш тугмаларини чиқарамиз
    data = await state.get_data()
    tx_type = data.get("tx_type", "expense")
    kb = tx_currency_keyboard(db_user.main_currency, tx_type)
    
    await msg.answer(
        f"💰 {t(lang, 'amount')}: {amount}\n📝 {t(lang, 'description')}: {description}\n\n"
        f"{t(lang, 'choose_currency_for_tx')}", 
        reply_markup=kb
    )
    await state.set_state(TxState.waiting_currency)

@router.callback_query(TxState.waiting_currency, F.data.startswith("txcur_"))
async def tx_choose_currency(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    _, tx_type, currency = cb.data.split("_")
    data = await state.get_data()
    
    save_transaction(cb.from_user.id, tx_type, data["amount"], currency, data["description"])
    await state.clear()
    await cb.message.edit_text(f"{t(lang, 'saved')} {format_currency(data['amount'], currency)} — {data['description']}")

# ─────────────────────────────────────────────
# Statistics & Reports (Ўзгармади)
# ─────────────────────────────────────────────
@router.message(F.text.func(lambda txt: any(txt == TEXTS.get(l, {}).get("stats") for l in TEXTS)))
async def handle_stats(msg: Message, db_user):
    lang = db_user.language or "uz"
    stats = await get_stats(msg.from_user.id, db_user.main_currency)
    mc = db_user.main_currency
    text = (
        f"📊 *{t(lang, 'stats')}*\n\n"
        f"{t(lang, 'total_income')}: `{format_currency(stats['income'], mc)}`\n"
        f"{t(lang, 'total_expense')}: `{format_currency(stats['expense'], mc)}`\n"
        f"{t(lang, 'net_profit')}: `{format_currency(stats['net'], mc)}`"
    )
    await ad_timer_keyboard(msg, lang, text)

@router.message(F.text.func(lambda txt: any(txt == TEXTS.get(l, {}).get("monthly") for l in TEXTS)))
async def handle_monthly(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    await msg.answer(t(lang, "choose_month"), reply_markup=month_keyboard(lang, "monrep"))
    await state.set_state(ReportState.monthly_choose)

@router.callback_query(ReportState.monthly_choose, F.data.startswith("monrep_"))
async def monthly_report_result(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    _, year, month = cb.data.split("_")
    year, month = int(year), int(month)
    
    months_list = MONTHS.get(lang, MONTHS["en"])
    report = await get_monthly_report(cb.from_user.id, year, month, db_user.main_currency)
    mc = db_user.main_currency
    
    text = (
        f"📅 *{months_list[month-1]} {year}*\n\n"
        f"{t(lang, 'total_income')}: `{format_currency(report['income'], mc)}`\n"
        f"{t(lang, 'total_expense')}: `{format_currency(report['expense'], mc)}`\n"
        f"{t(lang, 'net_profit')}: `{format_currency(report['net'], mc)}`"
    )
    await state.clear()
    await cb.message.delete()
    await ad_timer_keyboard(cb.message, lang, text)

@router.message(F.text.func(lambda txt: any(txt == TEXTS.get(l, {}).get("daily") for l in TEXTS)))
async def handle_daily(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    await msg.answer(t(lang, "choose_month"), reply_markup=month_keyboard(lang, "dayrep"))
    await state.set_state(ReportState.daily_choose_month)

@router.callback_query(ReportState.daily_choose_month, F.data.startswith("dayrep_"))
async def daily_choose_month(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    _, year, month = cb.data.split("_")
    await state.update_data(year=int(year), month=int(month))
    await cb.message.edit_text(t(lang, "enter_day"))
    await state.set_state(ReportState.daily_choose_day)

@router.message(ReportState.daily_choose_day)
async def daily_report_result(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    data = await state.get_data()
    try:
        day = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Kun raqamini kiriting (1-31)")
        return
    
    items = await get_daily_report(msg.from_user.id, data["year"], data["month"], day, db_user.main_currency)
    months_list = MONTHS.get(lang, MONTHS["en"])
    
    if not items:
        await msg.answer(t(lang, "no_data"))
    else:
        text = f"🔍 *{day} {months_list[data['month']-1]}*\n\n" + "\n".join(items)
        await msg.answer(text, parse_mode="Markdown")
    await state.clear()

# ─────────────────────────────────────────────
# Debts, Utilities, Converter & Settings (Ўзгармади, faqat db_user qo'shildi)
# ─────────────────────────────────────────────
@router.message(F.text.func(lambda txt: any(txt == TEXTS.get(l, {}).get("debts") for l in TEXTS)))
async def handle_debts_menu(msg: Message, db_user):
    lang = db_user.language or "uz"
    await msg.answer(t(lang, "debts"), reply_markup=debt_menu_keyboard(lang))

@router.callback_query(F.data.startswith("debt_add_"))
async def debt_add_type(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    debt_type = cb.data.replace("debt_add_", "")
    await state.update_data(debt_type=debt_type)
    await cb.message.edit_text(t(lang, "enter_debt_info"))
    await state.set_state(DebtState.waiting_input)

@router.message(DebtState.waiting_input)
async def debt_save(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    data = await state.get_data()
    parts = msg.text.strip().split()
    if len(parts) < 2:
        await msg.answer("❌ Format: Ismi 100 USD")
        return
    try:
        person_name = parts[0]
        amount = float(parts[1])
        currency = parts[2].upper() if len(parts) > 2 else db_user.main_currency
    except (ValueError, IndexError):
        await msg.answer("❌ Format: Ismi 100 USD")
        return
    
    save_debt(msg.from_user.id, person_name, amount, currency, data["debt_type"])
    await state.clear()
    await msg.answer(t(lang, "saved"))

@router.callback_query(F.data == "debt_list")
async def debt_list_view(cb: CallbackQuery, db_user):
    lang = db_user.language or "uz"
    debts = get_debts(cb.from_user.id)
    if not debts:
        await cb.answer(t(lang, "no_data"), show_alert=True)
        return
    buttons = []
    text_lines = [f"📜 *{t(lang, 'debt_list')}*\n"]
    for debt_id, name, amount, currency, dtype in debts:
        emoji = "🟢" if dtype == "they_owe" else "🔴"
        text_lines.append(f"{emoji} {name}: {format_currency(amount, currency)}")
        buttons.append([InlineKeyboardButton(text=f"✅ {name} - {t(lang, 'pay_debt')}", callback_data=f"debtpay_{debt_id}")])
    await cb.message.edit_text("\n".join(text_lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("debtpay_"))
async def debt_pay_prompt(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    debt_id = int(cb.data.split("_")[1])
    await state.update_data(debt_id=debt_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "full_pay"), callback_data=f"debtfull_{debt_id}")],
        [InlineKeyboardButton(text=t(lang, "partial_pay"), callback_data=f"debtpart_{debt_id}")],
    ])
    await cb.message.edit_text(t(lang, "pay_debt"), reply_markup=kb)

@router.callback_query(F.data.startswith("debtfull_"))
async def debt_pay_full(cb: CallbackQuery, db_user):
    lang = db_user.language or "uz"
    debt_id = int(cb.data.split("_")[1])
    pay_debt(debt_id)
    await cb.message.edit_text(t(lang, "debt_paid"))

@router.callback_query(F.data.startswith("debtpart_"))
async def debt_pay_partial_prompt(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    debt_id = int(cb.data.split("_")[1])
    await state.update_data(debt_id=debt_id)
    await cb.message.edit_text(t(lang, "partial_pay"))
    await state.set_state(DebtState.paying)

@router.message(DebtState.paying)
async def debt_pay_partial_do(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    data = await state.get_data()
    try:
        amount = float(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Summa kiriting")
        return
    pay_debt(data["debt_id"], amount)
    await state.clear()
    await msg.answer(t(lang, "debt_paid"))

@router.message(F.text.func(lambda txt: any(txt == TEXTS.get(l, {}).get("utilities") for l in TEXTS)))
async def handle_utilities_menu(msg: Message, db_user):
    lang = db_user.language or "uz"
    await msg.answer(t(lang, "utilities"), reply_markup=utility_menu_keyboard(lang))

@router.callback_query(F.data == "util_add")
async def util_add_start(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    await cb.message.edit_text(t(lang, "choose_utility"), reply_markup=utility_category_keyboard(lang))
    await state.set_state(UtilityState.choose_category)

@router.callback_query(UtilityState.choose_category, F.data.startswith("utilcat_"))
async def util_choose_category(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    category = cb.data.replace("utilcat_", "")
    await state.update_data(category=category)
    await cb.message.edit_text(t(lang, "enter_amount_desc"))
    await state.set_state(UtilityState.waiting_input)

@router.message(UtilityState.waiting_input)
async def util_save(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    data = await state.get_data()
    parts = msg.text.strip().split(maxsplit=1)
    try:
        amount = float(parts[0].replace(",", "."))
        description = parts[1] if len(parts) > 1 else data.get("category", "")
    except ValueError:
        await msg.answer("❌ Format: 50000 tavsif")
        return
    save_utility(msg.from_user.id, data["category"], amount, db_user.main_currency, description)
    await state.clear()
    await msg.answer(t(lang, "saved"))

@router.callback_query(F.data == "util_stats")
async def util_stats_view(cb: CallbackQuery, db_user):
    lang = db_user.language or "uz"
    stats = await get_utility_stats(cb.from_user.id, db_user.main_currency)
    if not stats:
        await cb.answer(t(lang, "no_data"), show_alert=True)
        return
    lines = [f"🏠 *{t(lang, 'utility_stats')}*\n"]
    for cat, amount in stats.items():
        lines.append(f"• {cat}: {format_currency(amount, db_user.main_currency)}")
    text = "\n".join(lines)
    await cb.message.delete()
    await ad_timer_keyboard(cb.message, lang, text)

@router.callback_query(F.data == "util_monthly")
async def util_monthly(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    await cb.message.edit_text(t(lang, "choose_month"), reply_markup=month_keyboard(lang, "utilmon"))
    await state.set_state(UtilityState.monthly_view)

@router.callback_query(UtilityState.monthly_view, F.data.startswith("utilmon_"))
async def util_monthly_result(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    _, year, month = cb.data.split("_")
    
    from models import Utility
    session = get_session()
    year, month = int(year), int(month)
    utils = session.query(Utility).filter_by(user_id=cb.from_user.id).filter(
        Utility.date >= datetime(year, month, 1)
    ).all()
    session.close()
    
    months_list = MONTHS.get(lang, MONTHS["en"])
    lines = [f"📅 *{months_list[month-1]} {year}*\n"]
    total = 0.0
    for u in utils:
        converted = await convert_amount(u.amount, u.currency, db_user.main_currency)
        total += converted
        lines.append(f"• {u.category}: {format_currency(converted, db_user.main_currency)}")
    lines.append(f"\n📊 Jami: {format_currency(total, db_user.main_currency)}")
    await state.clear()
    await cb.message.edit_text("\n".join(lines))

@router.message(F.text.func(lambda txt: any(txt == TEXTS.get(l, {}).get("converter") for l in TEXTS)))
async def handle_converter(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    await msg.answer(t(lang, "converter_prompt"))
    await state.set_state(ConverterState.waiting_input)

@router.message(ConverterState.waiting_input)
async def converter_do(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    parts = msg.text.strip().split()
    if len(parts) < 2:
        await msg.answer("❌ Format: 100 USD")
        return
    try:
        amount = float(parts[0])
        from_currency = parts[1].upper()
    except ValueError:
        await msg.answer("❌ Format: 100 USD")
        return
    converted = await convert_amount(amount, from_currency, db_user.main_currency)
    text = f"{t(lang, 'converted')}\n`{format_currency(amount, from_currency)}` → `{format_currency(converted, db_user.main_currency)}`"
    await state.clear()
    await msg.answer(text)

@router.message(F.text.func(lambda txt: any(txt == TEXTS.get(l, {}).get("settings") for l in TEXTS)))
async def handle_settings(msg: Message, db_user):
    lang = db_user.language or "uz"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Til / Language", callback_data="set_lang")],
        [InlineKeyboardButton(text="💵 Valyuta / Currency", callback_data="set_cur")],
    ])
    await msg.answer(t(lang, "settings"), reply_markup=kb)

@router.callback_query(F.data == "set_lang")
async def settings_lang(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("🌐 Tilni tanlang:", reply_markup=lang_keyboard())
    await state.set_state(SettingsState.choose_lang)

@router.callback_query(SettingsState.choose_lang, F.data.startswith("lang_"))
async def settings_set_lang(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split("_")[1]
    update_user(cb.from_user.id, language=lang)
    await state.clear()
    await cb.message.edit_text(t(lang, "lang_changed"))
    await cb.message.answer(t(lang, "main_menu"), reply_markup=main_menu_keyboard(lang))

@router.callback_query(F.data == "set_cur")
async def settings_cur(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    await cb.message.edit_text(t(lang, "choose_currency"), reply_markup=currency_keyboard("setcur"))
    await state.set_state(SettingsState.choose_currency)

@router.callback_query(SettingsState.choose_currency, F.data.startswith("setcur_"))
async def settings_set_cur(cb: CallbackQuery, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    currency = cb.data.split("_")[1]
    update_user(cb.from_user.id, main_currency=currency)
    await state.clear()
    await cb.message.edit_text(t(lang, "currency_changed"))

@router.callback_query(F.data == "ad_wait")
async def ad_wait(cb: CallbackQuery):
    await cb.answer("⏳ Iltimos kuting...", show_alert=False)

# ─────────────────────────────────────────────
# App Startup & Main
# ─────────────────────────────────────────────
async def on_startup(bot: Bot):
    init_db()
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

def main():
    # Парсе мод янги Aiogram 3 усулида ёзилди
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    # Порт автоматик олинади (Render талабига мос)
    web.run_app(app, host="0.0.0.0", port=WEB_SERVER_PORT)

if __name__ == "__main__":
    main()  бу код муни кайси каторига койи # "123456789" деган жойини ўчириб, 0 қилиб қўямиз.
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) муни ва import re # Коднинг энг тепасига қўшинг

@router.message(TxState.waiting_input)
async def tx_get_input(msg: Message, state: FSMContext, db_user):
    lang = db_user.language or "uz"
    text = msg.text.strip()
    
    # 1. Матн ичидан ҳамма рақамларни қидирамиз (масалан: 50 000 ёки 50000.5)
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", text.replace(" ", ""))
    
    if not numbers:
        await msg.answer("❌ Суммани киритмадингиз. Масалан: 'Обед 50000'")
        return

    amount = float(numbers[0]) # Биринчи топилган рақамни оламиз
    
    # 2. Рақамдан ташқари қолган матнни "Изоҳ" (яъни категория) сифатида оламиз
    description = text.replace(str(int(amount) if amount.is_integer() else amount), "").strip()
    
    # Агар изоҳ бўш бўлса, "Бошқа" деб ёзиб қўямиз
    if not description:
        description = "Бошқа"

    await state.update_data(amount=amount, description=description)
    
    # Валюта танлашга ўтамиз
    data = await state.get_data()
    kb = tx_currency_keyboard(db_user.main_currency, data["tx_type"])
    await msg.answer(f"💰 Сумма: {amount}\n📝 Категория: {description}\n\nВалютани танланг:", reply_markup=kb)
    await state.set_state(TxState.waiting_currency)
