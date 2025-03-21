import telebot
import requests
from telebot import types

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Каналы
NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}  # Первый канал без проверки
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
        "iOS": None  # Нет версии для iOS
    }
}

# Текст для отправки другу
SHARE_TEXT = "– мой любимый бесплатный чит на Oxide: Survival Island! ❤️"

# Словарь для хранения выбора пользователей
user_data = {}

# Проверка подписки
def is_subscribed(user_id):
    for channel_name, channel_link in REQUIRED_CHANNELS.items():
        channel_username = channel_link.split("/")[-1]
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{channel_username}&user_id={user_id}"
        response = requests.get(url).json()
        status = response.get('result', {}).get('status')
        if status not in ['member', 'administrator', 'creator']:
            return False  
    return True  

# Обработчик команды /start (выбор игры)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":
        return  

    user_id = message.from_user.id
    user_data[user_id] = {}

    markup = types.InlineKeyboardMarkup()
    oxide_button = types.InlineKeyboardButton("Oxide: Survival Island", callback_data="game_oxide")
    standoff_button = types.InlineKeyboardButton("Standoff 2", callback_data="game_standoff")
    markup.add(oxide_button, standoff_button)

    bot.send_message(message.chat.id, "🎮 *Выберите игру, для которой хотите получить мод:*", parse_mode="Markdown", reply_markup=markup)

# Обработчик выбора игры
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def select_game(call):
    user_id = call.from_user.id
    game = "Oxide" if call.data == "game_oxide" else "Standoff 2"
    user_data[user_id]["game"] = game

    markup = types.InlineKeyboardMarkup()
    android_button = types.InlineKeyboardButton("📱 Android", callback_data="system_android")
    ios_button = types.InlineKeyboardButton("🍏 iOS", callback_data="system_ios")
    markup.add(android_button, ios_button)

    bot.edit_message_text("🔹 *Выберите вашу систему:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# Обработчик выбора ОС
@bot.callback_query_handler(func=lambda call: call.data.startswith("system_"))
def select_system(call):
    user_id = call.from_user.id
    system = "Android" if call.data == "system_android" else "iOS"
    user_data[user_id]["system"] = system

    game = user_data[user_id].get("game")
    if not game:
        bot.send_message(call.message.chat.id, "❌ Ошибка! Вы не выбрали игру.")
        return

    apk_link = APK_LINKS.get(game, {}).get(system)
    if apk_link:
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [types.InlineKeyboardButton(name, url=link) for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items()]
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))

        bot.edit_message_text(
            "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
            call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup
        )
    else:
        bot.edit_message_text(
            "❌ *Извините, но APK для данной игры и платформы пока недоступен.*",
            call.message.chat.id, call.message.message_id, parse_mode="Markdown"
        )

# Проверка подписки
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id
    game = user_data.get(user_id, {}).get("game")
    system = user_data.get(user_id, {}).get("system")

    if not game or not system:
        bot.send_message(call.message.chat.id, "❌ Ошибка! Вы не выбрали игру или систему.")
        return

    apk_link = APK_LINKS.get(game, {}).get(system)
    if not apk_link:
        bot.send_message(call.message.chat.id, "❌ Ошибка! APK для данной игры недоступен.")
        return

    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT)
        about_button = types.InlineKeyboardButton("ℹ️ Об моде", callback_data="about_mod")
        markup.add(share_button)
        markup.add(about_button)

        bot.edit_message_text(
            f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
            f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({apk_link})\n\n"
            f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
            call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup
        )
    else:
        bot.send_message(
            call.message.chat.id,
            "❌ *Вы ещё не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
            parse_mode="Markdown"
        )

# Обработчик кнопки "ℹ️ Об моде"
@bot.callback_query_handler(func=lambda call: call.data == "about_mod")
def about_mod(call):
    user_id = call.from_user.id
    game = user_data.get(user_id, {}).get("game", "неизвестной игры")

    markup = types.InlineKeyboardMarkup()
    back_button = types.InlineKeyboardButton("🔙 Назад", callback_data="check_subscription")
    markup.add(back_button)

    bot.edit_message_text(
        f"ℹ️ *Информация*\n\nИнформация о моде для {game} временно отсутствует.",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup
    )

# Обработка неверных команд (только в ЛС)
@bot.message_handler(func=lambda message: message.chat.type == "private")
def handle_unknown_command(message):
    bot.send_message(
        message.chat.id,
        "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Бот запущен! Ожидаем команды...")
    bot.infinity_polling()
