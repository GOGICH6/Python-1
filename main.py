import telebot
import requests
import psycopg2
from telebot import types
from datetime import datetime, timedelta

# --- Токен и Telegram бот ---
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# --- Подключение к PostgreSQL (Neon.tech) ---
DATABASE_URL = 'postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require'
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# --- Константы ---
ADMIN_ID = 1903057676

NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}
REQUIRED_CHANNELS = {
    "2 канал": "https://t.me/ChatByOxide",
    "3 канал": "https://t.me/Oxide_Vzlom"
}

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

user_state = {}  # Временное хранилище выбора игры

# --- Подписка ---
def is_subscribed(user_id):
    for url in REQUIRED_CHANNELS.values():
        channel = url.split("/")[-1]
        check_url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{channel}&user_id={user_id}"
        res = requests.get(check_url).json()
        status = res.get("result", {}).get("status")
        if status not in ["member", "administrator", "creator"]:
            return False
    return True

# --- Сохранение ID ---
def save_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    conn.commit()

# --- /start ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != "private":
        return

    save_user(message.from_user.id)

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Oxide", callback_data="game_Oxide"),
        types.InlineKeyboardButton("Standoff 2", callback_data="game_Standoff")
    )
    bot.send_message(message.chat.id, "🎮 *Выбери нужную игру:*", parse_mode="Markdown", reply_markup=markup)

# --- Выбор игры ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def select_game(call):
    game = call.data.split("_")[1]
    user_state[call.from_user.id] = {"game": game}

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 Android", callback_data="os_Android"),
        types.InlineKeyboardButton("🍏 iOS", callback_data="os_iOS")
    )
    bot.edit_message_text("🔹 *Выберите вашу систему:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# --- Выбор ОС ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("os_"))
def select_os(call):
    system = call.data.split("_")[1]
    user_id = call.from_user.id
    game = user_state.get(user_id, {}).get("game")

    if not game:
        bot.send_message(call.message.chat.id, "❌ Ошибка: сначала выберите игру.")
        return

    user_state[user_id]["system"] = system
    link = APK_LINKS.get(game, {}).get(system)

    if not link:
        bot.edit_message_text("❌ *Извините, но APK для этой игры и платформы пока недоступен.*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        return

    if is_subscribed(user_id):
        send_download_menu(call.message.chat.id, link)
    else:
        send_subscription_request(call.message.chat.id)

# --- Проверка подписки ---
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_sub(call):
    user_id = call.from_user.id
    game = user_state.get(user_id, {}).get("game")
    system = user_state.get(user_id, {}).get("system")
    link = APK_LINKS.get(game, {}).get(system)

    if not game or not system:
        bot.send_message(call.message.chat.id, "❌ Сначала выберите игру и ОС.")
        return

    if not link:
        bot.send_message(call.message.chat.id, "❌ APK пока недоступен.")
        return

    if is_subscribed(user_id):
        send_download_menu(call.message.chat.id, link)
    else:
        bot.send_message(call.message.chat.id, "❌ Вы ещё не подписаны на все каналы!", parse_mode="Markdown")

# --- Меню подписки ---
def send_subscription_request(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=3)
    for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items():
        markup.add(types.InlineKeyboardButton(name, url=link))
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))

    bot.send_message(chat_id, "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*", parse_mode="Markdown", reply_markup=markup)

# --- Меню загрузки ---
def send_download_menu(chat_id, apk_link):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query="– мой любимый бесплатный чит на Oxide! ❤️"))
    markup.add(types.InlineKeyboardButton("ℹ️ Об моде", callback_data="about_mod"))
    bot.send_message(chat_id,
        f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
        f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({apk_link})\n\n"
        f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- Об моде ---
@bot.callback_query_handler(func=lambda call: call.data == "about_mod")
def about_mod(call):
    game = user_state.get(call.from_user.id, {}).get("game", "мода")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Техподдержка", url="https://t.me/Oxide_Vzlom_bot"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="check_subscription"))
    bot.edit_message_text(f"ℹ️ *Информация*\n\n**Информация о моде для {game} временно отсутствует.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# --- Админ-панель ---
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "⛔ У вас нет доступа.")
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date >= NOW() - INTERVAL '1 day'")
    last_24h = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_date >= NOW() - INTERVAL '2 day'")
    last_48h = cursor.fetchone()[0]
    bot.send_message(message.chat.id,
        f"📊 *Статистика:*\n"
        f"• Всего: {total}\n"
        f"• За 24ч: {last_24h}\n"
        f"• За 48ч: {last_48h}",
        parse_mode="Markdown"
    )

# --- Неизвестные команды ---
@bot.message_handler(func=lambda msg: msg.chat.type == "private")
def unknown(msg):
    bot.send_message(msg.chat.id, "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.", parse_mode="Markdown")

# --- Запуск ---
if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
