import os
import telebot
from telebot import types
import psycopg2
from datetime import datetime

# Данные
BOT_TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
ADMIN_ID = 1903057676
DB_URL = "postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"

bot = telebot.TeleBot(BOT_TOKEN)
conn = psycopg2.connect(DB_URL)
conn.autocommit = True
cursor = conn.cursor()

# Создание таблиц
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS invites (
    id SERIAL PRIMARY KEY,
    creator_id BIGINT,
    channel_id BIGINT,
    channel_title TEXT,
    invite_link TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

# 📥 Регистрация пользователя
def register_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

# 🧮 Получение статистики
def get_stats():
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '24 hours'")
    day = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '48 hours'")
    two_days = cursor.fetchone()[0]
    return total, day, two_days

# 🔘 Кнопки админ-панели
def admin_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📩 Рассылка", callback_data="admin_broadcast"),
    )
    markup.add(
        types.InlineKeyboardButton("➕ Создать ссылку", callback_data="admin_create_link"),
        types.InlineKeyboardButton("🔗 Мои ссылки", callback_data="admin_my_links")
    )
    return markup

# 📦 /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.type != "private":
        return
    register_user(message.from_user.id)
    bot.send_message(message.chat.id, "🎮 Выберите нужную игру:", reply_markup=types.ReplyKeyboardRemove())

# 👮‍♂️ /admin только для тебя
@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ У вас нет доступа.")
    bot.send_message(message.chat.id, "🛠 Админ-панель:", reply_markup=admin_menu())

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
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=admin_menu())

# 📩 Рассылка
broadcast_cache = {}

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def ask_broadcast(call):
    bot.send_message(call.from_user.id, "✏️ Отправьте сообщение, которое хотите разослать всем пользователям.")
    broadcast_cache[call.from_user.id] = "wait_message"

@bot.message_handler(func=lambda m: broadcast_cache.get(m.from_user.id) == "wait_message")
def confirm_broadcast(message):
    broadcast_cache[message.from_user.id] = message
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data="broadcast_confirm"))
    markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="broadcast_cancel"))
    bot.send_message(message.chat.id, "Вы точно хотите отправить это сообщение всем?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("broadcast_"))
def do_broadcast(call):
    if call.data == "broadcast_confirm":
        msg = broadcast_cache.get(call.from_user.id)
        if isinstance(msg, telebot.types.Message):
            cursor.execute("SELECT user_id FROM users")
            user_ids = cursor.fetchall()
            sent = 0
            for (uid,) in user_ids:
                try:
                    bot.copy_message(uid, msg.chat.id, msg.message_id)
                    sent += 1
                except:
                    continue
            bot.send_message(call.from_user.id, f"📬 Рассылка завершена. Отправлено: {sent}")
        broadcast_cache.pop(call.from_user.id, None)
    else:
        bot.send_message(call.from_user.id, "❌ Рассылка отменена.")
        broadcast_cache.pop(call.from_user.id, None)

# ➕ Создать ссылку
invite_stage = {}

@bot.callback_query_handler(func=lambda c: c.data == "admin_create_link")
def ask_channel_id(call):
    bot.send_message(call.from_user.id, "📥 Отправьте ID канала, в котором бот админ.")
    invite_stage[call.from_user.id] = "waiting_channel_id"

@bot.message_handler(func=lambda m: invite_stage.get(m.from_user.id) == "waiting_channel_id")
def create_link_step2(message):
    try:
        chat = bot.get_chat(int(message.text))
        if not chat.type.startswith("channel"):
            return bot.reply_to(message, "❗ Это не ID канала.")
        invite_link = bot.create_chat_invite_link(chat.id, creates_join_request=False).invite_link
        cursor.execute("INSERT INTO invites (creator_id, channel_id, channel_title, invite_link) VALUES (%s, %s, %s, %s)", (
            message.from_user.id, chat.id, chat.title, invite_link
        ))
        bot.send_message(message.chat.id, f"✅ Ссылка создана для канала <b>{chat.title}</b>\n🔗 {invite_link}", parse_mode="HTML")
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "❌ Не удалось создать ссылку. Проверь, что бот — админ.")
    finally:
        invite_stage.pop(message.from_user.id, None)

# 🔗 Мои ссылки
@bot.callback_query_handler(func=lambda c: c.data == "admin_my_links")
def show_links(call):
    cursor.execute("SELECT channel_title, invite_link FROM invites WHERE creator_id = %s", (call.from_user.id,))
    links = cursor.fetchall()
    if not links:
        bot.send_message(call.from_user.id, "🔎 У вас пока нет ссылок.")
        return
    text = "<b>Ваши ссылки:</b>\n\n"
    for i, (title, link) in enumerate(links, 1):
        text += f"{i}) <b>{title}</b>\n🔗 {link}\n\n"
    bot.send_message(call.from_user.id, text, parse_mode="HTML")

# Обработка неизвестных
@bot.message_handler(func=lambda m: True)
def fallback(m):
    bot.send_message(m.chat.id, "🤖 Я вас не понял. Напишите /start или /admin.")

if __name__ == "__main__":
    print("Бот запущен")
    bot.infinity_polling()
    
