import asyncio
import logging
import os
import google.generativeai as genai
import nest_asyncio
from telebot.async_telebot import AsyncTeleBot

# Применение nest_asyncio для повторного использования event loop
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = AsyncTeleBot(BOT_TOKEN)

# Получение имени пользователя бота
bot_info = asyncio.run(bot.get_me())
bot_username = bot_info.username

# Хранение данных по разговорам
conversation_data = {}

# Установка API ключа для Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Установка модели Gemini
model
