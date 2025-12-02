# bot_final_with_manager.py
import os
import json
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8536013019:AAEwkfOa5RNmJn1WX2WtDUW4jop7GCxYdKQ")
ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "365476305"))

# Контакты менеджера
MANAGER_USERNAME = "@red_water"  # ← ВОТ ВАШ МЕНЕДЖЕР!

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== WEBAPP МАГАЗИН ==========
async def handle_webapp(request):
    """Отдаем HTML магазин"""
    try:
        content = (Path(__file__).parent / "webapp.html").read_text(encoding='utf-8')
        return web.Response(text=content, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"<h1>Магазин VapeRoom</h1><p>Скоро откроемся...</p>", content_type='text/html')

# ========== КОМАНДА /start ==========
@dp.message(Command("start"))
async def start(message: Message):
    """Команда /start с контактами менеджера"""
    # Получаем URL магазина на Render
    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://ваш-проект.onrender.com")
    shop_url = f"{base_url}/shop"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛍 Открыть магазин", 
            web_app=WebAppInfo(url=shop_url)
        )],
        [InlineKeyboardButton(
            text="💬 Связаться с менеджером", 
            url=f"https://t.me/{MANAGER_USERNAME.replace('@', '')}"  # убираем @ для ссылки
        )]
    ])

    text = (
        "Добро пожаловать в VapeRoom 👋\n"
        "Нажмите 'Открыть магазин', чтобы посмотреть ассортимент 😎\n\n"
        "Наши контакты:\n"
        f"• Менеджер: {MANAGER_USERNAME}\n"
        "• 🚚 Доставка по Минску от 2 банок\n"
        "• 📦 Другие города — Европочта\n\n"
        "❗️ 18+ Только для совершеннолетних"
    )

    await message.answer(text, reply_markup=keyboard)
    logger.info(f"✅ Отправил /start пользователю {message.from_user.id}")

@dp.message(F.text == "🛍 Открыть магазин")
async def open_shop_button(message: Message):
    """Обработчик кнопки магазина"""
    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://ваш-проект.onrender.com")
    shop_url = f"{base_url}/shop"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📱 Открыть каталог",
            web_app=WebAppInfo(url=shop_url)
        )
    ]])
    
    await message.answer("Нажмите кнопку ниже, чтобы открыть каталог 👇", reply_markup=keyboard)

# ========== КОМАНДА /help ==========
@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "🤖 *VapeRoom Bot - Помощь*\n\n"
        "Доступные команды:\n"
        "/start - открыть магазин\n"
        "/help - помощь\n"
        "/test - тест уведомлений\n\n"
        f"💬 *Контакты менеджера:*\n"
        f"{MANAGER_USERNAME}\n\n"
        "🚚 *Доставка:*\n"
        "• Минск: от 2 банок\n"
        "• Другие города: Европочта\n\n"
        "❗️ 18+ Только для совершеннолетних",
        parse_mode="Markdown"
    )

# ========== ОБРАБОТКА ЗАКАЗОВ ==========
@dp.message(F.web_app_data)
async def handle_order(message: types.Message):
    """Обработка заказа из WebApp - УВЕДОМЛЯЕМ МЕНЕДЖЕРА!"""
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get('action') == 'order':
            items = data.get('items', [])
            total = data.get('total', 0)
            customer_name = message.from_user.full_name
            customer_id = message.from_user.id
            
            # Формируем детали заказа для менеджера
            order_details = ""
            for item in items:
                order_details += f"• {item.get('name')} - {item.get('price')} ₽\n"
            
            # 1. Уведомляем менеджера (@red_water)
            manager_text = (
                f"🛒 *НОВЫЙ ЗАКАЗ В VAPEROOM!*\n\n"
                f"*Товары:*\n{order_details}\n"
                f"*Итого:* {total} ₽\n\n"
                f"*Клиент:* {customer_name}\n"
                f"*ID клиента:* {customer_id}\n\n"
                f"📞 Свяжитесь: https://t.me/{customer_id}"
            )
            
            # Пытаемся отправить менеджеру (если бот может)
            # Если не получается - отправляем админу
            try:
                # Можно попробовать отправить менеджеру если он есть в контактах бота
                # Или просто отправляем админу
                await bot.send_message(
                    chat_id=ADMIN_ID,  # пока отправляем админу (вам)
                    text=manager_text,
                    parse_mode="Markdown"
                )
                logger.info(f"📞 Уведомление о заказе отправлено менеджеру/админу")
            except:
                # Если не получается - логируем
                logger.warning("Не удалось отправить уведомление менеджеру")
            
            # 2. Подтверждаем клиенту
            customer_text = (
                f"✅ *Заказ принят!*\n\n"
                f"*Ваш заказ на {total} ₽:*\n"
                f"{order_details}\n"
                f"*Менеджер свяжется с вами:* {MANAGER_USERNAME}\n\n"
                f"Спасибо за покупку! 😊"
            )
            
            await message.answer(customer_text, parse_mode="Markdown")
            
            logger.info(f"✅ Заказ от {customer_name} ({customer_id}) на {total} ₽")
            
    except Exception as e:
        logger.error(f"Ошибка заказа: {e}")
        await message.answer(
            f"❌ Ошибка обработки заказа\n"
            f"Свяжитесь с менеджером: {MANAGER_USERNAME}"
        )

# ========== КОМАНДА /manager ==========
@dp.message(Command("manager"))
async def manager_command(message: Message):
    """Быстрая связь с менеджером"""
    await message.answer(
        f"👨‍💼 *Связь с менеджером*\n\n"
        f"Менеджер: {MANAGER_USERNAME}\n"
        f"Телеграм: https://t.me/{MANAGER_USERNAME.replace('@', '')}\n\n"
        f"📞 *Для консультации:*\n"
        f"• Выбор жидкости\n"
        f"• Подбор POD-системы\n"
        f"• Уточнение по доставке\n"
        f"• Оптовые заказы",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# ========== НАСТРОЙКА WEBHOOK ==========
async def on_startup(bot: Bot):
    """Настройка при запуске"""
    webhook_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if webhook_url:
        webhook_url += "/webhook"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info(f"✅ Webhook установлен: {webhook_url}")
        
        # Уведомляем админа о запуске
        startup_text = (
            f"🤖 *VapeRoom Bot ЗАПУЩЕН!*\n\n"
            f"✅ Webhook настроен\n"
            f"🛍 Магазин готов\n"
            f"👨‍💼 Менеджер: {MANAGER_USERNAME}\n\n"
            f"*Контактные данные:*\n"
            f"Менеджер: {MANAGER_USERNAME}\n"
            f"Доставка: Минск от 2 банок\n"
            f"18+ Только для совершеннолетних\n\n"
            f"🚀 Бот: https://t.me/vaperoom_shop_bot"
        )
        
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=startup_text,
            parse_mode="Markdown"
        )

# ========== ОСНОВНОЕ ПРИЛОЖЕНИЕ ==========
async def main():
    """Запуск приложения"""
    dp.startup.register(on_startup)
    
    # Создаем веб-приложение
    app = web.Application()
    
    # Маршруты
    app.router.add_get("/shop", handle_webapp)  # магазин
    app.router.add_get("/", lambda r: web.Response(text="🚀 VapeRoom Bot API"))
    app.router.add_get("/health", lambda r: web.Response(text="✅ OK"))
    app.router.add_get("/manager", lambda r: web.Response(text=f"👨‍💼 Менеджер: {MANAGER_USERNAME}"))
    
    # Webhook для Telegram
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    
    # Запускаем сервер
    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info(f"🤖 VapeRoom Bot запускается...")
    logger.info(f"👨‍💼 Менеджер: {MANAGER_USERNAME}")
    logger.info(f"👑 Админ ID: {ADMIN_ID}")
    logger.info(f"🌐 Магазин: {os.getenv('RENDER_EXTERNAL_URL', 'Локальный')}/shop")
    logger.info(f"📡 Webhook: {os.getenv('RENDER_EXTERNAL_URL', 'Polling')}/webhook")
    
    # Бесконечный цикл
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())