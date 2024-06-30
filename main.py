import asyncio
import logging
import os
import google.generativeai as genai
import nest_asyncio
from aiogram import Bot, Dispatcher, executor, types

# Применение nest_asyncio для повторного использования event loop
nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

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

@dp.message_handler(commands=['start'])
async def handle_start_command(message: types.Message):
    logger.info(f"Received /start command from {message.chat.id}")
    await message.reply("Привет! Я бот, использующий модель Gemini от Google.")

@dp.message_handler()
async def handle_message(message: types.Message):
    logger.info(f"Received message: {message.text} from {message.chat.id}")
    query = message.text.strip()
    
    if query:
        logger.info(f"Processing query: {query}")
        await message.reply("Обрабатываю ваш запрос...")
        
        response = await get_gemini_response(query)
        
        await message.reply(response)
        logger.info("Ответ отправлен")
    else:
        await message.reply("Пожалуйста, введите сообщение.")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
