import telebot
from telebot import types
import requests
from flask import Flask
from threading import Thread
from datetime import datetime

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Информация о всех играх и ссылки для скачивания
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
CHANNEL = {
    "name": "Oxide Vzlom",
    "link": "https://t.me/Oxide_Vzlom",
    "username": "@Oxide_Vzlom"
}

# Временное хранилище данных пользователей
user_data = {}

# Проверка подписки на канал
def is_subscribed(user_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL['username']}&user_id={user_id}"
    response = requests.get(url).json()
    if response.get('result', {}).get('status') in ['member', 'administrator', 'creator']:
        return True
    return False

# Приветственное сообщение и основное меню
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {
            "username": message.from_user.username,
            "registration_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "invites": 0,
            "referral_link": f"https://t.me/{bot.get_me().username}?start={user_id}"
        }

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Список игр", "Профиль", "Помощь", "Техподдержка", "О нас"]
    markup.add(*[types.KeyboardButton(button) for button in buttons])
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите один из пунктов ниже.", reply_markup=markup)

# Обработчик для кнопки "Список игр"
@bot.message_handler(func=lambda message: message.text == "Список игр")
def show_game_list(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for game in GAME_INFO.keys():
        markup.add(types.KeyboardButton(game))
    markup.add(types.KeyboardButton("Назад"))
    bot.send_message(message.chat.id, "Выберите нужную игру:", reply_markup=markup)

# Информация об игре
@bot.message_handler(func=lambda message: message.text in GAME_INFO.keys())
def send_game_info(message):
    game_name = message.text
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(CHANNEL["name"], url=CHANNEL["link"]))
        markup.add(types.InlineKeyboardButton("Проверить подписку ✅", callback_data=f"check_{game_name}"))
        bot.send_message(
            message.chat.id,
            "Подпишитесь на канал, чтобы получить доступ к модификатору игры.",
            reply_markup=markup
        )
    else:
        send_game_link(message, game_name)

# Обработчик нажатия на кнопку "Проверить подписку"
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_subscription(call):
    user_id = call.from_user.id
    game_name = call.data.split("_")[1]

    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ Вы подписаны на канал!")
        send_game_link(call.message, game_name)
    else:
        bot.answer_callback_query(call.id, "❌ Вы не подписаны на канал!")
        bot.send_message(
            call.message.chat.id,
            "Пожалуйста, подпишитесь на канал и повторите попытку.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(CHANNEL["name"], url=CHANNEL["link"])
            )
        )

# Отправка ссылки на игру
def send_game_link(message, game_name):
    game_info = GAME_INFO.get(game_name)
    link = game_info["link"]
    description = game_info["description"]

    markup = types.InlineKeyboardMarkup()
    if link:
        markup.add(types.InlineKeyboardButton("Скачать", url=link))
    markup.add(types.InlineKeyboardButton("Как установить?", callback_data="how_to_install"))

    response = f"🎮 Игра: {game_name}\n📄 Описание: {description}"
    if not link:
        response += "\n‼️ Актуальный APK для этой игры временно недоступен. Пожалуйста, попробуйте позже."

    bot.send_message(message.chat.id, response, reply_markup=markup)

# Обработчик для кнопки "Профиль"
@bot.message_handler(func=lambda message: message.text == "Профиль")
def profile_info(message):
    user_info = user_data.get(message.from_user.id)
    if user_info:
        response = (
            f"👤 Профиль:\n"
            f"Тег пользователя: @{user_info['username']}\n"
            f"Время регистрации: {user_info['registration_time']}\n"
            f"Приглашений: {user_info['invites']}\n"
            f"Реферальная ссылка: {user_info['referral_link']}"
        )
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Профиль не найден. Пожалуйста, начните с команды /start.")

# Обработчик для кнопки "Помощь"
@bot.message_handler(func=lambda message: message.text == "Помощь")
def help_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("Гугл вход с читом", "google_login_cheat"),
        ("Разбан аккаунта", "account_unban"),
        ("Как установить?", "how_to_install"),
        ("Как пользоваться?", "how_to_use")
    ]
    markup.add(*[types.InlineKeyboardButton(text, callback_data=data) for text, data in buttons])
    bot.send_message(message.chat.id, "Выбери нужный пункт:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    responses = {
        "google_login_cheat": (
            "1. Зайдите в оригинальный Oxide и дождитесь загрузки серверов.\n"
            "2. Выйдите из игры и удалите её.\n"
            "3. Установите чит и войдите в игру через Google.\n"
            "4. Готово!"
        ),
        "account_unban": "Ссылка для разбана: https://t.me/Oxide_Vzlom/2327",
        "how_to_install": "Удалите оригинальный APK и установите модификатор.",
        "how_to_use": "Информация отсутствует."
    }
    bot.send_message(call.message.chat.id, responses.get(call.data, "Неверный запрос."))

# Обработчик для кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    start_command(message)

# Обработчик для кнопки "Техподдержка"
@bot.message_handler(func=lambda message: message.text == "Техподдержка")
def tech_support(message):
    bot.send_message(
        message.chat.id,
        "Свяжитесь с техподдержкой через: @Oxide_Vzlom_bot.\n"
        "Мы постараемся ответить вам в кратчайшие сроки!"
    )

# Обработчик для кнопки "О нас"
@bot.message_handler(func=lambda message: message.text == "О нас")
def about_bot(message):
    response = (
        "ℹ️ О боте:\n"
        "Бот создан для упрощения загрузки модификаторов. Здесь собраны все необходимые модификаторы и информация о них.\n\n"
        "📌 Сейчас бот находится в стадии разработки, поэтому возможны баги и нестабильная работа из-за отсутствия полноценного хостинга.\n\n"
        "📰 Вся актуальная информация доступна на канале: @Oxide_Vzlom.\n\n"
        "Версия бота: 0.1.0"
    )
    bot.send_message(message.chat.id, response)

# Flask-приложение для поддержки работы на Replit
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# Запуск бота
keep_alive()
bot.polling(none_stop=True)
