import os
import telebot
import requests
import psycopg2
from datetime import datetime
from telebot import types

# Настройки
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
ADMIN_ID = 1903057676
DB_URL = 'postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'

bot = telebot.TeleBot(TOKEN)
conn = psycopg2.connect(DB_URL)
conn.autocommit = True
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Каналы
NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}
REQUIRED_CHANNELS = {
    "2 канал": "https://t.me/ChatByOxide",
    "3 канал": "https://t.me/Oxide_Vzlom"
}

# Ссылки на загрузку
APK_LINKS = {
    "Oxide": {
        "Android": "https://t.me/+dxcSK08NRmxjNWRi",
        "iOS": "https://t.me/+U3QzhcTHKv1lNmMy"
    },
    "Standoff 2": {
        "Android": "https://t.me/+fgN29Y8PjTNhZWFi",
        "iOS": None
    }
}

# Проверка подписки
def is_subscribed(user_id):
    for link in REQUIRED_CHANNELS.values():
        username = link.split("/")[-1]
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{username}&user_id={user_id}"
        res = requests.get(url).json()
        status = res.get("result", {}).get("status")
        if status not in ["member", "administrator", "creator"]:
            return False
    return True

# 📥 Регистрация пользователя
def register_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

# 📊 Получение статистики
def get_stats():
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '24 hours'")
    last_24h = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '48 hours'")
    last_48h = cursor.fetchone()[0]
    return total, last_24h, last_48h

# 📦 /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.type != "private":
        return
    register_user(message.from_user.id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Oxide", callback_data="game_oxide"),
        types.InlineKeyboardButton("Standoff 2", callback_data="game_standoff")
    )
    
    bot.send_message(
        message.chat.id,
        "🎮 *Выберите игру:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Выбор ОС
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def select_os(call):
    game = "Oxide" if call.data == "game_oxide" else "Standoff 2"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 Android", callback_data=f"system_{game}_Android"),
        types.InlineKeyboardButton("🍏 iOS", callback_data=f"system_{game}_iOS")
    )

    bot.edit_message_text(
        "🔹 *Выберите вашу систему:*",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# Запрос подписки (старый дизайн)
def send_subscription_request(message):
    markup = types.InlineKeyboardMarkup()
    row = []
    for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items():
        row.append(types.InlineKeyboardButton(name, url=link))
    
    markup.row(*row)
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))

    bot.send_message(
        message.chat.id,
        "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Проверка подписки
@bot.callback_query_handler(func=lambda c: c.data == "check_subscription")
def check_subscription(call):
    if is_subscribed(call.from_user.id):
        bot.send_message(call.message.chat.id, "✅ Вы успешно подписались!", parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id,
                         "❌ *Вы ещё не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
                         parse_mode="Markdown")

# 👮‍♂️ /admin - админ-панель
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ У вас нет доступа.")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📩 Рассылка", callback_data="admin_broadcast")
    )
    
    bot.send_message(message.chat.id, "🛠 Админ-панель:", reply_markup=markup)

# 📊 Статистика
@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def stats_handler(call):
    total, day, two_days = get_stats()
    text = (
        "📊 <b>Статистика:</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🕒 За 24 часа: <b>{day}</b>\n"
        f"🕒 За 48 часов: <b>{two_days}</b>"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML")

# 📩 Рассылка
broadcast_cache = {}

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def ask_broadcast(call):
    bot.send_message(call.from_user.id, "✏️ Отправьте сообщение для рассылки.")
    broadcast_cache[call.from_user.id] = "wait_message"

@bot.message_handler(func=lambda m: broadcast_cache.get(m.from_user.id) == "wait_message")
def confirm_broadcast(message):
    broadcast_cache[message.from_user.id] = message
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data="broadcast_confirm"))
    markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="broadcast_cancel"))
    bot.send_message(message.chat.id, "Вы уверены, что хотите отправить это сообщение всем?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("broadcast_"))
def do_broadcast(call):
    if call.data == "broadcast_confirm":
        msg = broadcast_cache.get(call.from_user.id)
        cursor.execute("SELECT user_id FROM users")
        for (uid,) in cursor.fetchall():
            try:
                bot.copy_message(uid, msg.chat.id, msg.message_id)
            except:
                continue
        bot.send_message(call.from_user.id, "📬 Рассылка завершена.")
    else:
        bot.send_message(call.from_user.id, "❌ Рассылка отменена.")

if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
    
