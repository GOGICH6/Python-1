import os
import telebot
import requests
import psycopg2
from datetime import datetime
from telebot import types

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

# ✅ Выбор игры
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Oxide", callback_data="game_oxide"))
    markup.add(types.InlineKeyboardButton("Standoff 2", callback_data="game_standoff"))
    bot.send_message(message.chat.id, "🎮 *Выбери нужную игру:*", parse_mode="Markdown", reply_markup=markup)

# ✅ Выбор ОС
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def select_os(call):
    game = "Oxide" if call.data == "game_oxide" else "Standoff 2"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 Android", callback_data=f"os_{game}_Android"))
    markup.add(types.InlineKeyboardButton("🍏 iOS", callback_data=f"os_{game}_iOS"))
    bot.edit_message_text("🔹 *Выберите вашу систему:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# ✅ Ссылки на АПК
APK_LINKS = {
    "Oxide": {"Android": "https://t.me/+dxcSK08NRmxjNWRi", "iOS": "https://t.me/+U3QzhcTHKv1lNmMy"},
    "Standoff 2": {"Android": "https://t.me/+fgN29Y8PjTNhZWFi", "iOS": None}
}

# ✅ Проверка подписки
@bot.callback_query_handler(func=lambda call: call.data.startswith("os_"))
def check_subscription(call):
    _, game, system = call.data.split("_")
    apk_link = APK_LINKS.get(game, {}).get(system)

    if not apk_link:
        bot.edit_message_text("❌ *Извините, но APK для данной игры пока недоступен.*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data=f"check_sub_{game}_{system}"))
    bot.edit_message_text("📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# ✅ Подтверждение подписки и выдача ссылки
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_sub_"))
def send_apk_link(call):
    _, game, system = call.data.split("_")
    apk_link = APK_LINKS.get(game, {}).get(system)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query="Мой любимый бесплатный чит! ❤️"))
    bot.edit_message_text(f"✅ *Вы успешно подписались!*\n🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({apk_link})", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# ✅ АДМИН-ПАНЕЛЬ
def admin_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    markup.add(types.InlineKeyboardButton("📩 Рассылка", callback_data="admin_broadcast"))
    return markup

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ У вас нет доступа.")
    bot.send_message(message.chat.id, "🛠 Админ-панель:", reply_markup=admin_menu())

# ✅ СТАТИСТИКА
@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def stats_handler(call):
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '24 hours'")
    day = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '48 hours'")
    two_days = cursor.fetchone()[0]
    text = f"📊 <b>Статистика:</b>\n👥 Всего: <b>{total}</b>\n🕒 24ч: <b>{day}</b>\n🕒 48ч: <b>{two_days}</b>"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=admin_menu())

# ✅ РАССЫЛКА (копирует формат сообщения)
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
        user_ids = cursor.fetchall()
        sent, failed = 0, 0
        for (uid,) in user_ids:
            try:
                bot.copy_message(uid, msg.chat.id, msg.message_id)
                sent += 1
            except:
                failed += 1
        bot.send_message(call.from_user.id, f"📬 Рассылка завершена.\n✅ Отправлено: {sent}\n❌ Ошибки: {failed}")
    else:
        bot.send_message(call.from_user.id, "❌ Рассылка отменена.")
    broadcast_cache.pop(call.from_user.id, None)

# ✅ ОБРАБОТКА НЕИЗВЕСТНЫХ СООБЩЕНИЙ
@bot.message_handler(func=lambda m: True)
def fallback(m):
    bot.send_message(m.chat.id, "🤖 Я вас не понял. Напишите /start или /admin.")

# ✅ ЗАПУСК БОТА
if __name__ == "__main__":
    print("Бот запущен")
    bot.infinity_polling()
    
