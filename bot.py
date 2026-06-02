"""
Бот "Всё для дома — Махачкала"
Установка: pip install pyTelegramBotAPI
Запуск:    python bot.py
"""

import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# ========== НАСТРОЙКИ ==========
TOKEN = "8777850515:AAGR16m-7wdy1aFC3Baq1KcO2Eyx4xK28tU"   # Вставь сюда токен
MINI_APP_URL = "https://project-d7s9l.vercel.app" # Ссылка на мини-апп
ADMIN_ID = 5715605642  # Твой Telegram ID (для получения заявок)
# ================================

bot = telebot.TeleBot(TOKEN)


# ───────────────────────────────────────────
# ГЛАВНАЯ КЛАВИАТУРА (постоянные кнопки внизу)
# ───────────────────────────────────────────
def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("🏠 Открыть приложение"),
        KeyboardButton("🔧 Найти мастера"),
    )
    kb.add(
        KeyboardButton("🏪 Магазины"),
        KeyboardButton("🚚 Доставка"),
    )
    kb.add(
        KeyboardButton("📋 Оставить заявку"),
        KeyboardButton("ℹ️ Как это работает"),
    )
    kb.add(
        KeyboardButton("🛠️ Стать мастером"),
        KeyboardButton("📞 Поддержка"),
    )
    return kb


# ───────────────────────────────────────────
# INLINE-КНОПКИ для стартового сообщения
# ───────────────────────────────────────────
def start_inline():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(
            "🚀 Открыть мини-приложение",
            web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
        ),
        InlineKeyboardButton("🔧 Найти мастера", callback_data="masters"),
        InlineKeyboardButton("🏪 Магазины стройматериалов", callback_data="shops"),
        InlineKeyboardButton("🚚 Заказать доставку", callback_data="delivery"),
        InlineKeyboardButton("ℹ️ Как это работает", callback_data="howto"),
    )
    return kb


# ───────────────────────────────────────────
# /start — приветствие
# ───────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(message):
    name = message.from_user.first_name or "друг"
    text = (
        f"👋 Привет, {name}!\n\n"
        "🏠 *Всё для дома — Махачкала*\n\n"
        "Здесь ты найдёшь:\n"
        "🔧 *Мастеров* — сантехников, электриков, отделочников и других специалистов\n"
        "🏪 *Магазины* — стройматериалы, плитка, электрика, сантехника\n"
        "🚚 *Доставку* — газель, КамАЗ, курьер по Махачкале\n\n"
        "Нажми кнопку ниже чтобы открыть приложение 👇"
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=start_inline()
    )
    # Показываем постоянную клавиатуру
    bot.send_message(
        message.chat.id,
        "Или выбери раздел из меню:",
        reply_markup=main_keyboard()
    )


# ───────────────────────────────────────────
# /help — инструкция
# ───────────────────────────────────────────
@bot.message_handler(commands=["help"])
def cmd_help(message):
    text = (
        "📖 *Инструкция по использованию*\n\n"
        "1️⃣ Нажми *«Открыть приложение»* — откроется полный каталог мастеров и магазинов\n\n"
        "2️⃣ Выбери нужного *мастера* по категории (сантехник, электрик и т.д.)\n\n"
        "3️⃣ Посмотри рейтинг, отзывы и цены — нажми *«Вызвать мастера»*\n\n"
        "4️⃣ Заполни короткую форму: имя, телефон, описание задачи\n\n"
        "5️⃣ Мастер *свяжется с тобой в течение 15 минут* ✅\n\n"
        "───────────────\n"
        "Если нужна *доставка материалов* — выбери тип транспорта в разделе 🚚 Доставка\n\n"
        "Есть вопросы? Пиши в *Поддержку* 📞"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(
        "🚀 Открыть приложение",
        web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
    ))
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=kb)


# ───────────────────────────────────────────
# /masters — список категорий мастеров
# ───────────────────────────────────────────
@bot.message_handler(commands=["masters"])
def cmd_masters(message):
    send_masters(message.chat.id)

def send_masters(chat_id):
    text = (
        "🔧 *Мастера Махачкалы*\n\n"
        "Выбери категорию — покажу доступных специалистов:"
    )
    kb = InlineKeyboardMarkup(row_width=2)
    categories = [
        ("🔧 Сантехники", "cat_plumber"),
        ("⚡ Электрики", "cat_electric"),
        ("🪣 Отделочники", "cat_finish"),
        ("🪚 Плиточники", "cat_tile"),
        ("🔥 Сварщики", "cat_weld"),
        ("🛋️ Мебельщики", "cat_furniture"),
        ("🎨 Маляры", "cat_paint"),
        ("🪟 Окна/Двери", "cat_windows"),
    ]
    buttons = [InlineKeyboardButton(name, callback_data=cb) for name, cb in categories]
    kb.add(*buttons)
    kb.add(InlineKeyboardButton("🚀 Открыть все в приложении",
                                 web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)


# ───────────────────────────────────────────
# /shops — магазины
# ───────────────────────────────────────────
@bot.message_handler(commands=["shops"])
def cmd_shops(message):
    send_shops(message.chat.id)

def send_shops(chat_id):
    text = (
        "🏪 *Магазины стройматериалов*\n\n"
        "🧱 *СтройМаркет Дагестан*\n"
        "   пр. Акушинского, 12 • 8:00–20:00\n"
        "   Кирпич, цемент, арматура, блоки\n\n"
        "🪟 *Мир Плитки*\n"
        "   ул. Ленина, 45 • 9:00–19:00\n"
        "   Керамика, керамогранит, мозаика\n\n"
        "🔌 *ЭлектроДом*\n"
        "   ул. Гагарина, 8 • 8:00–18:00\n"
        "   Кабель, розетки, освещение\n\n"
        "🛁 *АкваЛюкс*\n"
        "   пр. Насрутдинова, 3 • 9:00–19:00\n"
        "   Сантехника, ванны, трубы\n\n"
        "🎨 *КрасоТА*\n"
        "   ул. Советская, 22 • 8:00–18:00\n"
        "   Краски, грунтовки, шпатлёвки\n\n"
        "🪵 *ДеревоДом*\n"
        "   ул. Дахадаева, 18 • 8:00–17:00\n"
        "   Доски, ламинат, фанера, OSB"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(
        "🏪 Открыть все магазины в приложении",
        web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
    ))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)


# ───────────────────────────────────────────
# /delivery — доставка
# ───────────────────────────────────────────
@bot.message_handler(commands=["delivery"])
def cmd_delivery(message):
    send_delivery(message.chat.id)

def send_delivery(chat_id):
    text = (
        "🚚 *Доставка по Махачкале*\n\n"
        "🛵 *Курьер* — от 150 ₽\n"
        "   До 30 кг • 1-2 часа\n\n"
        "🚚 *Газель* — от 500 ₽\n"
        "   До 1.5 т • грузчики +200 ₽/чел\n\n"
        "🏗️ *КамАЗ / Зил* — от 2 500 ₽\n"
        "   До 10 т • сыпучие материалы\n\n"
        "🏠 *Подъём на этаж* — от 300 ₽\n"
        "   Любой этаж • аккуратно\n\n"
        "Выбери нужный тип и оформи заказ:"
    )
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🛵 Курьер", callback_data="order_courier"),
        InlineKeyboardButton("🚚 Газель", callback_data="order_gazel"),
        InlineKeyboardButton("🏗️ КамАЗ", callback_data="order_kamaz"),
        InlineKeyboardButton("🏠 Подъём", callback_data="order_lift"),
    )
    kb.add(InlineKeyboardButton(
        "🚀 Открыть в приложении",
        web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
    ))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)


# ───────────────────────────────────────────
# КАК ЭТО РАБОТАЕТ
# ───────────────────────────────────────────
def send_howto(chat_id):
    text = (
        "ℹ️ *Как это работает?*\n\n"
        "*Для заказчиков:*\n"
        "1. Открой приложение или выбери категорию\n"
        "2. Найди подходящего мастера\n"
        "3. Оставь заявку — укажи имя и телефон\n"
        "4. Мастер позвонит в течение 15 минут\n"
        "5. После работы оставь отзыв ⭐\n\n"
        "*Для мастеров:*\n"
        "1. Нажми «Стать мастером»\n"
        "2. Укажи специальность и опыт\n"
        "3. Получай заявки от клиентов\n\n"
        "✅ *Сервис бесплатный для клиентов*\n"
        "💼 Для мастеров — подписка от 500 ₽/мес"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(
        "🚀 Открыть приложение",
        web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
    ))
    kb.add(InlineKeyboardButton("🛠️ Стать мастером", callback_data="become_master"))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)


# ───────────────────────────────────────────
# СТАТЬ МАСТЕРОМ
# ───────────────────────────────────────────
def send_become_master(chat_id):
    text = (
        "🛠️ *Стать мастером*\n\n"
        "Зарегистрируйся в сервисе и получай клиентов каждый день!\n\n"
        "📋 *Что нужно:*\n"
        "• Указать специальность\n"
        "• Добавить фото работ\n"
        "• Пройти проверку\n\n"
        "💰 *Тарифы:*\n"
        "• Пробный — 0 ₽ (7 дней)\n"
        "• Базовый — 500 ₽/мес\n"
        "• Про — 1 200 ₽/мес (топ выдача)\n\n"
        "Напиши нам для регистрации:"
    )
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📝 Подать заявку мастера", callback_data="master_apply"))
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)


# ───────────────────────────────────────────
# ОБРАБОТКА ТЕКСТОВЫХ КНОПОК (ReplyKeyboard)
# ───────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def text_handler(message):
    t = message.text
    cid = message.chat.id

    if "Открыть приложение" in t:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(
            "🚀 Открыть мини-приложение",
            web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
        ))
        bot.send_message(cid, "Нажми чтобы открыть:", reply_markup=kb)

    elif "Найти мастера" in t:
        send_masters(cid)

    elif "Магазины" in t:
        send_shops(cid)

    elif "Доставка" in t:
        send_delivery(cid)

    elif "Оставить заявку" in t:
        bot.send_message(
            cid,
            "📋 *Оставить заявку*\n\nНапишите:\n"
            "• Ваше имя\n• Номер телефона\n• Что нужно сделать\n\n"
            "Например:\n_Магомед, +7 928 123-45-67, нужен сантехник — течёт труба под раковиной_",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(message, receive_application)

    elif "Как это работает" in t:
        send_howto(cid)

    elif "Стать мастером" in t:
        send_become_master(cid)

    elif "Поддержка" in t:
        bot.send_message(
            cid,
            "📞 *Поддержка*\n\n"
            "По всем вопросам пишите:\n"
            "👤 @admin_vsedomamakh\n"
            "📱 +7 (928) 000-00-00\n\n"
            "Работаем: 8:00 – 22:00 ежедневно",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            cid,
            "Выбери раздел из меню ниже 👇",
            reply_markup=main_keyboard()
        )


# ───────────────────────────────────────────
# ПРИЁМ ЗАЯВКИ
# ───────────────────────────────────────────
def receive_application(message):
    text = message.text
    user = message.from_user
    cid = message.chat.id

    # Подтверждение пользователю
    bot.send_message(
        cid,
        "✅ *Заявка принята!*\n\nМастер свяжется с вами в течение 15 минут.\n\nСпасибо за обращение! 🙏",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

    # Уведомление администратору
    admin_text = (
        f"🔔 *Новая заявка!*\n\n"
        f"👤 {user.full_name} (@{user.username or 'нет'})\n"
        f"🆔 ID: {user.id}\n\n"
        f"📝 *Текст заявки:*\n{text}"
    )
    try:
        bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception:
        pass


# ───────────────────────────────────────────
# CALLBACK КНОПКИ
# ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)

    CATEGORY_TEXTS = {
        "cat_plumber":   ("🔧 Сантехники", "Замена труб, установка сантехники, тёплый пол, счётчики", "от 800 ₽/час"),
        "cat_electric":  ("⚡ Электрики", "Монтаж проводки, щиты, розетки, освещение, видеонаблюдение", "от 1 000 ₽/час"),
        "cat_finish":    ("🪣 Отделочники", "Штукатурка, шпаклёвка, обои, покраска, гипсокартон", "от 600 ₽/м²"),
        "cat_tile":      ("🪚 Плиточники", "Укладка плитки, мозаика, затирка, тёплый пол", "от 700 ₽/м²"),
        "cat_weld":      ("🔥 Сварщики", "Ворота, заборы, перила, навесы, металлоконструкции", "от 1 200 ₽/час"),
        "cat_furniture": ("🛋️ Мебельщики", "Сборка мебели, шкафы-купе, кухни, корпусная мебель", "от 900 ₽/час"),
        "cat_paint":     ("🎨 Маляры", "Покраска стен и потолков, декоративная покраска, фасады", "от 500 ₽/м²"),
        "cat_windows":   ("🪟 Окна/Двери", "Установка окон ПВХ, регулировка, установка дверей, балконы", "от 1 500 ₽"),
    }

    DELIVERY_TEXTS = {
        "order_courier": ("🛵 Курьер", "до 30 кг • по городу", "от 150 ₽"),
        "order_gazel":   ("🚚 Газель", "до 1.5 тонны • + грузчики", "от 500 ₽"),
        "order_kamaz":   ("🏗️ КамАЗ / Зил", "до 10 тонн • сыпучие", "от 2 500 ₽"),
        "order_lift":    ("🏠 Подъём на этаж", "любой этаж • грузчики", "от 300 ₽"),
    }

    if call.data in CATEGORY_TEXTS:
        name, desc, price = CATEGORY_TEXTS[call.data]
        text = (
            f"*{name}*\n\n"
            f"📝 {desc}\n"
            f"💰 Цена: *{price}*\n\n"
            f"В приложении — полный список с рейтингами и отзывами 👇"
        )
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(
            "🚀 Смотреть мастеров в приложении",
            web_app=telebot.types.WebAppInfo(url=MINI_APP_URL)
        ))
        kb.add(InlineKeyboardButton("📋 Оставить заявку", callback_data=f"apply_{call.data}"))
        bot.send_message(cid, text, parse_mode="Markdown", reply_markup=kb)

    elif call.data in DELIVERY_TEXTS:
        name, desc, price = DELIVERY_TEXTS[call.data]
        text = (
            f"*{name}*\n"
            f"📦 {desc}\n"
            f"💰 {price}\n\n"
            f"Напишите адрес и что нужно доставить — мы свяжемся с вами:"
        )
        bot.send_message(cid, text, parse_mode="Markdown")
        bot.register_next_step_handler(call.message, receive_application)

    elif call.data == "masters":
        send_masters(cid)

    elif call.data == "shops":
        send_shops(cid)

    elif call.data == "delivery":
        send_delivery(cid)

    elif call.data == "howto":
        send_howto(cid)

    elif call.data == "become_master":
        send_become_master(cid)

    elif call.data == "master_apply":
        bot.send_message(
            cid,
            "📝 Напишите:\n• Ваше имя\n• Специальность\n• Опыт\n• Номер телефона\n\n"
            "Например: _Али, электрик, 7 лет, +7 928 000-00-00_",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(call.message, receive_application)

    elif call.data.startswith("apply_"):
        bot.send_message(
            cid,
            "📋 Напишите ваш запрос:\n• Имя\n• Телефон\n• Описание задачи",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(call.message, receive_application)


# ───────────────────────────────────────────
# ЗАПУСК
# ───────────────────────────────────────────
if __name__ == "__main__":
    print("✅ Бот запущен...")
    bot.infinity_polling()
