import asyncio
import logging
import os
import google.generativeai as genai
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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
        response = model.generate_content(prompt=query)
        logger.info(f"Received response from Gemini: {response['content']}")
        return response['content']
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {str(e)}")
        return f"Произошла ошибка при обращении к Gemini: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text.strip()
    if query:
        logger.info(f"Processing query: {query}")
        response = await get_gemini_response(query)
        await update.message.reply_text(response)

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот, использующий модель Gemini от Google. Обращайтесь ко мне по @username или отвечайте на мои сообщения, чтобы получить ответ.")

async def handle_clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Очищаем данные по разговорам (если есть)
    await update.message.reply_text("Данные по разговорам очищены.")

async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', handle_start_command))
    application.add_handler(CommandHandler('clear', handle_clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Запуск бота...")
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
