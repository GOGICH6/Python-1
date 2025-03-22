import os
import telebot
import requests
import psycopg2
from telebot import types
from datetime import datetime

BOT_TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
ADMIN_ID = 1903057676
DB_URL = "postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

bot = telebot.TeleBot(BOT_TOKEN)
conn = psycopg2.connect(DB_URL)
conn.autocommit = True
cursor = conn.cursor()

# Создание таблиц
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS apk_links (
    game TEXT, system TEXT, url TEXT,
    PRIMARY KEY (game, system)
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS required_channels (
    name TEXT PRIMARY KEY,
    url TEXT
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS games (
    name TEXT PRIMARY KEY
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS mod_info (
    game TEXT PRIMARY KEY,
    description TEXT
);""")

# Переменные
user_data = {}
broadcast_cache = {}
apk_stage = {}
channel_stage = {}
channel_mode = {}
game_stage = {}
mod_stage = {}

# Регистрация пользователя
def register_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

# Проверка подписки
def is_subscribed(user_id):
    try:
        cursor.execute("SELECT url FROM required_channels")
        for url, in cursor.fetchall():
            username = url.split("/")[-1]
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id=@{username}&user_id={user_id}").json()
            if r.get("result", {}).get("status") not in ["member", "administrator", "creator"]:
                return False
        return True
    except:
        return False

# Команда /start
@bot.message_handler(commands=['start'])
def start_handler(msg):
    if msg.chat.type != "private":
        return
    register_user(msg.from_user.id)
    cursor.execute("SELECT name FROM games")
    rows = cursor.fetchall()
    if not rows:
        return bot.send_message(msg.chat.id, "❗ Нет доступных игр.")
    markup = types.InlineKeyboardMarkup()
    for name, in rows:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"game_{name}"))
    bot.send_message(msg.chat.id, "🎮 Выберите игру:", reply_markup=markup)

# Выбор игры
@bot.callback_query_handler(func=lambda c: c.data.startswith("game_"))
def choose_system(c):
    game = c.data.split("game_", 1)[1]
    user_data[c.from_user.id] = {"game": game}
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 Android", callback_data="system_Android"),
        types.InlineKeyboardButton("🍏 iOS", callback_data="system_iOS")
    )
    bot.edit_message_text("📲 Выберите систему:", c.message.chat.id, c.message.message_id, reply_markup=markup)

# Выбор ОС
@bot.callback_query_handler(func=lambda c: c.data.startswith("system_"))
def choose_system_os(c):
    uid = c.from_user.id
    system = c.data.split("_", 1)[1]
    game = user_data[uid]["game"]
    user_data[uid]["system"] = system

    cursor.execute("SELECT url FROM apk_links WHERE game = %s AND system = %s", (game, system))
    row = cursor.fetchone()
    if not row:
        bot.edit_message_text("❌ APK недоступен для этой платформы.", c.message.chat.id, c.message.message_id)
        return

    if not is_subscribed(uid):
        ask_subscription(c.message)
    else:
        show_download(c, game, system, row[0])

# Отправка подписки
def ask_subscription(message):
    cursor.execute("SELECT name, url FROM required_channels")
    markup = types.InlineKeyboardMarkup()
    for name, url in cursor.fetchall():
        markup.add(types.InlineKeyboardButton(name, url=url))
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))
    bot.edit_message_text("📢 Подпишитесь на каналы и нажмите «Проверить подписку»", message.chat.id, message.message_id, reply_markup=markup)
    # Проверка подписки
@bot.callback_query_handler(func=lambda c: c.data == "check_subscription")
def recheck_subscription(c):
    uid = c.from_user.id
    game = user_data[uid]["game"]
    system = user_data[uid]["system"]
    cursor.execute("SELECT url FROM apk_links WHERE game = %s AND system = %s", (game, system))
    row = cursor.fetchone()
    if not row:
        bot.send_message(uid, "❌ APK для этой ОС не найден.")
        return
    if not is_subscribed(uid):
        bot.send_message(uid, "❌ Вы не подписались на все каналы.")
    else:
        show_download(c, game, system, row[0])

# Меню скачивания
def show_download(c, game, system, url):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query="– мой любимый бесплатный чит на Oxide! ❤️"))
    markup.add(types.InlineKeyboardButton("ℹ️ Об моде", callback_data="about_mod"))
    bot.edit_message_text(
        f"✅ Вы прошли проверку!\n\n🔗 [Скачать APK]({url})",
        c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=markup
    )

# Инфо о моде
@bot.callback_query_handler(func=lambda c: c.data == "about_mod")
def about_mod_handler(c):
    game = user_data.get(c.from_user.id, {}).get("game")
    if not game:
        bot.answer_callback_query(c.id, "Сначала выберите игру.")
        return
    cursor.execute("SELECT description FROM mod_info WHERE game = %s", (game,))
    row = cursor.fetchone()
    desc = row[0] if row else "ℹ️ Описание не задано."
    bot.send_message(c.message.chat.id, desc)

# Статистика
def get_stats():
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '24 hours'")
    day = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '48 hours'")
    two_days = cursor.fetchone()[0]
    return total, day, two_days

# Меню админа
def admin_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📩 Рассылка", callback_data="admin_broadcast")
    )
    markup.add(
        types.InlineKeyboardButton("🔗 АПК-ссылки", callback_data="admin_apk"),
        types.InlineKeyboardButton("📢 Каналы", callback_data="admin_channels")
    )
    markup.add(
        types.InlineKeyboardButton("🎮 Игры", callback_data="admin_games"),
        types.InlineKeyboardButton("ℹ️ О модах", callback_data="admin_mods")
    )
    return markup

# Команда /admin
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ Нет доступа.")
    bot.send_message(message.chat.id, "🛠 Админ-панель:", reply_markup=admin_menu())

# Статистика
@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def stats_callback(call):
    t, d, td = get_stats()
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{t}</b>\n"
        f"🕒 За 24 часа: <b>{d}</b>\n"
        f"🕒 За 48 часов: <b>{td}</b>"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=admin_menu())

# Заготовка рассылки
@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def ask_broadcast(call):
    bot.send_message(call.from_user.id, "✏️ Отправьте сообщение для рассылки.")
    broadcast_cache[call.from_user.id] = "wait"

@bot.message_handler(func=lambda m: broadcast_cache.get(m.from_user.id) == "wait")
def confirm_broadcast(msg):
    broadcast_cache[msg.from_user.id] = msg
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data="broadcast_confirm"))
    markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="broadcast_cancel"))
    bot.send_message(msg.chat.id, "Вы точно хотите отправить это сообщение всем?", reply_markup=markup)
    @bot.callback_query_handler(func=lambda c: c.data.startswith("broadcast_"))
def do_broadcast(call):
    if call.data == "broadcast_confirm":
        message_obj = broadcast_cache.get(call.from_user.id)
        cursor.execute("SELECT user_id FROM users")
        users_list = cursor.fetchall()
        s, f = 0, 0
        for (uid,) in users_list:
            try:
                bot.copy_message(uid, message_obj.chat.id, message_obj.message_id)
                s += 1
            except:
                f += 1
        bot.send_message(call.from_user.id, f"📬 Рассылка завершена.\n✅ Отправлено: {s}\n❌ Ошибок: {f}")
    else:
        bot.send_message(call.from_user.id, "🚫 Рассылка отменена.")
    broadcast_cache.pop(call.from_user.id, None)

# Плейсхолдеры (можно временно убрать, если заменили основным меню)
@bot.callback_query_handler(func=lambda c: c.data in [
    "admin_apk", "admin_channels", "admin_games", "admin_mods"])
def placeholders(c):
    bot.answer_callback_query(c.id, "Раздел уже реализован.")

# Неизвестные команды
@bot.message_handler(func=lambda m: m.chat.type == "private")
def fallback(m):
    bot.send_message(m.chat.id, "🤖 Напиши /start для начала.")

# Запуск бота
if __name__ == "__main__":
    print("✅ Бот запущен.")
    bot.infinity_polling()
