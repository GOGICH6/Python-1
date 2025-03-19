import telebot
import requests
from telebot import types
from datetime import datetime, timedelta

# Токен бота
TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

# Админ ID
ADMIN_ID = 1903057676  

# Каналы
NO_CHECK_CHANNEL = {"1 канал": "https://t.me/+gQzXZwSO5cliNGJi"}
REQUIRED_CHANNELS = {
    "2 канал": "https://t.me/ChatByOxide",
    "3 канал": "https://t.me/Oxide_Vzlom"
}
DOWNLOAD_CHANNEL_LINK = "https://t.me/+dxcSK08NRmxjNWRi"

# Текст для отправки другу
SHARE_TEXT = "- лучший бесплатный чит на Oxide!"

# База пользователей
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

# 📌 Ловим /start (регистрируем пользователя)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data[message.from_user.id] = datetime.now()  # Регистрируем пользователя

    if is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton("📤 Отправить другу", switch_inline_query=SHARE_TEXT)
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

# 📌 Команда /admin (только для тебя)
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к админ-панели.")
        return

    markup = types.InlineKeyboardMarkup()
    stats_btn = types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    notify_btn = types.InlineKeyboardButton("📢 Оповещение", callback_data="admin_notify")
    markup.add(stats_btn, notify_btn)

    bot.send_message(message.chat.id, "🔧 *Админ-панель:*\nВыберите действие:", parse_mode="Markdown", reply_markup=markup)

# 📌 Обработчик кнопок в админке
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_buttons(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ У вас нет доступа к админ-панели.")
        return

    if call.data == "admin_stats":
        bot.send_message(call.message.chat.id, get_statistics(), parse_mode="Markdown")

    elif call.data == "admin_notify":
        bot.send_message(call.message.chat.id, "📢 *Введите сообщение для рассылки:*", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, confirm_broadcast)

# 📌 Функция получения статистики
def get_statistics():
    total_users = len(user_data)
    now = datetime.now()

    last_24h = sum(1 for date in user_data.values() if now - date <= timedelta(hours=24))
    last_48h = sum(1 for date in user_data.values() if now - date <= timedelta(hours=48))
    last_month = sum(1 for date in user_data.values() if now - date <= timedelta(days=30))

    return f"📊 *Статистика:*\n\n" \
           f"👥 *Всего пользователей:* {total_users}\n" \
           f"📅 *За 24 часа:* {last_24h}\n" \
           f"📅 *За 48 часов:* {last_48h}\n" \
           f"📅 *За месяц:* {last_month}"

# 📌 Подтверждение рассылки
def confirm_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return

    markup = types.InlineKeyboardMarkup()
    confirm_btn = types.InlineKeyboardButton("✅ Да", callback_data="confirm_broadcast")
    cancel_btn = types.InlineKeyboardButton("❌ Нет", callback_data="cancel_broadcast")
    markup.add(confirm_btn, cancel_btn)

    bot.send_message(message.chat.id, f"📢 *Вы хотите отправить это сообщение?*\n\n{message.text}", parse_mode="Markdown", reply_markup=markup)

    bot.register_next_step_handler(message, lambda msg: save_broadcast(msg, message.text))

# 📌 Сохранение сообщения для рассылки
broadcast_message = ""

def save_broadcast(msg, text):
    global broadcast_message
    broadcast_message = text

# 📌 Подтверждение рассылки
@bot.callback_query_handler(func=lambda call: call.data in ["confirm_broadcast", "cancel_broadcast"])
def handle_broadcast_confirmation(call):
    global broadcast_message

    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ У вас нет доступа к админ-панели.")
        return

    if call.data == "confirm_broadcast":
        send_broadcast(broadcast_message)
        bot.send_message(call.message.chat.id, "✅ Сообщение отправлено!")
        broadcast_message = ""

    elif call.data == "cancel_broadcast":
        bot.send_message(call.message.chat.id, "❌ Рассылка отменена.")
        broadcast_message = ""

# 📌 Функция рассылки
def send_broadcast(message_text):
    sent_count = 0
    for user_id in user_data.keys():
        try:
            bot.send_message(user_id, message_text, parse_mode="Markdown")
            sent_count += 1
        except:
            continue
    print(f"✅ Сообщение отправлено {sent_count} пользователям!")

if __name__ == "__main__":
    print("Бот запущен! Ожидаем команды...")
    bot.infinity_polling()
