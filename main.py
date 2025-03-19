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

    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT)  # Теперь точно как надо
        markup.add(share_button)

        bot.send_message(
            message.chat.id, 
            f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
            f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({DOWNLOAD_CHANNEL_LINK})\n\n"
            f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
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

# Проверка подписки (отправляет сообщение в чат, а не всплывающее уведомление)
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id

    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT)  # Теперь точно как надо
        markup.add(share_button)

        bot.send_message(
            call.message.chat.id, 
            f"✅ *Вы успешно подписались на все каналы и прошли регистрацию!*\n\n"
            f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({DOWNLOAD_CHANNEL_LINK})\n\n"
            f"⚠ *Важно!* Не отписывайтесь от каналов, иначе бот может посчитать вас мошенником и *добавить в ЧС во всех каналах!*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            call.message.chat.id,
            "❌ *Вы ещё не подписаны на все каналы!* Подпишитесь и нажмите \"✅ Проверить подписку\" снова.",
            parse_mode="Markdown"
        )

# Обработка неверных команд (только в ЛС)
@bot.message_handler(func=lambda message: message.chat.type == "private")
def handle_unknown_command(message):
    user_id = message.from_user.id

    if is_subscribed(user_id):  # Если подписан, но отправил неизвестную команду
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
