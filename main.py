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

def ensure_connection():
    global conn, cursor
    if conn.closed != 0:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

def register_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

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
    },
    "Black Russia": {
        "Android": "https://t.me/+_mYvPRVrZL9jZTZi",
        "iOS": None
    },
    "BSD Brawl": {
        "Android": None,
        "iOS": None
    }
}

SHARE_TEXT = "- в нём лучшие бесплатные читы на мобильные игры ❤️"
user_data = {}

def is_subscribed(user_id):
    try:
        for channel_link in REQUIRED_CHANNELS.values():
            username = channel_link.split("/")[-1]
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id=@{username}&user_id={user_id}"
            r = requests.get(url).json()
            status = r.get("result", {}).get("status", "left")
            if status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False

@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        ensure_connection()
        if message.chat.type != "private":
            return
        register_user(message.from_user.id)
        if message.from_user.id not in user_data:
            user_data[message.from_user.id] = {}

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Oxide", callback_data="game_oxide"),
            types.InlineKeyboardButton("Standoff 2", callback_data="game_standoff")
        )
        markup.add(
            types.InlineKeyboardButton("Black Russia", callback_data="game_blackrussia"),
            types.InlineKeyboardButton("BSD Brawl", callback_data="game_bsdbrawl")
        )
        markup.add(types.InlineKeyboardButton("Ещё", callback_data="game_other"))

        bot.send_message(
            message.chat.id,
            "🎮 *Выберите нужную игру:*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка в /start у {message.from_user.id}: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка. Попробуйте снова позже.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def select_game(call):
    user_id = call.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}

    if call.data == "game_other":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Чтобы скачать любую другую игру, перейдите в канал и нажмите «Установить»")
        return

    game = {
        "game_oxide": "Oxide",
        "game_standoff": "Standoff 2",
        "game_blackrussia": "Black Russia",
        "game_bsdbrawl": "BSD Brawl"
    }.get(call.data)

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

    try:
        ensure_connection()
        if message.chat.type != "private":
            return

        register_user(message.from_user.id)

        if message.from_user.id not in user_data:
            user_data[message.from_user.id] = {}

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("Oxide", callback_data="game_oxide"),
            types.InlineKeyboardButton("Standoff 2", callback_data="game_standoff"),
            types.InlineKeyboardButton("Black Russia", callback_data="game_blackrussia"),
            types.InlineKeyboardButton("BSD Brawl", callback_data="game_bsdbrawl"),
        )
        markup.add(types.InlineKeyboardButton("🎮 Ещё", callback_data="game_other"))

        bot.send_message(
            message.chat.id,
            "🎮 *Выберите нужную игру:*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка в /start: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка. Попробуйте снова позже.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def select_game(call):
    user_id = call.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}

    code = call.data.replace("game_", "")

    if code == "other":
        return bot.edit_message_text(
            "🎮 Чтобы скачать любую другую игру, перейдите в канал и нажмите «Установить»",
            call.message.chat.id,
            call.message.message_id
        )

    game_names = {
        "oxide": "Oxide",
        "standoff": "Standoff 2",
        "blackrussia": "Black Russia",
        "bsdbrawl": "BSD Brawl"
    }

    game = game_names.get(code)
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
@bot.callback_query_handler(func=lambda call: call.data.startswith("system_"))
def select_system(call):
    user_id = call.from_user.id

    if user_id not in user_data or "game" not in user_data[user_id]:
        bot.answer_callback_query(call.id, "Ошибка. Попробуйте заново /start.")
        return

    system = "Android" if call.data == "system_android" else "iOS"
    user_data[user_id]["system"] = system
    game = user_data[user_id]["game"]
    apk_link = APK_LINKS.get(game, {}).get(system)

    if not apk_link:
        bot.edit_message_text(
            "❌ *Не удалось найти файл. Вероятно, обновление ещё в процессе. Загляните позже!*",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        return  # <-- не забудь return после edit_message_text

    if is_subscribed(user_id):
        send_download_menu(call, game, system, apk_link)
    else:
        send_subscription_request(call.message)

def send_subscription_request(message):
    markup = types.InlineKeyboardMarkup(row_width=3)  # 3 кнопки в ряд

    buttons = [
        types.InlineKeyboardButton(name, url=link)
        for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items()
    ]
    markup.add(*buttons)  # добавляет все в одну строку

    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))

    bot.send_message(
        message.chat.id,
        "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
        parse_mode="Markdown",
        reply_markup=markup
    )

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
            "❌ *Вы ещё не подписались на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
            parse_mode="Markdown"
        )

def send_download_menu(call, game, system, apk_link):  # <-- теперь всё ок
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
@bot.callback_query_handler(func=lambda call: call.data == "about_mod")
def about_mod(call):
    game = user_data.get(call.from_user.id, {}).get("game", "мода")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💬 Техподдержка", callback_data="support"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="check_subscription")
    )

    bot.edit_message_text(
        f"ℹ️ *Информация*\n\n**Информация о моде для {game} временно отсутствует.**",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    bot.send_message(
        call.message.chat.id,
        "Если у вас возникли вопросы или проблемы, вы можете обратиться в техподдержку: <b>@Oxide_Vzlom_bot</b>",
        parse_mode="HTML"
    )
    # ========== Админ-панель ==========
def get_stats():
    ensure_connection()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '24 hours'")
    day = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '48 hours'")
    two_days = cursor.fetchone()[0]
    return total, day, two_days

def admin_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📩 Рассылка", callback_data="admin_broadcast")
    )
    return markup

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ У вас нет доступа.")
    bot.send_message(message.chat.id, "🛠 Админ-панель:", reply_markup=admin_menu())

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
    ensure_connection()
    if call.data == "broadcast_confirm":
        msg = broadcast_cache.get(call.from_user.id)
        if isinstance(msg, telebot.types.Message):
            cursor.execute("SELECT user_id FROM users")
            user_ids = cursor.fetchall()
            sent = 0
            failed = 0
            for (uid,) in user_ids:
                try:
                    bot.copy_message(uid, msg.chat.id, msg.message_id)
                    sent += 1
                except:
                    failed += 1
            bot.send_message(call.from_user.id, f"📬 Рассылка завершена.\n✅ Отправлено: {sent}\n❌ Не доставлено: {failed}")
        broadcast_cache.pop(call.from_user.id, None)
    else:
        bot.send_message(call.from_user.id, "❌ Рассылка отменена.")
        broadcast_cache.pop(call.from_user.id, None)

# Обработка неизвестных сообщений
@bot.message_handler(func=lambda msg: msg.chat.type == "private")
def unknown_command(msg):
    bot.send_message(
        msg.chat.id,
        "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.",
        parse_mode="Markdown"
    )

# Запуск бота
if __name__ == "__main__":
    print("✅ Бот запущен.")
    bot.infinity_polling()
