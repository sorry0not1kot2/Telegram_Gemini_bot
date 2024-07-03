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

# ... (остальной код такой же) ... 

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (остальной код такой же) ...

        try:
            response = await get_gemini_response(query)

            # Экранируем одиночные '*' вне блоков кода и строк документации, 
            # но не экранируем двойные звёздочки ('**')
            in_code_block = False
            in_docstring = False
            escaped_response = []
            i = 0
            while i < len(response):
                char = response[i]
                if (
                    i < len(response) - 2 
                    and response[i] == '"' 
                    and response[i + 1] == '"' 
                    and response[i + 2] == '"'
                ):
                    in_docstring = not in_docstring
                    escaped_response.append(char)  # Добавляем кавычки
                    i += 3  # Пропускаем две следующие кавычки
                    continue 
                if char == '`':
                    in_code_block = not in_code_block
                if char == '*' and not in_code_block and not in_docstring:
                    # Проверяем, является ли это одиночной звездочкой 
                    if i < len(response) - 1 and response[i + 1] == '*':
                        escaped_response.append('**')  # Добавляем без экранирования
                        i += 1  # Пропускаем следующую звёздочку
                    else:
                        escaped_response.append('\*') # Экранируем одиночную 
                else:
                    escaped_response.append(char)
                i += 1
            response = ''.join(escaped_response)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=response,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            await message.reply_text(f"Произошла ошибка: {str(e)}")
    else:
        # ... (остальной код такой же) ...

# ... (остальной код такой же) ... 
