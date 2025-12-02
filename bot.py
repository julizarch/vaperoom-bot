import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8536013019:AAEwkfOa5RNmJn1WX2WtDUW4jop7GCxYdKQ")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "365476305"))
MANAGER = "@red_water"

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== КОМАНДЫ БОТА ==========
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    """Команда /start"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="💬 Написать менеджеру",
            url=f"https://t.me/{MANAGER.replace('@', '')}"
        )]
    ])
    
    await message.answer(
        "👋 Добро пожаловать в VapeRoom!\n\n"
        f"💬 Менеджер: {MANAGER}\n"
        "🚚 Доставка по Минску от 2 банок\n"
        "📦 Другие города — Европочта\n\n"
        "❗️ 18+ Только для совершеннолетних",
        reply_markup=keyboard
    )
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    """Команда /help"""
    await message.answer(
        "🤖 Помощь по боту:\n\n"
        "/start - запустить бота\n"
        "/help - эта справка\n"
        "/test - тест работы\n\n"
        f"💬 Менеджер: {MANAGER}\n\n"
        "🚚 Доставка:\n"
        "- Минск: от 2 банок\n"
        "- Другие города: Европочта"
    )

@dp.message(Command("test"))
async def test_cmd(message: types.Message):
    """Тест команда"""
    try:
        await bot.send_message(
            ADMIN_ID,
            "✅ Тест: бот работает на Render!"
        )
        await message.answer("✅ Тест пройден! Админ уведомлен.")
        logger.info("Тест пройден успешно")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        logger.error(f"Ошибка теста: {e}")

@dp.message(Command("manager"))
async def manager_cmd(message: types.Message):
    """Связь с менеджером"""
    await message.answer(
        f"👨‍💼 Контакты менеджера:\n\n"
        f"Telegram: {MANAGER}\n"
        f"Ссылка: https://t.me/{MANAGER.replace('@', '')}\n\n"
        f"📞 Для заказов и консультаций"
    )

# ========== ВЕБ-СЕРВЕР ==========
async def shop_handler(request):
    """Магазин HTML"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>VapeRoom Shop 🛍</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; }}
            .product {{ background: #f9f9f9; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .contact {{ background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .telegram-btn {{ display: inline-block; background: #0088cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛍 VapeRoom Магазин</h1>
            
            <div class="product">
                <h3>🎮 POD-системы</h3>
                <p>• Vaporesso XROS 5 - 2 500 ₽</p>
                <p>• Geekvape Wenax - 2 300 ₽</p>
            </div>
            
            <div class="product">
                <h3>💨 Солевые жидкости</h3>
                <p>• Husky "Рик и Морти" - 900 ₽</p>
                <p>• Soltech ICE - 850 ₽</p>
            </div>
            
            <div class="contact">
                <strong>💬 Для заказа свяжитесь с менеджером:</strong><br>
                <strong>Telegram:</strong> {MANAGER}<br>
                <a href="https://t.me/{MANAGER.replace('@', '')}" class="telegram-btn">Написать в Telegram</a>
            </div>
            
            <p><strong>🚚 Доставка:</strong><br>- Минск: от 2 банок<br>- Другие города: Европочта</p>
            <p><strong>❗️ 18+</strong> Только для совершеннолетних</p>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def health_handler(request):
    """Health check для Render"""
    return web.Response(text='✅ OK')

async def start_web_server():
    """Запуск веб-сервера"""
    app = web.Application()
    app.router.add_get('/shop', shop_handler)
    app.router.add_get('/health', health_handler)
    app.router.add_get('/', lambda r: web.Response(text='🚀 VapeRoom Bot API'))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 10000)))
    await site.start()
    
    logger.info(f"🌐 Веб-сервер запущен на порту {os.getenv('PORT', 10000)}")
    logger.info(f"🛍 Магазин доступен по адресу: /shop")
    return runner

# ========== ЗАПУСК ==========
async def main():
    """Основная функция запуска"""
    # Запускаем веб-сервер
    web_runner = await start_web_server()
    
    # Отправляем уведомление админу
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🤖 VapeRoom Bot запущен!\n"
            f"👨‍💼 Менеджер: {MANAGER}\n"
            f"✅ Веб-магазин готов к работе"
        )
        logger.info("Уведомление админу отправлено")
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление админу: {e}")
    
    # Запускаем бота
    logger.info("🤖 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
