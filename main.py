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

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS apk_links (
    game TEXT, system TEXT, url TEXT,
    PRIMARY KEY (game, system)
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS required_channels (
    name TEXT PRIMARY KEY,
    url TEXT
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS games (
    name TEXT PRIMARY KEY
);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS mod_info (
    game TEXT PRIMARY KEY,
    description TEXT
);""")

user_data = {}
broadcast_cache = {}
apk_stage = {}
channel_stage = {}
game_stage = {}
mod_stage = {}

def register_user(user_id):
    cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

def is_subscribed(user_id):
    try:
        cursor.execute("SELECT url FROM required_channels")
        for url, in cursor.fetchall():
            username = url.split("/")[-1]
            r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id=@{username}&user_id={user_id}").json()
            if r.get("result", {}).get("status") not in ["member", "administrator", "creator"]:
                return False
        return True
    except:
        return False

@bot.message_handler(commands=['start'])
def start_handler(msg):
    if msg.chat.type != "private":
        return
    register_user(msg.from_user.id)
    cursor.execute("SELECT name FROM games")
    rows = cursor.fetchall()
    if not rows:
        return bot.send_message(msg.chat.id, "❗ Нет доступных игр.")
    markup = types.InlineKeyboardMarkup()
    for name, in rows:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"game_{name}"))
    bot.send_message(msg.chat.id, "🎮 Выберите игру:", reply_markup=markup)
    # --- ЧАСТЬ 2 ---

@bot.callback_query_handler(func=lambda c: c.data.startswith("game_"))
def choose_system(c):
    game = c.data.split("game_", 1)[1]
    user_data[c.from_user.id] = {"game": game}

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 Android", callback_data="system_Android"),
        types.InlineKeyboardButton("🍏 iOS", callback_data="system_iOS")
    )
    bot.edit_message_text("📲 Выберите систему:", c.message.chat.id, c.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("system_"))
def choose_system_os(c):
    uid = c.from_user.id
    system = c.data.split("_", 1)[1]
    game = user_data[uid]["game"]
    user_data[uid]["system"] = system

    # Ищем ссылку в apk_links
    cursor.execute("SELECT url FROM apk_links WHERE game = %s AND system = %s", (game, system))
    row = cursor.fetchone()
    if not row:
        bot.edit_message_text("❌ APK недоступен для этой платформы.", c.message.chat.id, c.message.message_id)
        return

    if not is_subscribed(uid):
        ask_subscription(c.message)
    else:
        show_download(c, game, system, row[0])

def ask_subscription(message):
    cursor.execute("SELECT name, url FROM required_channels")
    markup = types.InlineKeyboardMarkup()
    for row in cursor.fetchall():
        name, url = row
        markup.add(types.InlineKeyboardButton(name, url=url))
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))
    bot.edit_message_text("📢 Подпишитесь на каналы и нажмите «Проверить подписку»",
                          message.chat.id, message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "check_subscription")
def recheck_subscription(c):
    uid = c.from_user.id
    game = user_data[uid]["game"]
    system = user_data[uid]["system"]
    cursor.execute("SELECT url FROM apk_links WHERE game = %s AND system = %s", (game, system))
    row = cursor.fetchone()
    if not row:
        bot.send_message(uid, "❌ APK для этой ОС не найден.")
        return
    if not is_subscribed(uid):
        bot.send_message(uid, "❌ Вы не подписались на все каналы.")
    else:
        show_download(c, game, system, row[0])

def show_download(c, game, system, url):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query="– мой любимый бесплатный чит на Oxide! ❤️"))
    markup.add(types.InlineKeyboardButton("ℹ️ Об моде", callback_data="about_mod"))
    bot.edit_message_text(
        f"✅ Вы прошли проверку!\n\n🔗 [Скачать APK]({url})",
        c.message.chat.id, c.message.message_id, parse_mode="Markdown", reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data == "about_mod")
def about_mod_handler(c):
    game = user_data.get(c.from_user.id, {}).get("game")
    if not game:
        bot.answer_callback_query(c.id, "Сначала выберите игру.")
        return
    cursor.execute("SELECT description FROM mod_info WHERE game = %s", (game,))
    row = cursor.fetchone()
    desc = row[0] if row else "ℹ️ Описание не задано."
    bot.send_message(c.message.chat.id, desc)
    # --- ЧАСТЬ 3 ---

broadcast_cache = {}

def get_stats():
    # Подсчёт пользователей
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '24 hours'")
    day = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE registration_time >= NOW() - INTERVAL '48 hours'")
    two_days = cursor.fetchone()[0]

    return total, day, two_days

def admin_menu():
    """ Главное меню админа. """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📩 Рассылка", callback_data="admin_broadcast")
    )
    markup.add(
        types.InlineKeyboardButton("🔗 АПК-ссылки", callback_data="admin_apk"),
        types.InlineKeyboardButton("📢 Каналы", callback_data="admin_channels")
    )
    markup.add(
        types.InlineKeyboardButton("🎮 Игры", callback_data="admin_games"),
        types.InlineKeyboardButton("ℹ️ О модах", callback_data="admin_mods")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ Нет доступа.")
    bot.send_message(message.chat.id, "🛠 Админ-панель:", reply_markup=admin_menu())

@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def stats_callback(call):
    t, d, td = get_stats()
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{t}</b>\n"
        f"🕒 За 24 часа: <b>{d}</b>\n"
        f"🕒 За 48 часов: <b>{td}</b>"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=admin_menu())

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def ask_broadcast(call):
    bot.send_message(call.from_user.id, "✏️ Отправьте сообщение для рассылки.")
    broadcast_cache[call.from_user.id] = "wait"

@bot.message_handler(func=lambda m: broadcast_cache.get(m.from_user.id) == "wait")
def confirm_broadcast(msg):
    broadcast_cache[msg.from_user.id] = msg
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data="broadcast_confirm"))
    markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="broadcast_cancel"))
    bot.send_message(msg.chat.id, "Вы точно хотите отправить это сообщение всем?", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("broadcast_"))
def do_broadcast(call):
    if call.data == "broadcast_confirm":
        message_obj = broadcast_cache.get(call.from_user.id)
        cursor.execute("SELECT user_id FROM users")
        users_list = cursor.fetchall()
        s, f = 0, 0
        for (uid,) in users_list:
            try:
                bot.copy_message(uid, message_obj.chat.id, message_obj.message_id)
                s += 1
            except:
                f += 1
        bot.send_message(call.from_user.id, f"📬 Рассылка завершена.\n✅ Отправлено: {s}\n❌ Ошибок: {f}")
    else:
        bot.send_message(call.from_user.id, "🚫 Рассылка отменена.")
    broadcast_cache.pop(call.from_user.id, None)

# Заглушки для кнопок "admin_apk", "admin_channels", "admin_games", "admin_mods"
@bot.callback_query_handler(func=lambda c: c.data == "admin_apk")
def admin_apk_placeholder(call):
    bot.answer_callback_query(call.id, "Управление АПК-ссылками будет добавлено позже.")

@bot.callback_query_handler(func=lambda c: c.data == "admin_channels")
def admin_channels_placeholder(call):
    bot.answer_callback_query(call.id, "Управление каналами будет добавлено позже.")

@bot.callback_query_handler(func=lambda c: c.data == "admin_games")
def admin_games_placeholder(call):
    bot.answer_callback_query(call.id, "Управление играми будет добавлено позже.")

@bot.callback_query_handler(func=lambda c: c.data == "admin_mods")
def admin_mods_placeholder(call):
    bot.answer_callback_query(call.id, "Управление модами будет добавлено позже.")
    apk_stage = {}

@bot.callback_query_handler(func=lambda c: c.data == "admin_apk")
def admin_apk_main(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📄 Показать все", callback_data="apk_show"),
        types.InlineKeyboardButton("➕ Добавить", callback_data="apk_add"),
    )
    markup.add(
        types.InlineKeyboardButton("✏ Изменить", callback_data="apk_edit"),
        types.InlineKeyboardButton("❌ Удалить", callback_data="apk_delete"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_admin")
    )
    bot.edit_message_text("🔗 Управление АПК-ссылками:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "apk_show")
def apk_show_all(call):
    cursor.execute("SELECT game, system, url FROM apk_links")
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(call.from_user.id, "❌ Нет сохранённых АПК-ссылок.")
        return
    text = "📄 <b>Список АПК-ссылок:</b>\n"
    for game, system, url in rows:
        text += f"\n🎮 <b>{game}</b> | {system}\n🔗 {url}\n"
    bot.send_message(call.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "apk_add")
def apk_add_1(call):
    apk_stage[call.from_user.id] = {"step": "add_game"}
    bot.send_message(call.from_user.id, "🎮 Введите название игры:")

@bot.message_handler(func=lambda m: apk_stage.get(m.from_user.id, {}).get("step") == "add_game")
def apk_add_2(msg):
    apk_stage[msg.from_user.id]["game"] = msg.text
    apk_stage[msg.from_user.id]["step"] = "add_system"
    bot.send_message(msg.chat.id, "📱 Введите ОС (Android / iOS):")

@bot.message_handler(func=lambda m: apk_stage.get(m.from_user.id, {}).get("step") == "add_system")
def apk_add_3(msg):
    apk_stage[msg.from_user.id]["system"] = msg.text
    apk_stage[msg.from_user.id]["step"] = "add_url"
    bot.send_message(msg.chat.id, "🔗 Вставьте ссылку на АПК:")

@bot.message_handler(func=lambda m: apk_stage.get(m.from_user.id, {}).get("step") == "add_url")
def apk_add_finish(msg):
    data = apk_stage.pop(msg.from_user.id)
    game, system, url = data["game"], data["system"], msg.text
    try:
        cursor.execute("""INSERT INTO apk_links (game, system, url)
            VALUES (%s,%s,%s)
            ON CONFLICT (game, system) DO UPDATE SET url = EXCLUDED.url""", (game, system, url))
        bot.send_message(msg.chat.id, f"✅ Ссылка добавлена: {game} / {system}")
    except Exception as e:
        bot.send_message(msg.chat.id, "❌ Ошибка при добавлении")
        print("apk_add_finish error:", e)

@bot.callback_query_handler(func=lambda c: c.data == "apk_edit")
def apk_edit_1(call):
    apk_stage[call.from_user.id] = {"step": "edit_game"}
    bot.send_message(call.from_user.id, "🎮 Название игры, у которой хотите изменить ссылку:")

@bot.message_handler(func=lambda m: apk_stage.get(m.from_user.id, {}).get("step") == "edit_game")
def apk_edit_2(msg):
    apk_stage[msg.from_user.id]["game"] = msg.text
    apk_stage[msg.from_user.id]["step"] = "edit_system"
    bot.send_message(msg.chat.id, "📱 Какая ОС (Android / iOS)?")

@bot.message_handler(func=lambda m: apk_stage.get(m.from_user.id, {}).get("step") == "edit_system")
def apk_edit_3(msg):
    apk_stage[msg.from_user.id]["system"] = msg.text
    apk_stage[msg.from_user.id]["step"] = "edit_url"
    bot.send_message(msg.chat.id, "🔗 Введите новую ссылку:")

@bot.message_handler(func=lambda m: apk_stage.get(m.from_user.id, {}).get("step") == "edit_url")
def apk_edit_finish(msg):
    data = apk_stage.pop(msg.from_user.id)
    game, system = data["game"], data["system"]
    url = msg.text
    try:
        cursor.execute("UPDATE apk_links SET url = %s WHERE game = %s AND system = %s", (url, game, system))
        bot.send_message(msg.chat.id, f"✅ Ссылка изменена: {game} ({system})")
    except Exception as e:
        bot.send_message(msg.chat.id, "❌ Ошибка при изменении")
        print("apk_edit_finish:", e)

@bot.callback_query_handler(func=lambda c: c.data == "apk_delete")
def apk_delete_1(call):
    apk_stage[call.from_user.id] = {"step": "del_game"}
    bot.send_message(call.from_user.id, "🗑 Введите название игры, чтобы удалить ВСЕ ссылки игры:")

@bot.message_handler(func=lambda m: apk_stage.get(m.from_user.id, {}).get("step") == "del_game")
def apk_delete_finish(msg):
    game = msg.text
    apk_stage.pop(msg.from_user.id, None)
    cursor.execute("DELETE FROM apk_links WHERE game = %s", (game,))
    bot.send_message(msg.chat.id, f"🗑 Все ссылки для игры '{game}' удалены.")
    channel_stage = {}
channel_mode = {}

@bot.callback_query_handler(func=lambda c: c.data == "admin_channels")
def admin_channels_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📄 Показать все", callback_data="chan_show_all"),
        types.InlineKeyboardButton("➕ Добавить", callback_data="chan_add"),
    )
    markup.add(
        types.InlineKeyboardButton("✏ Изменить", callback_data="chan_edit"),
        types.InlineKeyboardButton("❌ Удалить", callback_data="chan_del"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_admin")
    )
    bot.edit_message_text("📢 Управление каналами:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "chan_show_all")
def chan_show_all(call):
    cursor.execute("SELECT name, url FROM required_channels")
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(call.from_user.id, "❗ Каналы не добавлены.")
        return
    text = "<b>📢 Список каналов:</b>\n\n"
    for name, url in rows:
        text += f"• <b>{name}</b>: {url}\n"
    bot.send_message(call.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "chan_add")
def chan_add_step1(call):
    channel_stage[call.from_user.id] = {"step": "add_name"}
    bot.send_message(call.from_user.id, "🆕 Введите название канала:")

@bot.message_handler(func=lambda m: channel_stage.get(m.from_user.id, {}).get("step") == "add_name")
def chan_add_step2(msg):
    channel_stage[msg.from_user.id]["name"] = msg.text
    channel_stage[msg.from_user.id]["step"] = "add_url"
    bot.send_message(msg.chat.id, "🔗 Введите ссылку на канал:")

@bot.message_handler(func=lambda m: channel_stage.get(m.from_user.id, {}).get("step") == "add_url")
def chan_add_finish(msg):
    data = channel_stage.pop(msg.from_user.id)
    name = data["name"]
    url = msg.text
    try:
        cursor.execute("INSERT INTO required_channels (name, url) VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET url = EXCLUDED.url", (name, url))
        bot.send_message(msg.chat.id, f"✅ Канал '{name}' добавлен/обновлён.")
    except Exception as e:
        bot.send_message(msg.chat.id, "❌ Ошибка при добавлении канала.")
        print("chan_add_finish:", e)

@bot.callback_query_handler(func=lambda c: c.data == "chan_del")
def chan_del_1(call):
    channel_mode[call.from_user.id] = "delete"
    bot.send_message(call.from_user.id, "🗑 Введите точное название канала для удаления:")

@bot.message_handler(func=lambda m: channel_mode.get(m.from_user.id) == "delete")
def chan_del_finish(msg):
    name = msg.text
    try:
        cursor.execute("DELETE FROM required_channels WHERE name = %s", (name,))
        bot.send_message(msg.chat.id, f"✅ Канал '{name}' удалён.")
    except Exception as e:
        bot.send_message(msg.chat.id, "❌ Ошибка при удалении канала.")
        print("chan_del_finish:", e)
    channel_mode.pop(msg.from_user.id, None)

@bot.callback_query_handler(func=lambda c: c.data == "chan_edit")
def chan_edit_1(call):
    channel_stage[call.from_user.id] = {"step": "edit_name"}
    bot.send_message(call.from_user.id, "✏ Введите название канала, который хотите изменить:")

@bot.message_handler(func=lambda m: channel_stage.get(m.from_user.id, {}).get("step") == "edit_name")
def chan_edit_2(msg):
    channel_stage[msg.from_user.id]["name"] = msg.text
    channel_stage[msg.from_user.id]["step"] = "edit_url"
    bot.send_message(msg.chat.id, "🔗 Введите новую ссылку на канал:")

@bot.message_handler(func=lambda m: channel_stage.get(m.from_user.id, {}).get("step") == "edit_url")
def chan_edit_finish(msg):
    data = channel_stage.pop(msg.from_user.id)
    name = data["name"]
    new_url = msg.text
    try:
        cursor.execute("UPDATE required_channels SET url = %s WHERE name = %s", (new_url, name))
        bot.send_message(msg.chat.id, f"✅ Канал '{name}' обновлён.")
    except Exception as e:
        bot.send_message(msg.chat.id, "❌ Ошибка при изменении канала.")
        print("chan_edit_finish:", e)
        game_stage = {}

@bot.callback_query_handler(func=lambda c: c.data == "admin_games")
def admin_games_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📄 Показать все", callback_data="games_show"),
        types.InlineKeyboardButton("➕ Добавить", callback_data="games_add"),
        types.InlineKeyboardButton("❌ Удалить", callback_data="games_delete")
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_admin"))
    bot.edit_message_text("🎮 Управление играми:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "games_show")
def games_show_all(call):
    cursor.execute("SELECT name FROM games")
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(call.from_user.id, "❗ Нет игр.")
        return
    text = "🎮 <b>Список игр:</b>\n\n" + "\n".join(f"• {r[0]}" for r in rows)
    bot.send_message(call.from_user.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "games_add")
def games_add_1(call):
    game_stage[call.from_user.id] = "adding"
    bot.send_message(call.from_user.id, "✏ Введите название новой игры:")

@bot.message_handler(func=lambda m: game_stage.get(m.from_user.id) == "adding")
def games_add_finish(msg):
    name = msg.text
    try:
        cursor.execute("INSERT INTO games (name) VALUES (%s) ON CONFLICT DO NOTHING", (name,))
        bot.send_message(msg.chat.id, f"✅ Игра '{name}' добавлена.")
    except Exception as e:
        bot.send_message(msg.chat.id, "❌ Ошибка при добавлении игры.")
        print("games_add_finish:",
