# main.py
import asyncio
import logging
import os
import google.generativeai as genai
from telebot.async_telebot import AsyncTeleBot

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
bot = AsyncTeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

# Получение имени пользователя бота
bot_info = asyncio.run(bot.get_me())
bot_username = bot_info.username

# Хранение данных по разговорам
conversation_data = {}

# Установка API ключа для Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Установка модели Gemini
model = genai.GenerativeModel('gemini-1.5-flash')

async def get_gemini_response(query):
    try:
        response = model.generate_content(prompt=query)
        return response['content']
    except Exception as e:
        logger.error(f"Ошибка при получении ответа от Gemini: {str(e)}")
        return f"Произошла ошибка при обращении к Gemini: {str(e)}"

@bot.message_handler(commands=['start'])
async def handle_start_command(message):
    await bot.send_message(message.chat.id, f"Привет! Я бот, использующий модель Gemini от Google. Обращайтесь ко мне по @{bot_username} или отвечайте на мои сообщения, чтобы получить ответ.")

@bot.message_handler(commands=['clear'])
async def handle_clear_command(message):
    conversation_data.pop(message.chat.id, None)
    await bot.send_message(message.chat.id, "Данные по разговорам очищены.")

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and (bot_username in message.text or (message.reply_to_message and message.reply_to_message.from_user.username == bot_username)))
async def handle_message(message):
    query = message.text.replace(f"@{bot_username}", "").strip()
    
    if query:
        logger.info(f"Получен запрос: {query}")
        await bot.send_message(message.chat.id, "Обрабатываю ваш запрос...")
        
        response = await get_gemini_response(query)
        
        await bot.reply_to(message, response)
        logger.info("Ответ отправлен")
    else:
        await bot.reply_to(message, "Пожалуйста, введите сообщение.")

# Функция для запуска бота
async def main():
    try:
        logger.info("Запуск бота...")
        await bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {str(e)}")

# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())
