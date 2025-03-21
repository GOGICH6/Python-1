import telebot
import requests
from telebot import types

TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Игры и их доступные APK
GAMES = {
    "Oxide: Survival Island": {
        "key": "Oxide",
        "available_apks": ["Android", "iOS"]
    },
    "Standoff 2": {
        "key": "Standoff",
        "available_apks": ["Android"]
    }
}

# Каналы
NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}  
REQUIRED_CHANNELS = {
    "2 канал": "https://t.me/ChatByOxide",
    "3 канал": "https://t.me/Oxide_Vzlom"
}
DOWNLOAD_CHANNEL_LINK = "https://t.me/+dxcSK08NRmxjNWRi"

# Текст для отправки другу
SHARE_TEXT = "– мой любимый бесплатный чит на Oxide: Survival Island! ❤️"

# Хранение ID сообщений для удаления
user_messages = {}

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

# Удаление старых сообщений перед отправкой нового
def delete_old_message(chat_id):
    if chat_id in user_messages:
        try:
            bot.delete_message(chat_id, user_messages[chat_id])
        except:
            pass

# Ловим /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":  
        return  

    delete_old_message(message.chat.id)

    markup = types.InlineKeyboardMarkup()
    for game_name in GAMES.keys():
        markup.add(types.InlineKeyboardButton(game_name, callback_data=f"game_{GAMES[game_name]['key']}"))
    
    sent_msg = bot.send_message(
        message.chat.id,
        "🎮 *Выберите игру, для которой хотите получить мод:*",
        parse_mode="Markdown",
        reply_markup=markup
    )
    user_messages[message.chat.id] = sent_msg.message_id

# Обрабатываем выбор игры
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def game_selected(call):
    delete_old_message(call.message.chat.id)

    game_key = call.data.split("_")[1]
    game_name = next((name for name, data in GAMES.items() if data["key"] == game_key), None)

    if not game_name:
        bot.answer_callback_query(call.id, "Ошибка выбора игры!")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for os_type in ["Android", "iOS", "Windows"]:
        emoji = "📱" if os_type == "Android" else "🍏" if os_type == "iOS" else "💻"
        markup.add(types.InlineKeyboardButton(f"{emoji} {os_type}", callback_data=f"os_{game_key}_{os_type}"))

    sent_msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🔷 *Выберите вашу систему:*",
        parse_mode="Markdown",
        reply_markup=markup
    )
    user_messages[call.message.chat.id] = sent_msg.message_id

# Обрабатываем выбор ОС
@bot.callback_query_handler(func=lambda call: call.data.startswith("os_"))
def os_selected(call):
    delete_old_message(call.message.chat.id)

    _, game_key, os_type = call.data.split("_")

    game_data = next((data for name, data in GAMES.items() if data["key"] == game_key), None)

    if not game_data:
        bot.answer_callback_query(call.id, "Ошибка выбора ОС!")
        return

    if os_type not in game_data["available_apks"]:
        sent_msg = bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ *К сожалению, мод для этой ОС недоступен.*",
            parse_mode="Markdown"
        )
        user_messages[call.message.chat.id] = sent_msg.message_id
        return

    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(name, url=link) for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items()]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data=f"check_subscription_{game_key}_{os_type}"))

    sent_msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
        parse_mode="Markdown",
        reply_markup=markup
    )
    user_messages[call.message.chat.id] = sent_msg.message_id

# Проверка подписки
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_subscription_"))
def check_subscription(call):
    delete_old_message(call.message.chat.id)

    user_id = call.from_user.id

    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT)  
        markup.add(share_button)

        sent_msg = bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
            f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({DOWNLOAD_CHANNEL_LINK})\n\n"
            f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
            parse_mode="Markdown",
            reply_markup=markup
        )
        user_messages[call.message.chat.id] = sent_msg.message_id
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Вы ещё не подписаны на все каналы! Подпишитесь и попробуйте снова.",
            show_alert=True
        )

# Обработка неверных команд (только в ЛС)
@bot.message_handler(func=lambda message: message.chat.type == "private")
def handle_unknown_command(message):
    delete_old_message(message.chat.id)

    user_id = message.from_user.id

    if is_subscribed(user_id):
        sent_msg = bot.send_message(message.chat.id, "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.", parse_mode="Markdown")
        user_messages[message.chat.id] = sent_msg.message_id
    else:
        sent_msg = bot.send_message(
            message.chat.id,
            "⚠ *Вы не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
            parse_mode="Markdown"
        )
        user_messages[message.chat.id] = sent_msg.message_id

if __name__ == "__main__":
    print("Бот запущен! Ожидаем команды...")
    bot.infinity_polling()
