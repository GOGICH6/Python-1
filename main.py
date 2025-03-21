import telebot
from telebot import types
import psycopg2

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Каналы для подписки
# Обязательный канал (проверяется)
REQUIRED_CHANNEL = {"Oxide_Vzlom": "https://t.me/Oxide_Vzlom"}
# Необязательный (информационный) канал (не проверяется)
OPTIONAL_CHANNEL = {"ChatByOxide": "https://t.me/ChatByOxide"}

# Ссылки на моды по игре и платформе
download_links = {
    "Oxide": {
        "Android": "https://t.me/+dxcSK08NRmxjNWRi",
        "iOS": "https://t.me/+U3QzhcTHKv1lNmMy"
    },
    "Standoff2": {
        "Android": "https://t.me/+fgN29Y8PjTNhZWFi",
        "iOS": None  # нет ссылки для iOS
    }
}

# Текст для кнопки «📤 Отправить другу» (отдельно для каждой игры)
share_texts = {
    "Oxide": "– мой любимый бесплатный чит на Oxide: Survival Island! ❤️",
    "Standoff2": "– мой любимый бесплатный чит на Standoff 2! ❤️"
}

# Описание модов (если отсутствует, будет выведено сообщение)
mod_info = {
    "Oxide": None,
    "Standoff2": None
}

# Словари для хранения выбранной пользователем игры и платформы
user_game = {}    # user_id -> игра
user_system = {}  # user_id -> платформа

# Функция проверки подписки на обязательный канал
def is_subscribed_to_required(user_id):
    for _, channel_link in REQUIRED_CHANNEL.items():
        # Получаем username канала из ссылки
        if channel_link.startswith("https://t.me/"):
            username = channel_link.split("/")[-1]
        else:
            username = channel_link
        try:
            member = bot.get_chat_member(f"@{username}", user_id)
            status = member.status
        except Exception as e:
            # В случае ошибки (бот не админ в канале или нет доступа)
            print(f"Ошибка проверки подписки для user {user_id} в {username}: {e}")
            return False
        if status not in ['member', 'administrator', 'creator']:
            return False
    return True

# Обработчик команды /start (выбор игры)
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.type != "private":
        return  # Игнорировать команды вне личных сообщений
    # Клавиатура выбора игры
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Oxide", callback_data="select_game_oxide")
    btn2 = types.InlineKeyboardButton("Standoff 2", callback_data="select_game_standoff")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "🎮 *Выберите игру:*", parse_mode="Markdown", reply_markup=markup)

# Обработчик выбора игры
@bot.callback_query_handler(func=lambda call: call.data in ["select_game_oxide", "select_game_standoff"])
def callback_select_game(call):
    user_id = call.from_user.id
    # Определяем выбранную игру
    game = "Oxide" if call.data == "select_game_oxide" else "Standoff2"
    user_game[user_id] = game
    # После выбора игры запрашиваем выбор платформы
    markup = types.InlineKeyboardMarkup()
    btn_android = types.InlineKeyboardButton("📱 Android", callback_data="select_android")
    btn_ios = types.InlineKeyboardButton("🍏 iOS", callback_data="select_ios")
    markup.add(btn_android, btn_ios)
    bot.send_message(call.message.chat.id, "🔹 *Выберите вашу систему:*", parse_mode="Markdown", reply_markup=markup)

# Обработчик выбора платформы (Android или iOS)
@bot.callback_query_handler(func=lambda call: call.data in ["select_android", "select_ios"])
def callback_select_platform(call):
    user_id = call.from_user.id
    platform = "Android" if call.data == "select_android" else "iOS"
    user_system[user_id] = platform
    # Получаем выбранную игру пользователя
    game = user_game.get(user_id, "Oxide")
    # Проверяем наличие ссылки на мод для этой игры и платформы
    link = download_links.get(game, {}).get(platform)
    if link:
        # Если ссылка есть, предлагаем подписаться на каналы
        markup = types.InlineKeyboardMarkup()
        # Кнопки на каналы (сначала обязательный, затем информационный)
        for name, url in REQUIRED_CHANNEL.items():
            markup.add(types.InlineKeyboardButton(f"📢 {name}", url=url))
        for name, url in OPTIONAL_CHANNEL.items():
            markup.add(types.InlineKeyboardButton(f"📢 {name}", url=url))
        # Кнопка проверки подписки
        markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))
        bot.send_message(call.message.chat.id,
                         "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\n"
                         "После подписки нажмите *\"✅ Проверить подписку\".*",
                         parse_mode="Markdown", reply_markup=markup)
    else:
        # Если ссылки нет (мод недоступен для данной платформы)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_start"))
        bot.send_message(call.message.chat.id,
                         "❌ К сожалению, мод для этой платформы временно отсутствует.",
                         reply_markup=markup)

# Обработчик кнопки "✅ Проверить подписку"
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check_subscription(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if is_subscribed_to_required(user_id):
        # Пользователь подписан – сохраняем его в базе данных
        try:
            conn = psycopg2.connect("postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require")
            cur = conn.cursor()
            # Создаем таблицу users, если не существует
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    reg_date TIMESTAMP DEFAULT NOW()
                );
            """)
            # Вставляем запись о пользователе (если такой user_id уже есть, ничего не делаем)
            cur.execute("""
                INSERT INTO users (user_id, reg_date)
                VALUES (%s, NOW())
                ON CONFLICT (user_id) DO NOTHING;
            """, (user_id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Ошибка базы данных при регистрации пользователя {user_id}: {e}")
        # Отправляем ссылку на скачивание и дополнительные кнопки
        game = user_game.get(user_id, "Oxide")
        platform = user_system.get(user_id, "Android")
        download_link = download_links.get(game, {}).get(platform)
        # Кнопки: отправить другу, об моде, техподдержка, назад
        markup = types.InlineKeyboardMarkup(row_width=2)
        share_text = share_texts.get(game, "")
        btn_share = types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=share_text)
        btn_info = types.InlineKeyboardButton("ℹ️ Об моде", callback_data="info_mod")
        support_link = OPTIONAL_CHANNEL.get("ChatByOxide") or next(iter(OPTIONAL_CHANNEL.values()), None)
        if support_link:
            btn_support = types.InlineKeyboardButton("💬 Техподдержка", url=support_link)
        else:
            btn_support = types.InlineKeyboardButton("💬 Техподдержка", callback_data="support_info")
        btn_back = types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")
        markup.add(btn_share, btn_info, btn_support, btn_back)
        bot.send_message(chat_id,
                         f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
                         f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({download_link})\n\n"
                         f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
                         parse_mode="Markdown", reply_markup=markup)
    else:
        # Пользователь не подписан на обязательный канал
        bot.send_message(chat_id,
                         "❌ *Вы ещё не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
                         parse_mode="Markdown")

# Обработчик кнопки "ℹ️ Об моде"
@bot.callback_query_handler(func=lambda call: call.data == "info_mod")
def callback_mod_info(call):
    user_id = call.from_user.id
    game = user_game.get(user_id)
    info_text = mod_info.get(game)
    if info_text:
        bot.send_message(call.message.chat.id, info_text)
    else:
        bot.send_message(call.message.chat.id, "Информация о моде временно отсутствует.")

# Обработчик кнопки "💬 Техподдержка" (в случае отсутствия прямой ссылки)
@bot.callback_query_handler(func=lambda call: call.data == "support_info")
def callback_support_info(call):
    bot.send_message(call.message.chat.id,
                     "Для технической поддержки обращайтесь в наш чат: @ChatByOxide.")

# Обработчик кнопки "🔙 Назад" (возврат к выбору игры)
@bot.callback_query_handler(func=lambda call: call.data == "back_to_start")
def callback_back_to_start(call):
    chat_id = call.message.chat.id
    # Выводим заново меню выбора игры (то же, что при /start)
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Oxide", callback_data="select_game_oxide")
    btn2 = types.InlineKeyboardButton("Standoff 2", callback_data="select_game_standoff")
    markup.add(btn1, btn2)
    bot.send_message(chat_id, "🎮 *Выберите игру:*", parse_mode="Markdown", reply_markup=markup)

# Обработчик команды /admin (статистика)
@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    if user_id != 1903057676:
        # Если не админ, выводим сообщение об неизвестной команде
        bot.send_message(message.chat.id,
                         "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.",
                         parse_mode="Markdown")
        return
    # Получение статистики из базы данных
    try:
        conn = psycopg2.connect("postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users;")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE reg_date >= NOW() - INTERVAL '24 hours';")
        last_24h = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE reg_date >= NOW() - INTERVAL '48 hours';")
        last_48h = cur.fetchone()[0]
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка базы данных при выполнении /admin пользователем {user_id}: {e}")
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")
        return
    # Отправляем статистику администратору
    stats_message = (f"Всего пользователей: {total_users}\n"
                     f"За 24 часа: {last_24h}\n"
                     f"За 48 часов: {last_48h}")
    bot.send_message(message.chat.id, stats_message)

# Обработчик остальных сообщений (неизвестные команды)
@bot.message_handler(func=lambda message: message.chat.type == "private")
def fallback_message(message):
    # Игнорируем известные команды, которые обрабатываются отдельно
    if message.text and message.text.startswith('/'):
        cmd = message.text.split()[0][1:].split('@')[0].lower()
        if cmd in ['start', 'admin']:
            return
    bot.send_message(message.chat.id,
                     "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.",
                     parse_mode="Markdown")

if __name__ == "__main__":
    # Инициализация базы данных (создание таблицы при запуске)
    try:
        conn = psycopg2.connect("postgresql://neondb_owner:npg_G3VCfRiD0uwB@ep-late-sunset-a5ktl08d-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                reg_date TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка инициализации базы данных: {e}")
    print("Бот запущен! Ожидаем команды...")
    bot.infinity_polling()
                                
