import telebot

TOKEN = '7812547873:AAFhjkRFZ5wGzZn4BCcOPjAAdgEZBRc4bq8'
bot = telebot.TeleBot(TOKEN)

CHANNEL_USERNAME = "@Oxide_Vzlom"

@bot.message_handler(commands=['start'])
def send_closed_message(message):
    bot.send_message(
        message.chat.id,
        f"**Бот временно закрыт.**\n\n"
        f"**Следите за новостями в канале: {CHANNEL_USERNAME}**"
    )

if __name__ == '__main__':
    print("Бот запущен и временно закрыт.")
    bot.infinity_polling()
