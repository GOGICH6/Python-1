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

# Создание таблицы
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

# Текст для друга
SHARE_TEXT = "– мой любимый бесплатный чит на Oxide! ❤️"

# Временное хранилище
user_data = {}
broadcast_cache = {}

# Регистрация пользователя
def register_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

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

# /start
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != "private":
        return
    register_user(message.from_user.id)
    user_data[message.from_user.id] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Oxide", callback_data="game_oxide"),
        types.InlineKeyboardButton("Standoff 2", callback_data="game_standoff")
    )
    bot.send_message(message.chat.id, "🎮 *Выбери нужную игру:*", parse_mode="Markdown", reply_markup=markup)

# Выбор игры
@bot.callback_query_handler(func=lambda c: c.data.startswith("game_"))
def choose_game(call):
    user_id = call.from_user.id
    game = "Oxide" if call.data == "game_oxide" else "Standoff 2"
    user_data[user_id]["game"] = game

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 Android", callback_data="system_android"),
        types.InlineKeyboardButton("🍏 iOS", callback_data="system_ios")
    )
    bot.edit_message_text("🔹 *Выберите вашу систему:*", call.message.chat.id, call.message.message_id,
                          parse_mode="Markdown", reply_markup=markup)

# Выбор ОС
@bot.callback_query_handler(func=lambda c: c.data.startswith("system_"))
def choose_system(call):
    user_id = call.from_user.id
    system = "Android" if call.data == "system_android" else "iOS"
    user_data[user_id]["system"] = system

    game = user_data[user_id].get("game")
    apk_link = APK_LINKS.get(game, {}).get(system)

    if not apk_link:
        bot.edit_message_text("❌ *Извините, но APK для данной игры и платформы пока недоступен.*",
                              call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        return

    if is_subscribed(user_id):
        send_download_menu(call, game, apk_link)
    else:
        send_subscription_request(call.message)

# Запрос подписки
def send_subscription_request(message):
    markup = types.InlineKeyboardMarkup(row_width=3)
    for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items():
        markup.add(types.InlineKeyboardButton(name, url=link))
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))
    bot.send_message(message.chat.id,
                     "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
                     parse_mode="Markdown", reply_markup=markup)

# Проверка подписки
@bot.callback_query_handler(func=lambda c: c.data == "check_subscription")
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
        send_download_menu(call, game, apk_link)
    else:
        bot.send_message(call.message.chat.id,
                         "❌ *Вы ещё не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
                         parse_mode="Markdown")

# Меню после подписки
def send_download_menu(call, game, apk_link):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT))
    markup.add(types.InlineKeyboardButton("ℹ️ Об моде", callback_data="about_mod"))
    bot.edit_message_text(
        f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
        f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({apk_link})\n\n"
        f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# Об моде
@bot.callback_query_handler(func=lambda c: c.data == "about_mod")
def about_mod(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Техподдержка", callback_data="support"))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="check_subscription"))
    game = user_data.get(call.from_user.id, {}).get("game", "мода")
    bot.edit_message_text(
        f"ℹ️ *Информация*\n\n**Информация о моде для {game} временно отсутствует.**",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# Техподдержка
@bot.callback_query_handler(func=lambda c: c.data == "support")
def support(call):
    bot.send_message(call.message.chat.id,
                     "Если у вас возникли вопросы или проблемы, вы можете обратиться в техподдержку: <b>@Oxide_Vzlom_bot</b>",
                     parse_mode="HTML")

# /admin — только тебе
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ У вас нет доступа.")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"))
    markup.add(types.InlineKeyboardButton("📩 Рассылка", callback_data="admin_broadcast"))
    bot.send_message(message.chat.id, "🛠 Админ-панель:", reply_markup=markup)

# Статистика
@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def admin_stats(call):
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '24 hours'")
    day = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '48 hours'")
    two_days = cursor.fetchone()[0]

    bot.edit_message_text(
        f"📊 <b>Статистика:</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🕒 За 24 часа: <b>{day}</b>\n"
        f"🕒 За 48 часов: <b>{two_days}</b>",
        call.message.chat.id, call.message.message_id, parse_mode="HTML")

# Рассылка
@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def ask_broadcast(call):
    broadcast_cache[call.from_user.id] = "waiting_message"
    bot.send_message(call.from_user.id, "✉️ Отправь сообщение для рассылки.")

@bot.message_handler(func=lambda m: broadcast_cache.get(m.from_user.id) == "waiting_message")
def confirm_broadcast(message):
    broadcast_cache[message.from_user.id] = message
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data="confirm_broadcast"))
    markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="cancel_broadcast"))
    bot.send_message(message.chat.id, "Подтвердите рассылку:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ["confirm_broadcast", "cancel_broadcast"])
def do_broadcast(call):
    user_id = call.from_user.id
    if call.data == "confirm_broadcast":
        msg = broadcast_cache.get(user_id)
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        sent = 0
        for (uid,) in users:
            try:
                bot.copy_message(uid, msg.chat.id, msg.message_id)
                sent += 1
            except:
                continue
        bot.send_message(user_id, f"📬 Рассылка завершена. Отправлено: {sent}")
    else:
        bot.send_message(user_id, "❌ Рассылка отменена.")
    broadcast_cache.pop(user_id, None)

# Неизвестные команды
@bot.message_handler(func=lambda m: m.chat.type == "private")
def unknown_message(m):
    bot.send_message(m.chat.id, "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.",
                     parse_mode="Markdown")

# Запуск
if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
    
