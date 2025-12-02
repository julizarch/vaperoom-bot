import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web
import asyncio

# Настройка
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8536013019:AAEwkfOa5RNmJn1WX2WtDUW4jop7GCxYdKQ")
MANAGER = "@red_water"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Команды
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(f"👋 Привет! Менеджер: {MANAGER}")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    await message.answer(f"Помощь. Пиши менеджеру: {MANAGER}")

# Веб-сервер
async def shop(request):
    html = f"<h1>VapeRoom</h1><p>Менеджер: {MANAGER}</p>"
    return web.Response(text=html, content_type='text/html')

async def main():
    # Веб-сервер
    app = web.Application()
    app.router.add_get('/shop', shop)
    app.router.add_get('/health', lambda r: web.Response(text='OK'))
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 10000))).start()
    
    # Бот
    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
