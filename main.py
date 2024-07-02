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

# Максимальная длина сообщения Telegram
MAX_MESSAGE_LENGTH = 4096

async def get_bot_username():
    bot_info = await bot.get_me()
    return bot_info.username

async def get_gemini_response(query):
    logger.info(f"Sending query to Gemini: {query}")
    try:
        response = model.generate_content(query)
        raw_response = response.candidates[0].content.parts[0].text
        logger.info(f"Received response from Gemini: {raw_response}")
        return raw_response
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {str(e)}")
        return f"Произошла ошибка при обращении к Gemini: {str(e)}"

async def split_message(message):
    """Разбивает сообщение на части, не превышающие максимальную длину,
       стараясь не разбивать слова.
    """
    parts = []
    current_part = ""
    for word in message.split():
        if len(current_part) + len(word) + 1 <= MAX_MESSAGE_LENGTH:
            current_part += word + " "
        else:
            parts.append(current_part.strip())
            current_part = word + " "
    if current_part:
        parts.append(current_part.strip())
    return parts

def escape_markdown_v2(text):
    """Экранирует специальные символы Markdown V2 внутри кода."""
    text = re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\1', text)
    return text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    query = message.text.strip()
    bot_username = await get_bot_username()

    if message.reply_to_message and message.reply_to_message.from_user.username == bot_username:
        logger.info(f"Processing reply to bot: {query}")
    elif f"@{bot_username}" in query:
        logger.info(f"Processing mention of bot: {query}")
        query = query.replace(f"@{bot_username}", "").strip()
    else:
        return

    try:
        response = await get_gemini_response(query)

        # Экранируем спецсимволы только внутри блоков кода
        response = re.sub(r'```(.*?)```', 
                          lambda m: f"```{escape_markdown_v2(m.group(1))}```", 
                          response, flags=re.DOTALL)
        response = re.sub(r'`(.*?)`', 
                          lambda m: f"`{escape_markdown_v2(m.group(1))}`", 
                          response)

        message_parts = await split_message(response)
        for part in message_parts:
            await message.reply_text(part, parse_mode='MarkdownV2')
        await message.reply_text("Конец ответа. Что-то ещё? ", parse_mode='MarkdownV2')
    except Exception as e:
        await message.reply_text(f"Произошла ошибка: {str(e)}")

# ... (остальной код без изменений) 
