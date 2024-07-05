# рабочий файл с логами в память с условием работы только в телеграм группе, 
# с прописанным промтом и выставленными настройками для Gemini
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

# ID групповых чатов
ALLOWED_GROUP_CHAT_IDS = [-1002030510187, -1002030599999]  # замените на ваши ID

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

# ... (остальной код)

# Системная инструкция для Gemini (промт)
system_instruction = """Ты -  девушка по имени Ника,так звали греческую богиню. Ты - хороший, грамотный специалист по программированию. Много знаешь во всех областях наук и естествознаний. Пользуешься интернет поиском. 
                        Ты всё обясняешь для человека с нулевыми знаниями. Ты имеешь доступ к страницам интернета. В обяснении опираешься на ссылки материалов из интернета. Если тебе указывают ссылку на интернет страницу - ознакамливаешься
                        и изучаешь контекст этой страницк и ссылки на ней. 
                        Используешь легкий флирт в общении."""


async def get_bot_username():
    bot_info = await bot.get_me()
    return bot_info.username
    
async def get_gemini_response(query, history):
    logger.info(f"Sending query to Gemini: {query}")
    try:
        # Формируем контекст
        context = f"{system_instruction}\n\n" + "\n".join(
            [f"{message['role']}: {message['content']}" for message in history]
        )

        response = model.generate_content(
            context,
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
            response_text = response.candidates[0].content.parts[0].text
            return response_text  # Возвращаем текст без изменений
        else:
            logger.error("No candidates received from Gemini")
            return "Не удалось получить ответ от Gemini."
    except Exception as e:
        logger.error(f"Error getting response from Gemini: {str(e)}")
        return f"Произошла ошибка при обращении к Gemini: {str(e)}"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if message is not None and message.text is not None:
        query = message.text.strip()
        bot_username = await get_bot_username()
        user_id = update.effective_user.id

        # Инициализируем историю для пользователя
        if user_id not in context.bot_data:
            context.bot_data[user_id] = {"history": []}

        history = context.bot_data[user_id]["history"]

        if message.chat.id in ALLOWED_GROUP_CHAT_IDS and (
            (
                message.reply_to_message
                and message.reply_to_message.from_user.username == bot_username
            )
            or f"@{bot_username}" in query
        ):
            # Отправляем сообщение "думаю..."
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="_думаю..._",  # Курсив в Markdown
                parse_mode=ParseMode.MARKDOWN,
                message_thread_id=message.message_thread_id,
            )

            logger.info(f"Processing mention of bot: {query}")
            query = query.replace(f"@{bot_username}", "").strip()

            try:
                # Добавляем вопрос пользователя в историю
                history.append({"role": "user", "content": query})

                response = await get_gemini_response(query, history)

                # Добавляем ответ Gemini в историю
                history.append({"role": "assistant", "content": response})

                # Отправляем ответ в той же ветке
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=response,
                    parse_mode=ParseMode.MARKDOWN, # Markdown для ответа Gemini
                    message_thread_id=message.message_thread_id,
                )
            except Exception as e:
                await message.reply_text(f"Произошла ошибка: {str(e)}")
        #else:
        #    # Отправляем сообщение об ошибке
        #    await context.bot.send_message(
        #        chat_id=update.effective_chat.id,
        #        text=f"Сорян, я болтаю только когда меня называют по @{bot_username}, и только в телеграм-группе Беседка...",
        #        message_thread_id=message.message_thread_id,
        #    )
            

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = await get_bot_username()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Привет!\n"
             "Я -  бот на основе Gemini-flesh.\n\n"
             f"Для общения со мной, называйте меня в сообщении по @{bot_username} или  сделайте ответ (replay) на мои сообщения, чтобы я вам ответил. \n\n"
             "Я общаюсь только в телеграм-группе Беседка...\n\n"
             "© @Don_Dron",
        message_thread_id=update.effective_message.message_thread_id
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in context.bot_data:
        del context.bot_data[user_id]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="История сообщений очищена.",
        message_thread_id=update.effective_message.message_thread_id 
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
