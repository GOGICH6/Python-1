import telebot
import requests
import psycopg2
import os
from telebot import types
from datetime import datetime, timedelta

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Подключение к базе данных PostgreSQL (Neon.tech)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Создание таблицы пользователей, если она отсутствует
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
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

# Сохранение ID пользователя в базу данных
def save_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
    conn.commit()

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":
        return

    user_id = message.from_user.id
    save_user(user_id)  # Сохраняем пользователя в базу

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

# Выбор игры
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def select_game(call):
    user_id = call.from_user.id
    game = "Oxide" if call.data == "game_oxide" else "Standoff 2"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 Android", callback_data="system_android"),
        types.InlineKeyboardButton("🍏 iOS", callback_data="system_ios")
    )

    bot.edit_message_text(
        "🔹 *Выберите вашу систему:*",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# Выбор ОС
@bot.callback_query_handler(func=lambda call: call.data.startswith("system_"))
def select_system(call):
    user_id = call.from_user.id
    system = "Android" if call.data == "system_android" else "iOS"
    game = "Oxide" if call.message.text == "Oxide" else "Standoff 2"
    apk_link = APK_LINKS.get(game, {}).get(system)

    if not apk_link:
        bot.edit_message_text(
            "❌ *Извините, но APK для данной игры и платформы пока недоступен.*",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        return

    if is_subscribed(user_id):
        send_download_menu(call, game, system, apk_link)
    else:
        send_subscription_request(call.message)

# Запрос подписки
def send_subscription_request(message):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(name, url=link) for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items()
    ]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))

    bot.send_message(
        message.chat.id,
        "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Меню после успешной подписки
def send_download_menu(call, game, system, apk_link):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT))
    markup.add(types.InlineKeyboardButton("ℹ️ Об моде", callback_data="about_mod"))

    bot.edit_message_text(
        f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
        f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({apk_link})\n\n"
        f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# Команда /admin (доступ только тебе)
ADMIN_ID = 1903057676

@bot.message_handler(commands=['admin'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date >= NOW() - INTERVAL '1 day'")
    last_24h = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date >= NOW() - INTERVAL '2 days'")
    last_48h = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📊 *Статистика пользователей:*\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🕛 За 24 часа: {last_24h}\n"
        f"🕒 За 48 часов: {last_48h}",
        parse_mode="Markdown"
    )

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
