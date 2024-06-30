import asyncio
import logging
import os
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

async def get_bot_username():
    bot_info = await bot.get_me()
    return bot_info.username

async def get_gemini_response(query):
    logger.info(f"Sending query to Gemini: {query}")
    try:
        response = model.generate_content(query)
        logger.info(f"Received response from Gemini: {response.candidates[0].content.parts[0].text}")
        return response.candidates[0].content.parts[0].text
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {str(e)}")
        return f"Произошла ошибка при обращении к Gemini: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    query = message.text.strip()
    bot_username = await get_bot_username()

    if message.reply_to_message and message.reply_to_message.from_user.username == bot_username:
        # Если сообщение является ответом на сообщение бота
        logger.info(f"Processing reply to bot: {query}")
    elif f"@{bot_username}" in query:
        # Если сообщение содержит упоминание бота
        logger.info(f"Processing mention of bot: {query}")
        query = query.replace(f"@{bot_username}", "").strip()
    else:
        # Игнорируем сообщения, не содержащие упоминание бота или не являющиеся ответом на сообщение бота
        return

    try:
        response = await get_gemini_response(query)
        await message.reply_text(response)
    except Exception as e:
        await message.reply_text(f"Произошла ошибка: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error
