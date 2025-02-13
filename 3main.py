import asyncio
import logging
import os
import google.generativeai as genai
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
from telegram.constants import ParseMode
import nest_asyncio
from google.generativeai.types import HarmCategory, HarmBlockThreshold

nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(BOT_TOKEN)

# Установка API ключа для Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Установка модели Gemini
generation_config = {
    "temperature": 0.5,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 4096,
}

model = genai.GenerativeModel(model_name="gemini-1.5-flash")


async def get_bot_username():
    bot_info = await bot.get_me()
    return bot_info.username


async def get_gemini_response(query):
    logger.info(f"Sending query to Gemini: {query}")
    try:
        response = model.generate_content(
            query,
            generation_config=generation_config,
            safety_settings={
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            },
        )
        if response.candidates:
            logger.info(
                f"Received response from Gemini: {response.candidates[0].content.parts[0].text}"
            )
            return response.candidates[0].content.parts[0].text
        else:
            logger.error("No candidates received from Gemini")
            return "Не удалось получить ответ от Gemini."
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {str(e)}")
        return f"Произошла ошибка при обращении к Gemini: {str(e)}"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Проверяем, что message не равен None и содержит текст
    if message is not None and message.text is not None:
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

            # Экранируем одиночные '*' вне блоков кода и строк документации
            in_code_block = False
            in_docstring = False
            escaped_response = []
            for i, char in enumerate(response):
                if (
                    i > 0
                    and response[i - 1] == '"'
                    and response[i] == '"'
                    and response[i + 1] == '"'
                ):
                    in_docstring = not in_docstring
                if char == "`":
                    in_code_block = not in_code_block
                if char == "*" and not in_code_block and not in_docstring:
                    escaped_response.append("\*")
                else:
                    escaped_response.append(char)
            response = "".join(escaped_response)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=response,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            await message.reply_text(f"Произошла ошибка: {str(e)}")
    else:
        # Обработка других типов обновлений (необязательно)
        logger.info(f"Получено обновление без текста: {update}")
        return


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = await get_bot_username()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Привет! Я - Gemini бот. Обращайтесь по @{bot_username} или отвечайте на мои сообщения, чтобы получить ответ.",
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="История сообщений очищена."
    )


async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_error_handler(error_handler)

    logger.info("Запуск бота...")
    await application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
