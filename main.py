import asyncio
import logging
import os
import re
import html
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

def markdown_to_telegram(text):
    """Преобразует Markdown в разметку Telegram, экранируя HTML."""
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text) 
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text) 
    text = re.sub(r'`(.*?)`', r'<code>{}</code>'.format(html.escape(text)), text)  # Экранируем код
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text) 
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
        formatted_response = markdown_to_telegram(raw_response) 
        return formatted_response
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
        # Игнорируем сообщения
        return

    try:
        response = await get_gemini_response(query)
        await message.reply_text(response, parse_mode='HTML')  # Отправляем с HTML разметкой
    except Exception as e:
        await message.reply_text(f"Произошла ошибка: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = await get_bot_username()
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                  text=f"Привет! Я - Gemini бот. Обращайтесь по @{bot_username} "
                                       f"или отвечайте на мои сообщения, чтобы получить ответ.")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="История сообщений очищена.")

async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('clear', clear))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Запуск бота...")
    await application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
