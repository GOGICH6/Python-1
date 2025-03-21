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
DOWNLOAD_CHANNEL_LINK = "https://t.me/+dxcSK08NRmxjNWRi"  # Ссылка после подписки

# Список игр и ссылки на APK
GAMES = {
    "Oxide: Survival Island": {
        "Android": "https://example.com/oxide_android.apk",
        "iOS": None
    },
    "Standoff 2": {
        "Android": "https://example.com/standoff2_android.apk",
        "iOS": "https://example.com/standoff2_ios.ipa"
    }
}

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

# Ловим /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != "private":  
        return  

    user_id = message.from_user.id

    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(game, callback_data=f"game_{game}") for game in GAMES]
        markup.add(*buttons)

        bot.send_message(
            message.chat.id, 
            "🎮 *Выберите игру, для которой хотите получить мод:*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [types.InlineKeyboardButton(name, url=link) for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items()]
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription"))

        bot.send_message(
            message.chat.id,
            "📢 *Чтобы получить доступ к моду, подпишитесь на каналы ниже.*\nПосле подписки нажмите *\"✅ Проверить подписку\".*",
            parse_mode="Markdown",
            reply_markup=markup
        )

# Выбор ОС
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def choose_os(call):
    game_name = call.data.replace("game_", "")

    markup = types.InlineKeyboardMarkup()
    android_button = types.InlineKeyboardButton("📱 Android", callback_data=f"os_Android_{game_name}")
    ios_button = types.InlineKeyboardButton("🍏 iOS", callback_data=f"os_iOS_{game_name}")
    markup.add(android_button, ios_button)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🔷 *Выберите вашу систему:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Выдача ссылки на APK
@bot.callback_query_handler(func=lambda call: call.data.startswith("os_"))
def send_apk_link(call):
    _, os_type, game_name = call.data.split("_")

    if GAMES[game_name][os_type]:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ *Вот ваша ссылка для {os_type}:*\n\n🔗 {GAMES[game_name][os_type]}",
            parse_mode="Markdown"
        )
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ *К сожалению, APK недоступен для этой платформы!*",
            parse_mode="Markdown"
        )

# Проверка подписки
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id

    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(game, callback_data=f"game_{game}") for game in GAMES]
        markup.add(*buttons)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🎮 *Выберите игру, для которой хотите получить мод:*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            call.message.chat.id,
            "❌ *Вы ещё не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    print("Бот запущен! Ожидаем команды...")
    bot.infinity_polling()
