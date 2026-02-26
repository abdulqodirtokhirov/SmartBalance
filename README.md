# 🤖 SmartBalance — AI Finance Manager Bot

## 📁 Fayl strukturasi
```
smartbalance/
├── main.py          # Asosiy bot kodi (barcha handler'lar)
├── models.py        # PostgreSQL modellari (SQLAlchemy)
├── locales.py       # 10 ta til uchun tarjimalar
├── utils.py         # Yordamchi funksiyalar, valyuta konvertatsiyasi
├── requirements.txt # Python kutubxonalari
├── render.yaml      # Render hosting konfiguratsiyasi
└── README.md        # Shu fayl
```

## ⚙️ O'rnatish

### 1. Environment Variables (Render Dashboard'da)
```
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://...  (Render avtomatik beradi)
EXCHANGE_API_KEY=your_exchangerate_api_key  (https://exchangerate-api.com)
ADSGRAM_URL=https://adsgram.ai/your_link
WEBHOOK_HOST=https://your-app-name.onrender.com
```

### 2. ExchangeRate API olish
1. https://exchangerate-api.com saytiga boring
2. Bepul akkount oching
3. API kalitni oling va EXCHANGE_API_KEY ga qo'ying

### 3. Render'ga deploy qilish
1. GitHub'ga kodni yuklang
2. Render.com'da yangi Web Service yarating
3. Repository'ni ulang
4. render.yaml avtomatik konfiguratsiyani o'qiydi
5. Environment variables'larni kiriting
6. Deploy!

## 🚀 Funksiyalar

| Tugma | Tavsif |
|-------|--------|
| 💸 Xarajat | Xarajat kiritish (4 valyuta tanlov) |
| 💰 Daromad | Daromad kiritish |
| 📊 Statistika | Jami hisobot (Adsgram reklama) |
| 📅 Oylik Hisobot | Oy bo'yicha hisobot (Adsgram) |
| 🔍 Kunlik Hisobot | Kun bo'yicha batafsil |
| 🤝 Oldi-berdi | Qarz boshqaruvi (to'liq/qisman) |
| 🏠 Kommunal | Kommunal to'lovlar (Adsgram) |
| 📈 Konverter | Istalgan valyuta → asosiy valyuta |
| ⚙️ Sozlamalar | Til va valyuta o'zgartirish |

## 🌐 Qo'llab-quvvatlangan tillar
🇺🇿 O'zbek | 🇷🇺 Русский | 🇺🇸 English | 🇰🇿 Қазақ | 🇰🇬 Кыргызча  
🇹🇯 Тоҷикӣ | 🇹🇷 Türkçe | 🇮🇳 हिन्दी | 🇨🇳 中文 | 🇸🇦 العربية

## 💰 Monetizatsiya
- 4 ta joyda Adsgram reklama (5 soniyalik taymer)
- Statistika, Oylik hisobot, Kommunal statistika, Qarz ro'yxati

## 🗄️ Ma'lumotlar bazasi
PostgreSQL + SQLAlchemy:
- `users` — foydalanuvchi sozlamalari
- `transactions` — daromad/xarajatlar
- `debts` — qarzlar
- `utilities` — kommunal to'lovlar
