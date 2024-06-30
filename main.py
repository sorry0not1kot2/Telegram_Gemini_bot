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
    query = update.message.text.strip()
    if query:
        logger.info(f"Processing query: {query}")
        try:
            response = await get_gemini_response(query)
            await update.message.reply_text(response)
        except Exception as e:
            await update.message.reply_text(f"Произошла ошибка: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
