import telebot
from telebot import types
import requests
from datetime import datetime

# Токен твоего бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Информация об играх
GAME_INFO = {
    "Oxide Survival Island": {
        "link": "https://t.me/+X5HG9ZCxbhc4OTIy",
        "description": "Игра на выживание на острове с реалистичной графикой и возможностью построить свой мир."
    },
    "Black Russia": {
        "link": "https://t.me/+NFv32i5jI542Mjg6",
        "description": "Мультиплеерная игра с возможностью взаимодействовать с другими игроками."
    },
    "Standoff 2": {
        "link": None,
        "description": "Популярный шутер с режимами PvP и реалистичной графикой."
    },
    "Brawl Stars": {
        "link": None,
        "description": "Мультиплеерная игра с быстрыми битвами и различными героями."
    }
}

# Канал для проверки подписки
CHANNEL = "@Oxide_Vzlom"

# Данные пользователей (временное хранилище)
user_data = {}

# Проверка подписки
def is_subscribed(user_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL}&user_id={user_id}"
    response = requests.get(url).json()
    return response.get('result', {}).get('status') in ['member', 'administrator', 'creator']

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Список игр", "Профиль", "Помощь", "Техподдержка", "О нас"]
    markup.add(*buttons)
    return markup

# Стартовое сообщение
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {
            "username": message.from_user.username,
            "registration_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "referral_link": f"https://t.me/{bot.get_me().username}?start={user_id}"
        }
    bot.send_message(
        message.chat.id,
        "Добро пожаловать! Выберите пункт меню:",
        reply_markup=main_menu()
    )

# Обработка текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if not is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"Пожалуйста, подпишитесь на канал {CHANNEL}, чтобы использовать бота."
        )
        return

    if message.text == "Список игр":
        markup = types.InlineKeyboardMarkup()
        for game in GAME_INFO:
            markup.add(types.InlineKeyboardButton(text=game, callback_data=f"game_{game}"))
        bot.send_message(message.chat.id, "Выберите игру:", reply_markup=markup)

    elif message.text == "Профиль":
        data = user_data.get(message.from_user.id, {})
        reply = (
            f"Ваш профиль:\n"
            f"Имя пользователя: @{data.get('username', 'не указано')}\n"
            f"Дата регистрации: {data.get('registration_time', 'неизвестна')}\n"
            f"Реферальная ссылка: {data.get('referral_link', 'отсутствует')}"
        )
        bot.send_message(message.chat.id, reply)

    elif message.text == "Помощь":
        bot.send_message(message.chat.id, "Если нужна помощь, напишите в Техподдержку.")

    elif message.text == "Техподдержка":
        bot.send_message(message.chat.id, "Свяжитесь с нами через: @Oxide_Vzlom")

    elif message.text == "О нас":
        bot.send_message(message.chat.id, "Мы создаём игровые проекты для вас!")

# Обработка кнопок с играми
@bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
def game_callback(call):
    game_name = call.data.replace("game_", "")
    game = GAME_INFO.get(game_name, {})
    description = game.get("description", "Нет описания.")
    link = game.get("link")

    reply = f"Игра: {game_name}\nОписание: {description}\n"
    if link:
        reply += f"[Скачать игру]({link})"
        bot.send_message(call.message.chat.id, reply, parse_mode='Markdown')
    else:
        reply += "Ссылка на скачивание недоступна."
        bot.send_message(call.message.chat.id, reply)

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен")
    bot.infinity_polling()
