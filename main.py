import asyncio
import logging
import sys
import sqlite3
import json

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

import openai
from config import TELEGRAM_API_TOKEN, OPENAI_API_KEY

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Настройка API OpenAI
openai.api_key = OPENAI_API_KEY

# Подключение к базе данных SQLite
conn = sqlite3.connect('chatbot.db')
cursor = conn.cursor()


# Функция для загрузки контекста из базы данных
def load_context(user_id):
    cursor.execute('SELECT context FROM user_context WHERE user_id=?', (user_id,))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    else:
        return []


# Функция для сохранения контекста в базу данных
def save_context(user_id, context):
    cursor.execute('REPLACE INTO user_context (user_id, context) VALUES (?, ?)', (user_id, json.dumps(context)))
    conn.commit()


# Функция для взаимодействия с моделью GPT-4
def ask_gpt4(text, user_id, temperature=0.7, n=1):
    context = load_context(user_id)
    context.append({"role": "user", "content": text})

    # Ограничение контекста до последних 10 сообщений
    short_context = context[-10:]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=short_context,
        temperature=temperature,
        n=n
    )

    bot_response = response.choices[0].message['content']
    context.append({"role": "assistant", "content": bot_response})

    save_context(user_id, context)

    return bot_response


# Хэндлер для команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    user_context = load_context(message.from_user.id)
    await message.reply("Привет! Я бот, использующий модель GPT-4. Как я могу помочь?")


# Хэндлер для обработки текстовых сообщений
@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_input = message.text

    try:
        bot_response = ask_gpt4(user_input, user_id)
        await message.reply(bot_response)
    except Exception as e:
        error_message = f"Ошибка: {str(e)}"
        print(error_message)  # Отладка в консоли
        await message.reply(f"Произошла ошибка при обработке вашего сообщения. Подробности: {error_message}")


# Закрытие соединения с базой данных при завершении работы
async def on_shutdown(dispatcher: Dispatcher):
    conn.close()


# Запуск бота
async def main() -> None:
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(handle_message)

    await dp.start_polling(bot, skip_updates=True, on_shutdown=on_shutdown)


if __name__ == '__main__':
    asyncio.run(main())
