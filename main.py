import telebot
import requests
from telebot import types

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Канал без проверки (должен идти первым)
NO_CHECK_CHANNEL = {
    "🔥 Приватный канал": "https://t.me/+i54KtE7dZ9I1NTJi"
}

# Каналы для проверки подписки
REQUIRED_CHANNELS = {
    "Chat By Oxide": "https://t.me/ChatByOxide",
    "Oxide Vzlom": "https://t.me/Oxide_Vzlom"
}

# Проверка подписки пользователя
def is_subscribed(user_id):
    for channel_name, channel_link in REQUIRED_CHANNELS.items():
        channel_username = channel_link.split("/")[-1]  # Получаем @username канала
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{channel_username}&user_id={user_id}"
        response = requests.get(url).json()
        
        status = response.get('result', {}).get('status')
        if status not in ['member', 'administrator', 'creator']:
            return False  # Если пользователь не подписан хотя бы на один канал
    
    return True  # Если подписка есть на все каналы

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id

    if is_subscribed(user_id):
        bot.send_message(message.chat.id, f"✅ Спасибо за подписку! Вот ваша ссылка на закрытый канал:\n{NO_CHECK_CHANNEL['🔥 Приватный канал']}")
    else:
        markup = types.InlineKeyboardMarkup(row_width=3)

        # Сначала добавляем канал без проверки
        for name, link in NO_CHECK_CHANNEL.items():
            markup.add(types.InlineKeyboardButton(name, url=link))

        # Затем каналы с проверкой
        buttons = [types.InlineKeyboardButton(name, url=link) for name, link in REQUIRED_CHANNELS.items()]
        markup.add(*buttons)

        # Кнопка "Проверить подписку"
        check_button = types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription")
        markup.add(check_button)

        bot.send_message(
            message.chat.id,
            "📢 Чтобы получить доступ к моду, подпишитесь на каналы ниже.\nПосле подписки нажмите \"✅ Проверить подписку\".",
            reply_markup=markup
        )

# Обработчик кнопки "Проверить подписку"
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id

    if is_subscribed(user_id):
        bot.send_message(call.message.chat.id, f"✅ Спасибо за подписку! Вот ваша ссылка на закрытый канал:\n{NO_CHECK_CHANNEL['🔥 Приватный канал']}")
    else:
        bot.answer_callback_query(call.id, "❌ Вы ещё не подписаны на все каналы!")

if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling()
