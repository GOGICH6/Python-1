import telebot
from telebot import types
import requests

TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Доступные игры и ссылки на APK по платформам
GAMES = {
    "Oxide: Survival Island": {
        "android": "https://t.me/+dxcSK08NRmxjNWRi",
        "ios": "https://t.me/+U3QzhcTHKv1lNmMy"
    },
    "Standoff 2": {
        "android": None,
        "ios": None
    }
}

# Каналы
REQUIRED_CHANNELS = {
    "2 канал": "https://t.me/ChatByOxide",
    "3 канал": "https://t.me/Oxide_Vzlom"
}
NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}

# Текст для отправки другу
SHARE_TEXT = "– мой любимый бесплатный чит на Oxide: Survival Island! ❤️"

# Память: выбранная игра и сообщения
user_state = {}

def is_subscribed(user_id):
    for _, link in REQUIRED_CHANNELS.items():
        username = link.split("/")[-1]
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@{username}&user_id={user_id}"
        res = requests.get(url).json()
        if res.get('result', {}).get('status') not in ['member', 'administrator', 'creator']:
            return False
    return True

# START
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.chat.type != "private":
        return
    user_id = message.from_user.id
    remove_old_message(user_id)

    markup = types.InlineKeyboardMarkup()
    for game in GAMES:
        markup.add(types.InlineKeyboardButton(game, callback_data=f"game:{game}"))

    msg = bot.send_message(message.chat.id, "🎮 *Выберите нужную игру:*", parse_mode="Markdown", reply_markup=markup)
    user_state[user_id] = {"step": "game", "msg_id": msg.message_id}

# Выбор игры
@bot.callback_query_handler(func=lambda call: call.data.startswith("game:"))
def game_selected(call):
    user_id = call.from_user.id
    game = call.data.split("game:")[1]
    user_state[user_id] = {"game": game}

    remove_old_message(user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 Android", callback_data="os:android"),
        types.InlineKeyboardButton("🍏 iOS", callback_data="os:ios")
    )
    msg = bot.send_message(call.message.chat.id, f"📲 *Вы выбрали:* {game}\nТеперь выберите вашу ОС:", parse_mode="Markdown", reply_markup=markup)
    user_state[user_id]["msg_id"] = msg.message_id

# Выбор ОС
@bot.callback_query_handler(func=lambda call: call.data.startswith("os:"))
def os_selected(call):
    user_id = call.from_user.id
    os_type = call.data.split("os:")[1]
    game = user_state.get(user_id, {}).get("game")

    remove_old_message(user_id)

    if not game:
        bot.send_message(call.message.chat.id, "⚠ Произошла ошибка. Начните сначала: /start")
        return

    link = GAMES[game].get(os_type)
    if not link:
        bot.send_message(call.message.chat.id, "❌ Файл для этой системы или игры временно недоступен.")
        return

    # Проверка подписки
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup(row_width=3)
        for name, link in {**NO_CHECK_CHANNEL, **REQUIRED_CHANNELS}.items():
            markup.add(types.InlineKeyboardButton(name, url=link))
        markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))
        msg = bot.send_message(call.message.chat.id, "📢 *Чтобы получить доступ, подпишитесь на каналы ниже и нажмите кнопку ниже:*", parse_mode="Markdown", reply_markup=markup)
        user_state[user_id]["msg_id"] = msg.message_id
        user_state[user_id]["waiting_link"] = link
        return

    # Отправка ссылки
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT))
    bot.send_message(call.message.chat.id,
                     f"✅ *Вы успешно прошли регистрацию!*\n\n"
                     f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({link})\n\n"
                     f"⚠ *Не отписывайтесь от каналов — иначе бот добавит вас в ЧС!*",
                     parse_mode="Markdown", reply_markup=markup)

# Проверка подписки
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    user_id = call.from_user.id
    link = user_state.get(user_id, {}).get("waiting_link")

    if is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT))
        bot.send_message(call.message.chat.id,
                         f"✅ *Вы успешно прошли регистрацию!*\n\n"
                         f"🔗 *Ссылка на скачивание:* [👉 Нажмите здесь]({link})\n\n"
                         f"⚠ *Не отписывайтесь от каналов — иначе бот добавит вас в ЧС!*",
                         parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "❌ *Вы ещё не подписаны на все каналы!*", parse_mode="Markdown")

# Удаление предыдущего сообщения
def remove_old_message(user_id):
    data = user_state.get(user_id)
    if data and "msg_id" in data:
        try:
            bot.delete_message(user_id, data["msg_id"])
        except:
            pass

if __name__ == '__main__':
    print("Бот запущен")
    bot.infinity_polling()
    
