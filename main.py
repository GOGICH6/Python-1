import telebot
from telebot import types
import requests
from flask import Flask, request
from datetime import datetime
import os

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

# Обработчики для остальных функций (Список игр, Помощь, и т.д.) остаются такими же

# Flask-приложение для Webhook
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

# Установка Webhook
WEBHOOK_URL = f"https://<your-railway-url>.railway.app/{TOKEN}"
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

# Запуск Flask приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
