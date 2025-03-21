import telebot
import requests
import psycopg2
from telebot import types
from datetime import datetime, timedelta

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Подключение к PostgreSQL
DATABASE_URL = 'postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Создание таблицы, если не существует
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE,
        registered_at TIMESTAMP
    )
""")
conn.commit()

# Твой Telegram ID для админки
ADMIN_ID = 1903057676

# --- Каналы и ссылки ---
NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}
REQUIRED_CHANNELS = {
    "2 канал": "https://t.me/ChatByOxide",
    "3 канал": "https://t.me/Oxide_Vzlom"
}
DOWNLOAD_ANDROID = "https://t.me/+dxcSK08NRmxjNWRi"
DOWNLOAD_IOS = "https://t.me/+U3QzhcTHKv1lNmMy"
SHARE_TEXT = "– мой любимый бесплатный чит на Oxide: Survival Island! ❤️"
user_system = {}

# --- Функции БД ---
def save_user_id(user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, registered_at) VALUES (%s, %s)",
            (user_id, datetime.utcnow())
        )
        conn.commit()

def count_users_since(hours):
    time_limit = datetime.utcnow() - timedelta(hours=hours)
    cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at >= %s", (time_limit,))
    return cursor.fetchone()[0]

def total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

# --- Обработка команд ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":
        return

    save_user_id(message.from_user.id)

    markup = types.InlineKeyboardMarkup()
    android = types.InlineKeyboardButton("📱 Android", callback_data="select_android")
    ios = types.InlineKeyboardButton("🍏 iOS", callback_data="select_ios")
    markup.add(android, ios)

    bot.send_message(
        message.chat.id,
        "🔹 *Выберите вашу систему:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 У вас нет доступа к этой команде.")
        return

    count_24h = count_users_since(24)
    count_48h = count_users_since(48)
    count_all = total_users()

    bot.send_message(
        message.chat.id,
        f"📊 *Статистика пользователей:*\n"
        f"• За 24 часа: {count_24h}\n"
        f"• За 48 часов: {count_48h}\n"
        f"• Всего: {count_all}",
        parse_mode="Markdown"
    )

# --- Подписка и выбор ОС ---
def is_subscribed(user_id):
    for _, link in REQUIRED_CHANNELS.items():
        username = link.split("/")[-1]
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{username}&user_id={user_id}"
        response = requests.get(url).json()
        if response.get('result', {}).get('status') not in ['member', 'administrator', 'creator']:
            return False
    return True

@bot.callback_query_handler(func=lambda call: call.data in ["select_android", "select_ios"])
def select_system(call):
    user_id = call.from_user.id
    system = "Android" if call.data == "select_android" else "iOS"
    user_system[user_id] = system

    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(name, url=link) for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items()]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))

    bot.send_message(
        call.message.chat.id,
        "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id

    if is_subscribed(user_id):
        system = user_system.get(user_id, "Android")
        link = DOWNLOAD_ANDROID if system == "Android" else DOWNLOAD_IOS

        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT)
        markup.add(share_button)

        bot.send_message(
            call.message.chat.id,
            f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
            f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({link})\n\n"
            f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            call.message.chat.id,
            "❌ *Вы ещё не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
            parse_mode="Markdown"
        )

# --- Неизвестные команды ---
@bot.message_handler(func=lambda m: m.chat.type == "private")
def unknown(m):
    bot.send_message(
        m.chat.id,
        "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.",
        parse_mode="Markdown"
    )

# --- Запуск бота ---
if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
