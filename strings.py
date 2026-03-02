# strings.py - Multi-language support for the Telegram bot

STRINGS = {
    "uz": {
        # Language selection
        "select_language": "🌐 Iltimos, tilni tanlang:",
        "language_selected": "✅ O'zbek tili tanlandi!",
        
        # Main menu
        "main_menu": "🏠 Asosiy menyu\n\nQuyidagi tugmalardan birini tanlang:",
        "btn_expenses": "💸 Xarajatlar",
        "btn_income": "💰 Daromad",
        "btn_statistics": "📊 Statistika",
        "btn_monthly_report": "📅 Oylik hisobot",
        "btn_daily_report": "🔍 Kunlik hisobot",
        "btn_debts": "🤝 Oldi-berdi",
        "btn_utilities": "🏠 Kommunal",
        "btn_converter": "📈 Konverter/Valyuta",
        
        # Expenses/Income
        "enter_amount_goal": "📝 Iltimos, miqdor va maqsadni yozing.\n\nMasalan: Tushlik 50000",
        "select_currency": "💱 Valyutani tanlang:",
        "expense_saved": "✅ Xarajat saqlandi!\n\n💸 Maqsad: {goal}\n💰 Miqdor: {amount} {currency}\n📅 Sana: {date}",
        "income_saved": "✅ Daromad saqlandi!\n\n💰 Maqsad: {goal}\n💵 Miqdor: {amount} {currency}\n📅 Sana: {date}",
        "invalid_format": "❌ Noto'g'ri format. Iltimos, qaytadan kiriting.\n\nMasalan: Tushlik 50000",
        
        # Statistics
        "statistics_title": "📊 Umumiy statistika\n\n",
        "total_income": "💰 Jami daromad: {amount} {currency}",
        "total_expenses": "💸 Jami xarajatlar: {amount} {currency}",
        "net_profit": "📈 Sof foyda: {amount} {currency}",
        "no_data": "📭 Ma'lumot topilmadi.",
        
        # Monthly report
        "select_month": "📅 Oyni tanlang:",
        "monthly_report_title": "📅 {month} oyi hisoboti\n\n",
        "no_months": "📭 Hozircha hech qanday oy mavjud emas.",
        
        # Daily report
        "enter_day": "📆 Kunni kiriting (1-31):",
        "daily_report_title": "🔍 {date} sanasi hisoboti\n\n",
        "invalid_day": "❌ Noto'g'ri kun. Iltimos, 1-31 oralig'ida kiriting.",
        
        # Debts
        "debts_menu": "🤝 Oldi-berdi bo'limi\n\nQuyidagi tugmalardan birini tanlang:",
        "btn_i_owe": "🔴 Qarzdorman",
        "btn_owed_to_me": "🟢 Haqqim bor",
        "btn_debt_list": "📜 Kimda nima?",
        "enter_debt_info": "📝 Ism va miqdorni yozing.\n\nMasalan: Ali 100000",
        "debt_saved": "✅ Qarz saqlandi!\n\n👤 Ism: {name}\n💰 Miqdor: {amount} {currency}\n📅 Sana: {date}",
        "debt_list_title": "📜 Qarzlar ro'yxati\n\n",
        "owed_to_me": "🟢 Haqqim bor:",
        "i_owe": "🔴 Qarzdorman:",
        "no_debts": "✅ Hozircha qarzlar yo'q.",
        "btn_pay": "✅ To'lash",
        "enter_payment": "💵 Qancha to'landi?",
        "debt_updated": "✅ Qarz yangilandi!\n\n👤 {name}\n💰 Eski qarz: {old_amount} {currency}\n💵 To'langan: {paid} {currency}\n📊 Qolgan: {remaining} {currency}",
        "debt_cleared": "🎉 {name}ning qarzi to'liq to'landi va o'chirildi!",
        "invalid_payment": "❌ Noto'g'ri miqdor.",
        
        # Utilities
        "utilities_menu": "🏠 Kommunal to'lovlar\n\nQuyidagi tugmalardan birini tanlang:",
        "btn_add_utility": "➕ Hisob qo'shish",
        "btn_monthly_utilities": "📅 Oylik kommunal",
        "btn_daily_utilities": "🔍 Kunlik kommunal",
        "btn_utility_stats": "📈 Umumiy statistika",
        "select_utility_type": "🏠 Kommunal turini tanlang:",
        "utility_electricity": "⚡ Elektr",
        "utility_gas": "🔥 Gaz",
        "utility_water": "💧 Suv",
        "utility_waste": "🗑️ Chiqindi",
        "utility_internet": "🌐 Internet",
        "utility_phone": "📞 Telefon",
        "utility_tax": "🏛️ Soliq/Uy to'lovi",
        "enter_utility_amount": "💰 Miqdorni kiriting:",
        "utility_saved": "✅ Kommunal to'lov saqlandi!\n\n🏠 Turi: {type}\n💰 Miqdor: {amount} {currency}\n📅 Sana: {date}",
        "utility_stats_title": "📈 Kommunal statistika\n\n",
        
        # Converter
        "converter_menu": "📈 Konverter va valyuta\n\nQuyidagi tugmalardan birini tanlang:",
        "btn_convert": "💱 Konvertatsiya",
        "btn_main_currency": "⚙️ Asosiy valyuta",
        "select_from_currency": "💱 Qaysi valyutadan konvertatsiya qilasiz?",
        "enter_convert_amount": "💰 Miqdorni kiriting:",
        "convert_result": "💱 Konvertatsiya natijasi:\n\n{amount} {from_curr} = {result} UZS",
        "select_main_currency": "⚙️ Asosiy valyutani tanlang:\n\nBarcha statistikalar tanlangan valyutada ko'rsatiladi.",
        "main_currency_set": "✅ Asosiy valyuta {currency} qilib o'rnatildi!",
        
        # General
        "btn_back": "🔙 Orqaga",
        "btn_main_menu": "🏠 Asosiy menyu",
        "error_message": "😔 Kechirasiz, kutilmagan xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "welcome": "👋 Xush kelibsiz! Men sizning shaxsiy moliyaviy yordamchingizman.\n\nMen xarajatlar, daromadlar, qarzlar va kommunal to'lovlarni kuzatib borishingizga yordam beraman.",
    },
    
    "ru": {
        # Language selection
        "select_language": "🌐 Пожалуйста, выберите язык:",
        "language_selected": "✅ Русский язык выбран!",
        
        # Main menu
        "main_menu": "🏠 Главное меню\n\nВыберите одну из кнопок ниже:",
        "btn_expenses": "💸 Расходы",
        "btn_income": "💰 Доходы",
        "btn_statistics": "📊 Статистика",
        "btn_monthly_report": "📅 Месячный отчет",
        "btn_daily_report": "🔍 Дневной отчет",
        "btn_debts": "🤝 Долги",
        "btn_utilities": "🏠 Коммунальные",
        "btn_converter": "📈 Конвертер/Валюта",
        
        # Expenses/Income
        "enter_amount_goal": "📝 Пожалуйста, напишите сумму и цель.\n\nНапример: Обед 50000",
        "select_currency": "💱 Выберите валюту:",
        "expense_saved": "✅ Расход сохранен!\n\n💸 Цель: {goal}\n💰 Сумма: {amount} {currency}\n📅 Дата: {date}",
        "income_saved": "✅ Доход сохранен!\n\n💰 Цель: {goal}\n💵 Сумма: {amount} {currency}\n📅 Дата: {date}",
        "invalid_format": "❌ Неверный формат. Пожалуйста, попробуйте снова.\n\nНапример: Обед 50000",
        
        # Statistics
        "statistics_title": "📊 Общая статистика\n\n",
        "total_income": "💰 Общий доход: {amount} {currency}",
        "total_expenses": "💸 Общие расходы: {amount} {currency}",
        "net_profit": "📈 Чистая прибыль: {amount} {currency}",
        "no_data": "📭 Данные не найдены.",
        
        # Monthly report
        "select_month": "📅 Выберите месяц:",
        "monthly_report_title": "📅 Отчет за {month}\n\n",
        "no_months": "📭 Пока нет доступных месяцев.",
        
        # Daily report
        "enter_day": "📆 Введите день (1-31):",
        "daily_report_title": "🔍 Отчет за {date}\n\n",
        "invalid_day": "❌ Неверный день. Пожалуйста, введите число от 1 до 31.",
        
        # Debts
        "debts_menu": "🤝 Раздел долгов\n\nВыберите одну из кнопок ниже:",
        "btn_i_owe": "🔴 Я должен",
        "btn_owed_to_me": "🟢 Мне должны",
        "btn_debt_list": "📜 Кто кому?",
        "enter_debt_info": "📝 Напишите имя и сумму.\n\nНапример: Али 100000",
        "debt_saved": "✅ Долг сохранен!\n\n👤 Имя: {name}\n💰 Сумма: {amount} {currency}\n📅 Дата: {date}",
        "debt_list_title": "📜 Список долгов\n\n",
        "owed_to_me": "🟢 Мне должны:",
        "i_owe": "🔴 Я должен:",
        "no_debts": "✅ Пока долгов нет.",
        "btn_pay": "✅ Оплатить",
        "enter_payment": "💵 Сколько оплачено?",
        "debt_updated": "✅ Долг обновлен!\n\n👤 {name}\n💰 Старый долг: {old_amount} {currency}\n💵 Оплачено: {paid} {currency}\n📊 Остаток: {remaining} {currency}",
        "debt_cleared": "🎉 Долг {name} полностью погашен и удален!",
        "invalid_payment": "❌ Неверная сумма.",
        
        # Utilities
        "utilities_menu": "🏠 Коммунальные платежи\n\nВыберите одну из кнопок ниже:",
        "btn_add_utility": "➕ Добавить счет",
        "btn_monthly_utilities": "📅 Месячные платежи",
        "btn_daily_utilities": "🔍 Дневные платежи",
        "btn_utility_stats": "📈 Общая статистика",
        "select_utility_type": "🏠 Выберите тип коммунальной услуги:",
        "utility_electricity": "⚡ Электричество",
        "utility_gas": "🔥 Газ",
        "utility_water": "💧 Вода",
        "utility_waste": "🗑️ Мусор",
        "utility_internet": "🌐 Интернет",
        "utility_phone": "📞 Телефон",
        "utility_tax": "🏛️ Налог/Квартплата",
        "enter_utility_amount": "💰 Введите сумму:",
        "utility_saved": "✅ Коммунальный платеж сохранен!\n\n🏠 Тип: {type}\n💰 Сумма: {amount} {currency}\n📅 Дата: {date}",
        "utility_stats_title": "📈 Статистика коммунальных\n\n",
        
        # Converter
        "converter_menu": "📈 Конвертер и валюта\n\nВыберите одну из кнопок ниже:",
        "btn_convert": "💱 Конвертация",
        "btn_main_currency": "⚙️ Основная валюта",
        "select_from_currency": "💱 Из какой валюты конвертировать?",
        "enter_convert_amount": "💰 Введите сумму:",
        "convert_result": "💱 Результат конвертации:\n\n{amount} {from_curr} = {result} UZS",
        "select_main_currency": "⚙️ Выберите основную валюту:\n\nВся статистика будет отображаться в выбранной валюте.",
        "main_currency_set": "✅ Основная валюта установлена: {currency}!",
        
        # General
        "btn_back": "🔙 Назад",
        "btn_main_menu": "🏠 Главное меню",
        "error_message": "😔 Извините, произошла неожиданная ошибка. Пожалуйста, попробуйте снова.",
        "welcome": "👋 Добро пожаловать! Я ваш личный финансовый помощник.\n\nЯ помогу вам отслеживать расходы, доходы, долги и коммунальные платежи.",
    },
    
    "en": {
        # Language selection
        "select_language": "🌐 Please select a language:",
        "language_selected": "✅ English language selected!",
        
        # Main menu
        "main_menu": "🏠 Main Menu\n\nPlease select one of the buttons below:",
        "btn_expenses": "💸 Expenses",
        "btn_income": "💰 Income",
        "btn_statistics": "📊 Statistics",
        "btn_monthly_report": "📅 Monthly Report",
        "btn_daily_report": "🔍 Daily Report",
        "btn_debts": "🤝 Debts",
        "btn_utilities": "🏠 Utilities",
        "btn_converter": "📈 Converter/Currency",
        
        # Expenses/Income
        "enter_amount_goal": "📝 Please write the amount and goal.\n\nExample: Lunch 50000",
        "select_currency": "💱 Select currency:",
        "expense_saved": "✅ Expense saved!\n\n💸 Goal: {goal}\n💰 Amount: {amount} {currency}\n📅 Date: {date}",
        "income_saved": "✅ Income saved!\n\n💰 Goal: {goal}\n💵 Amount: {amount} {currency}\n📅 Date: {date}",
        "invalid_format": "❌ Invalid format. Please try again.\n\nExample: Lunch 50000",
        
        # Statistics
        "statistics_title": "📊 Overall Statistics\n\n",
        "total_income": "💰 Total Income: {amount} {currency}",
        "total_expenses": "💸 Total Expenses: {amount} {currency}",
        "net_profit": "📈 Net Profit: {amount} {currency}",
        "no_data": "📭 No data found.",
        
        # Monthly report
        "select_month": "📅 Select a month:",
        "monthly_report_title": "📅 Report for {month}\n\n",
        "no_months": "📭 No months available yet.",
        
        # Daily report
        "enter_day": "📆 Enter the day (1-31):",
        "daily_report_title": "🔍 Report for {date}\n\n",
        "invalid_day": "❌ Invalid day. Please enter a number between 1-31.",
        
        # Debts
        "debts_menu": "🤝 Debts Section\n\nPlease select one of the buttons below:",
        "btn_i_owe": "🔴 I Owe",
        "btn_owed_to_me": "🟢 Owed to Me",
        "btn_debt_list": "📜 Who Owes What?",
        "enter_debt_info": "📝 Write name and amount.\n\nExample: Ali 100000",
        "debt_saved": "✅ Debt saved!\n\n👤 Name: {name}\n💰 Amount: {amount} {currency}\n📅 Date: {date}",
        "debt_list_title": "📜 Debt List\n\n",
        "owed_to_me": "🟢 Owed to me:",
        "i_owe": "🔴 I owe:",
        "no_debts": "✅ No debts yet.",
        "btn_pay": "✅ Pay",
        "enter_payment": "💵 How much was paid?",
        "debt_updated": "✅ Debt updated!\n\n👤 {name}\n💰 Old debt: {old_amount} {currency}\n💵 Paid: {paid} {currency}\n📊 Remaining: {remaining} {currency}",
        "debt_cleared": "🎉 {name}'s debt has been fully paid and removed!",
        "invalid_payment": "❌ Invalid amount.",
        
        # Utilities
        "utilities_menu": "🏠 Utility Payments\n\nPlease select one of the buttons below:",
        "btn_add_utility": "➕ Add Bill",
        "btn_monthly_utilities": "📅 Monthly Utilities",
        "btn_daily_utilities": "🔍 Daily Utilities",
        "btn_utility_stats": "📈 Overall Statistics",
        "select_utility_type": "🏠 Select utility type:",
        "utility_electricity": "⚡ Electricity",
        "utility_gas": "🔥 Gas",
        "utility_water": "💧 Water",
        "utility_waste": "🗑️ Waste",
        "utility_internet": "🌐 Internet",
        "utility_phone": "📞 Phone",
        "utility_tax": "🏛️ Tax/House Bill",
        "enter_utility_amount": "💰 Enter the amount:",
        "utility_saved": "✅ Utility payment saved!\n\n🏠 Type: {type}\n💰 Amount: {amount} {currency}\n📅 Date: {date}",
        "utility_stats_title": "📈 Utility Statistics\n\n",
        
        # Converter
        "converter_menu": "📈 Converter and Currency\n\nPlease select one of the buttons below:",
        "btn_convert": "💱 Convert",
        "btn_main_currency": "⚙️ Main Currency",
        "select_from_currency": "💱 From which currency to convert?",
        "enter_convert_amount": "💰 Enter the amount:",
        "convert_result": "💱 Conversion result:\n\n{amount} {from_curr} = {result} UZS",
        "select_main_currency": "⚙️ Select main currency:\n\nAll statistics will be displayed in the selected currency.",
        "main_currency_set": "✅ Main currency set to {currency}!",
        
        # General
        "btn_back": "🔙 Back",
        "btn_main_menu": "🏠 Main Menu",
        "error_message": "😔 Sorry, an unexpected error occurred. Please try again.",
        "welcome": "👋 Welcome! I am your personal financial assistant.\n\nI will help you track expenses, income, debts, and utility payments.",
    }
}

UTILITY_TYPES = {
    "electricity": {"uz": "⚡ Elektr", "ru": "⚡ Электричество", "en": "⚡ Electricity"},
    "gas": {"uz": "🔥 Gaz", "ru": "🔥 Газ", "en": "🔥 Gas"},
    "water": {"uz": "💧 Suv", "ru": "💧 Вода", "en": "💧 Water"},
    "waste": {"uz": "🗑️ Chiqindi", "ru": "🗑️ Мусор", "en": "🗑️ Waste"},
    "internet": {"uz": "🌐 Internet", "ru": "🌐 Интернет", "en": "🌐 Internet"},
    "phone": {"uz": "📞 Telefon", "ru": "📞 Телефон", "en": "📞 Phone"},
    "tax": {"uz": "🏛️ Soliq/Uy to'lovi", "ru": "🏛️ Налог/Квартплата", "en": "🏛️ Tax/House Bill"},
}

def get_text(lang: str, key: str) -> str:
    """Get text in the specified language."""
    return STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))

def get_utility_name(lang: str, utility_type: str) -> str:
    """Get utility type name in the specified language."""
    return UTILITY_TYPES.get(utility_type, {}).get(lang, utility_type)
