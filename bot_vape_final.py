# bot_old_version.py - для aiogram 2.x
import os
import json
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8536013019:AAEwkfOa5RNmJn1WX2WtDUW4jop7GCxYdKQ")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "365476305"))
MANAGER = "@red_water"

# Инициализация бота
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ========== WEBAPP МАГАЗИН ==========
async def handle_webapp(request):
    """Отдаем HTML магазин"""
    try:
        content = (Path(__file__).parent / "webapp.html").read_text(encoding='utf-8')
        return web.Response(text=content, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"<h1>VapeRoom Shop</h1><p>Скоро откроемся...</p>", content_type='text/html')

# ========== КОМАНДА /start ==========
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """Команда /start"""
    # Получаем URL магазина на Render
    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://ваш-проект.onrender.com")
    shop_url = f"{base_url}/shop"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(
            text="🛍 Открыть магазин VapeRoom", 
            url=shop_url  # в aiogram 2.x нет web_app, используем url
        ),
        InlineKeyboardButton(
            text="💬 Связаться с менеджером", 
            url=f"https://t.me/{MANAGER.replace('@', '')}"
        )
    )

    text = (
        "Добро пожаловать в VapeRoom 👋\n"
        "Нажмите 'Открыть магазин', чтобы посмотреть ассортимент 😎\n\n"
        f"Наши контакты:\n"
        f"• Менеджер: {MANAGER}\n"
        "• 🚚 Доставка по Минску от 2 банок\n"
        "• 📦 Другие города — Европочта\n\n"
        "❗️ 18+ Только для совершеннолетних"
    )

    await message.answer(text, reply_markup=keyboard)
    logger.info(f"✅ Отправил /start пользователю {message.from_user.id}")

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    """Команда /help"""
    await message.answer(
        "🤖 *VapeRoom Bot - Помощь*\n\n"
        "Доступные команды:\n"
        "/start - открыть магазин\n"
        "/help - помощь\n"
        f"💬 *Контакты менеджера:*\n"
        f"{MANAGER}\n\n"
        "🚚 *Доставка:*\n"
        "• Минск: от 2 банок\n"
        "• Другие города: Европочта\n\n"
        "❗️ 18+ Только для совершеннолетних",
        parse_mode="Markdown"
    )

@dp.message_handler(commands=['test'])
async def test_command(message: types.Message):
    """Тест уведомлений"""
    await bot.send_message(
        ADMIN_ID,
        "🔔 *Тест бота на Render!*\n\nБот работает! ✅",
        parse_mode="Markdown"
    )
    await message.answer("✅ Тестовое уведомление отправлено!")

# ========== ЗАПУСК СЕРВЕРА ==========
async def start_web_server():
    """Запуск веб-сервера для магазина"""
    app = web.Application()
    app.router.add_get("/shop", handle_webapp)
    app.router.add_get("/health", lambda r: web.Response(text='✅ OK'))
    app.router.add_get("/", lambda r: web.Response(text='🚀 VapeRoom Bot API'))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()
    
    logger.info(f"🌐 WebApp магазин: {os.getenv('RENDER_EXTERNAL_URL', '')}/shop")
    return runner

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
async def on_startup(dp):
    """Действия при запуске"""
    # Запускаем веб-сервер
    web_runner = await start_web_server()
    
    # Сохраняем runner для завершения
    dp.bot['web_runner'] = web_runner
    
    logger.info(f"🤖 Бот запущен")
    logger.info(f"👨‍💼 Менеджер: {MANAGER}")
    logger.info(f"👑 Админ ID: {ADMIN_ID}")
    
    # Отправляем уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"🤖 *VapeRoom Bot ЗАПУЩЕН!*\n\n"
        f"✅ Магазин готов к работе\n"
        f"👨‍💼 Менеджер: {MANAGER}\n"
        f"🚀 Бот: https://t.me/vaperoom_shop_bot",
        parse_mode="Markdown"
    )

async def on_shutdown(dp):
    """Действия при завершении"""
    # Останавливаем веб-сервер
    if 'web_runner' in dp.bot:
        await dp.bot['web_runner'].cleanup()
    await dp.storage.close()
    await dp.storage.wait_closed()

if __name__ == '__main__':
    # Запускаем бота
    executor.start_polling(
        dp, 
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )
