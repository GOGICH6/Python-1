import telebot
import requests
import psycopg2
from telebot import types
from datetime import datetime, timedelta
import os

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Подключение к PostgreSQL (Neon.tech)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require")
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cursor = conn.cursor()

# Создание таблицы пользователей (если её нет)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE,
        registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()

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
        "iOS": None
    },
    "Standoff 2": {
        "Android": "https://t.me/+fgN29Y8PjTNhZWFi",
        "iOS": None
    }
}

# Текст для отправки другу
SHARE_TEXT = "– мой любимый бесплатный чит на Oxide! ❤️"

# Хранилище выбора пользователя
user_data = {}

# Проверка подписки
def is_subscribed(user_id):
    for channel_link in REQUIRED_CHANNELS.values():
        channel_username = channel_link.split("/")[-1]
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{channel_username}&user_id={user_id}"
        r = requests.get(url).json()
        status = r.get("result", {}).get("status")
        if status not in ["member", "administrator", "creator"]:
            return False
    return True

# Функция сохранения ID пользователя
def save_user(user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        conn.commit()

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":
        return

    user_id = message.from_user.id
    save_user(user_id)  # Сохраняем ID в базе

    user_data[user_id] = {}

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Oxide", callback_data="game_oxide"),
        types.InlineKeyboardButton("Standoff 2", callback_data="game_standoff")
    )

    bot.send_message(
        message.chat.id,
        "🎮 *Выбери нужную игру:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Команда /stats (только для администратора)
@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.from_user.id != 1903057676:
        bot.send_message(message.chat.id, "❌ *У вас нет доступа к этой команде.*", parse_mode="Markdown")
        return

    # Получаем статистику из базы
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '24 hours'")
    users_24h = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '48 hours'")
    users_48h = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📊 *Статистика пользователей:*\n\n"
        f"👥 *Всего пользователей:* {total_users}\n"
        f"📅 *За 24 часа:* {users_24h}\n"
        f"📆 *За 48 часов:* {users_48h}",
        parse_mode="Markdown"
    )

# Неизвестные команды
@bot.message_handler(func=lambda msg: msg.chat.type == "private")
def unknown_command(msg):
    bot.send_message(
        msg.chat.id,
        "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
