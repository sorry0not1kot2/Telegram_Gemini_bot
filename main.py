import asyncio
import logging
import os
import re
import google.generativeai as genai
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import nest_asyncio

nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = Bot(BOT_TOKEN)

# Установка API ключа для Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Установка модели Gemini
model = genai.GenerativeModel('gemini-1.5-flash')

# Функция для преобразования Markdown в разметку Telegram
def markdown_to_telegram(text):
    """Преобразует Markdown в разметку Telegram."""
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)  # Жирный
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)  # Курсив
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)  # Код
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)  # Ссылки
    return text

async def get_bot_username():
    bot_info = await bot.get_me()
    return bot_info.username

async def get_gemini_response(query):
    logger.info(f"Sending query to Gemini: {query}")
    try:
        response = model.generate_content(query)
        raw_response = response.candidates[0].content.parts[0].text
        logger.info(f"Received response from Gemini: {raw_response}")
        formatted_response = markdown_to_telegram(raw_response)  # Применяем форматирование
        return formatted_response
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {str(e)}")
        return f"Произошла ошибка при обращении к Gemini: {str(e)}"

# ... (остальной код остается без изменений) 
