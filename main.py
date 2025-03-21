import telebot
import requests
import psycopg2
from telebot import types
from datetime import datetime, timedelta

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Подключение к базе данных (Neon.tech)
DATABASE_URL = 'postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Создание таблицы, если не существует
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Админ ID
ADMIN_ID = 1903057676

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

SHARE_TEXT = "– мой любимый бесплатный чит на Oxide! ❤️"
user_data = {}

# Сохраняем юзера
def save_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    conn.commit()

# Проверка подписки
def is_subscribed(user_id):
    for link in REQUIRED_CHANNELS.values():
        username = link.split("/")[-1]
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{username}&user_id={user_id}"
        res = requests.get(url).json()
        status = res.get("result", {}).get("status")
        if status not in ['member', 'administrator', 'creator']:
            return False
    return True

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":
        return

    user_id = message.from_user.id
    user_data[user_id] = {}
    save_user(user_id)

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
    user_data[user_id]["game"] = game

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
    user_data[user_id]["system"] = system

    game = user_data[user_id].get("game")
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

# Подписка
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

# Проверка
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id
    game = user_data.get(user_id, {}).get("game")
    system = user_data.get(user_id, {}).get("system")
    apk_link = APK_LINKS.get(game, {}).get(system)

    if not game or not system:
        bot.send_message(call.message.chat.id, "❌ Ошибка! Вы не выбрали игру или систему.")
        return

    if not apk_link:
        bot.send_message(call.message.chat.id, "❌ APK для данной игры недоступен.")
        return

    if is_subscribed(user_id):
        send_download_menu(call, game, system, apk_link)
    else:
        bot.send_message(
            call.message.chat.id,
            "❌ *Вы ещё не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
            parse_mode="Markdown"
        )

# Меню после подписки
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

# Об моде
@bot.callback_query_handler(func=lambda call: call.data == "about_mod")
def about_mod(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💬 Техподдержка", callback_data="support"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="check_subscription")
    )

    game = user_data.get(call.from_user.id, {}).get("game", "мода")
    bot.edit_message_text(
        f"ℹ️ *Информация*\n\n**Информация о моде для {game} временно отсутствует.**",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# Техподдержка
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    bot.send_message(
        call.message.chat.id,
        "Если у вас возникли вопросы или проблемы, вы можете обратиться в техподдержку: <b>@Oxide_Vzlom_bot</b>",
        parse_mode="HTML"
    )

# Команда /admin
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет доступа.")
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date >= NOW() - INTERVAL '1 day'")
    last_24h = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date >= NOW() - INTERVAL '2 day'")
    last_48h = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📊 *Статистика:*\n\n"
        f"👥 Всего пользователей: {total}\n"
        f"🕛 За 24 часа: {last_24h}\n"
        f"🕒 За 48 часов: {last_48h}",
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
    
