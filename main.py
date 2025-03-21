import telebot
import requests
import psycopg2
from telebot import types
from datetime import datetime

# === НАСТРОЙКИ ===
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
ADMIN_ID = 1903057676

# Подключение к PostgreSQL
conn = psycopg2.connect("postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

bot = telebot.TeleBot(TOKEN)

# Каналы
NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}
REQUIRED_CHANNELS = {
    "2 канал": "https://t.me/ChatByOxide",
    "3 канал": "https://t.me/Oxide_Vzlom"
}

# Ссылки на APK
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

# Текст при нажатии "Отправить другу"
SHARE_TEXT = "– мой любимый бесплатный чит на Oxide! ❤️"

# Временное хранилище
user_state = {}

# === ФУНКЦИИ ===

def save_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    conn.commit()

def is_subscribed(user_id):
    for url in REQUIRED_CHANNELS.values():
        username = url.split("/")[-1]
        res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{username}&user_id={user_id}").json()
        if res.get("result", {}).get("status") not in ["member", "administrator", "creator"]:
            return False
    return True

# === ОБРАБОТЧИКИ ===

@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.type != "private":
        return
    user_id = message.from_user.id
    save_user(user_id)
    user_state[user_id] = {}

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Oxide", callback_data="game_Oxide"),
        types.InlineKeyboardButton("Standoff 2", callback_data="game_Standoff 2")
    )

    bot.send_message(message.chat.id, "🎮 *Выбери нужную игру:*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def choose_game(call):
    game = call.data.split("_")[1]
    user_state[call.from_user.id] = {"game": game}

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 Android", callback_data="os_Android"),
        types.InlineKeyboardButton("🍏 iOS", callback_data="os_iOS")
    )

    bot.edit_message_text("🔹 *Выберите вашу систему:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("os_"))
def choose_os(call):
    system = call.data.split("_")[1]
    user_id = call.from_user.id
    game = user_state.get(user_id, {}).get("game")

    if not game:
        bot.send_message(call.message.chat.id, "❌ Вы не выбрали игру.")
        return

    user_state[user_id]["system"] = system
    apk_link = APK_LINKS.get(game, {}).get(system)

    if not apk_link:
        bot.edit_message_text("❌ APK для этой игры и платформы пока недоступен.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        return

    if is_subscribed(user_id):
        send_download_menu(call.message.chat.id, apk_link)
    else:
        send_subscription_menu(call.message.chat.id)

def send_subscription_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=3)
    for name, url in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items():
        markup.add(types.InlineKeyboardButton(name, url=url))
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))
    bot.send_message(chat_id, "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите \"✅ Проверить подписку\".", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subs(call):
    user_id = call.from_user.id
    game = user_state.get(user_id, {}).get("game")
    system = user_state.get(user_id, {}).get("system")
    apk_link = APK_LINKS.get(game, {}).get(system)

    if not game or not system:
        bot.send_message(call.message.chat.id, "❌ Вы не выбрали игру или ОС.")
        return

    if not apk_link:
        bot.send_message(call.message.chat.id, "❌ APK для этой комбинации недоступен.")
        return

    if is_subscribed(user_id):
        send_download_menu(call.message.chat.id, apk_link)
    else:
        bot.send_message(call.message.chat.id, "❌ *Вы ещё не подписались на все каналы!*", parse_mode="Markdown")

def send_download_menu(chat_id, link):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT))
    markup.add(types.InlineKeyboardButton("ℹ️ Об моде", callback_data="about_mod"))
    bot.send_message(chat_id,
        f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
        f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({link})\n\n"
        f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
        parse_mode="Markdown", reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "about_mod")
def about_mod(call):
    game = user_state.get(call.from_user.id, {}).get("game", "этого мода")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Техподдержка", url="https://t.me/Oxide_Vzlom_bot"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="check_subscription"))
    bot.send_message(call.message.chat.id, f"ℹ️ *Информация о моде для {game} временно отсутствует.*", parse_mode="Markdown", reply_markup=markup)

# /admin
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "⛔ Нет доступа.")
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '1 day'")
    last_24h = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '2 day'")
    last_48h = cursor.fetchone()[0]

    bot.send_message(message.chat.id,
        f"📊 *Статистика:*\n\n"
        f"👥 Всего пользователей: {total}\n"
        f"🕐 За 24ч: {last_24h}\n"
        f"🕑 За 48ч: {last_48h}",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: msg.chat.type == "private")
def fallback(msg):
    bot.send_message(msg.chat.id, "🤖 *Я вас не понял!* Используйте /start", parse_mode="Markdown")

# === Запуск ===
print("Бот запущен.")
bot.infinity_polling()
