import telebot
import requests
from telebot import types

TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Доступные игры
GAMES = {
    "Oxide: Survival Island": "Oxide",
    "Standoff 2": "Standoff"
}

# Каналы
NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}  # Первый канал без проверки
REQUIRED_CHANNELS = {
    "2 канал": "https://t.me/ChatByOxide",
    "3 канал": "https://t.me/Oxide_Vzlom"
}
DOWNLOAD_CHANNEL_LINK = "https://t.me/+dxcSK08NRmxjNWRi"  # Ссылка после подписки

# Доступные APK (если нет, бот выдаст ошибку)
AVAILABLE_APKS = {
    "Oxide": ["Android", "iOS"],
    "Standoff": ["Android"]
}

# Текст для отправки другу
SHARE_TEXT = "– мой любимый бесплатный чит на Oxide: Survival Island! ❤️"

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

# Ловим /start (только в личных сообщениях)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":  
        return  

    print(f"Команда /start от {message.from_user.id}")  
    user_id = message.from_user.id

    markup = types.InlineKeyboardMarkup()
    for game_name in GAMES.keys():
        markup.add(types.InlineKeyboardButton(game_name, callback_data=f"game_{GAMES[game_name]}"))
    
    bot.send_message(
        message.chat.id,
        "🎮 *Выберите игру, для которой хотите получить мод:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Обрабатываем выбор игры
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def game_selected(call):
    game_key = call.data.split("_")[1]
    markup = types.InlineKeyboardMarkup()
    
    # Спрашиваем ОС
    for os_type in ["Android", "iOS", "Windows"]:
        markup.add(types.InlineKeyboardButton(os_type, callback_data=f"os_{game_key}_{os_type}"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📱 *Выберите вашу операционную систему:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Обрабатываем выбор ОС
@bot.callback_query_handler(func=lambda call: call.data.startswith("os_"))
def os_selected(call):
    _, game_key, os_type = call.data.split("_")

    if os_type not in AVAILABLE_APKS.get(game_key, []):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ *К сожалению, мод для этой ОС недоступен.*",
            parse_mode="Markdown"
        )
        return

    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(name, url=link) for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items()]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data=f"check_subscription_{game_key}_{os_type}"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Проверка подписки
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_subscription_"))
def check_subscription(call):
    user_id = call.from_user.id

    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT)  
        markup.add(share_button)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
            f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({DOWNLOAD_CHANNEL_LINK})\n\n"
            f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Вы ещё не подписаны на все каналы! Подпишитесь и попробуйте снова.",
            show_alert=True
        )

# Обработка неверных команд (только в ЛС)
@bot.message_handler(func=lambda message: message.chat.type == "private")
def handle_unknown_command(message):
    user_id = message.from_user.id

    if is_subscribed(user_id):
        bot.send_message(message.chat.id, "🤖 *Я вас не понял!* Используйте команду /start, чтобы начать.", parse_mode="Markdown")
    else:
        bot.send_message(
            message.chat.id,
            "⚠ *Вы не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    print("Бот запущен! Ожидаем команды...")
    bot.infinity_polling()
