import asyncio
import logging
import os
import sys

# Настройка Бота для работы с моделями Django
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_root not in sys.path:
    sys.path.insert(0, app_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

import django
django.setup()

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.enums import ParseMode
from decouple import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
SITE_URL = config('SITE_URL', default='https://web-production-48e.up.railway.app/')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_main_keyboard():
    web_app_btn = KeyboardButton(
        text='🛒 Открыть магазин',
        web_app=WebAppInfo(url=SITE_URL)
    )
    order_status_btn = KeyboardButton(text='📦 Статус заказа')
    help_btn = KeyboardButton(text='❓ Помощь')  # ← ИСПРАВЛЕНО
    profile_btn = KeyboardButton(text='👤 Мой профиль')

    kb = [
        [web_app_btn],
        [order_status_btn],
        [profile_btn, help_btn],
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    from telegram_bot.models import TelegramUser

    tg_user, created = TelegramUser.get_or_create_from_telegram(message.from_user)

    if created:
        text = (
            f"<b>👋 Добро пожаловать, {message.from_user.first_name}!</b>\n\n"
            f"Я бот интернет-магазина «Полезная микрозелень».\n\n"
            f"<b>Что я умею:</b>\n"
            f"• 🛒 Открыть магазин\n"
            f"• 📦 Проверить статус заказа\n"
            f"• 👤 Показать профиль\n"
            f"• 🔗 Привязать аккаунт на сайте\n\n"
            f"Используйте кнопки ниже или команды:\n"
            f"/start - запустить бота\n"
            f"/help - справка\n"
            f"/profile - мой профиль\n"
            f"/status - статус заказа\n"
            f"/link КОД - привязать аккаунт"
        )
    else:
        text = (
            f"<b>С возвращением, {message.from_user.first_name}!</b>\n\n"
            f"Рад видеть вас снова! 👋\n\n"
            f"Используйте кнопки ниже для навигации."
        )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard())
    logger.info(f'User {tg_user.telegram_id} started the bot')


@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    text = (
        "<b>📚 Справка по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Запустить бота\n"
        "/help - Эта справка\n"
        "/status - Статус последнего заказа\n"
        "/profile - Мой профиль\n"
        "/link КОД - Привязать аккаунт\n\n"
        "<b>Кнопки:</b>\n"
        "🛒 Открыть магазин - Переход на сайт\n"
        "📦 Статус заказа - Проверить заказ\n"
        "👤 Мой профиль - Информация о вас\n"
        "❓ Помощь - Эта справка\n\n"
        "<b>Нужна помощь?</b>\n"
        "Напишите нам: zaykova-oxana@yandex.ru"
    )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard())


@dp.message(Command('profile'))
async def cmd_profile(message: types.Message):
    from telegram_bot.models import TelegramUser

    tg_user, created = TelegramUser.get_or_create_from_telegram(message.from_user)

    if tg_user.user:
        linked_text = f"✅ Привязан к аккаунту: <b>{tg_user.user.username}</b>"
    else:
        linked_text = (
            f"❌ <b>Не привязан к аккаунту Django!</b>\n\n"
            f"Как привязать:\n"
            f"1. Зайдите на сайт\n"
            f"2. Перейдите в профиль\n"
            f"3. Нажмите «Привязать Telegram»\n"
            f"4. Отправьте полученный код боту: <code>/link КОД</code>"
        )

    text = (
        f"<b>👤 Ваш профиль</b>\n\n"
        f"<b>Telegram ID:</b> <code>{tg_user.telegram_id}</code>\n"
        f"<b>Имя:</b> {tg_user.first_name or message.from_user.first_name}\n"
        f"<b>Username:</b> @{tg_user.username or message.from_user.username}\n"
        f"<b>В боте с:</b> {tg_user.created_at.strftime('%d.%m.%Y')}\n\n"
        f"{linked_text}"
    )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard())


@dp.message(Command('status'))
async def cmd_status(message: types.Message):
    from telegram_bot.models import TelegramUser
    from shop.models import Order

    try:
        tg_user = TelegramUser.objects.get(telegram_id=message.from_user.id)
    except TelegramUser.DoesNotExist:
        await message.answer(
            "❌ Вы не зарегистрированы в боте.\nНажмите /start для регистрации",
            reply_markup=get_main_keyboard()
        )
        return

    if not tg_user.user:
        await message.answer(
            "🔗 Ваш Telegram не привязан к аккаунту!\n\n"
            "1. Зайдите на сайт\n"
            "2. Перейдите в профиль\n"
            "3. Нажмите «Привязать Telegram»\n"
            "4. Отправьте код боту: /link КОД",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard()
        )
        return

    order = Order.objects.filter(user=tg_user.user).order_by('-created_at').first()

    if not order:
        await message.answer(
            "📭 У вас пока нет заказов.\nПерейдите в магазин и сделайте первый заказ!",
            reply_markup=get_main_keyboard()
        )
        return

    status_emoji = {
        'new': '🆕', 'processing': '🔄', 'paid': '💳',
        'shipped': '📦', 'delivered': '✅', 'cancelled': '❌',
    }

    text = (
        f"<b>📦 Заказ #{order.id}</b>\n\n"
        f"{status_emoji.get(order.status, '📦')} <b>Статус:</b> {order.get_status_display()}\n"
        f"💰 <b>Сумма:</b> {order.total_price} ₽\n"
        f"📅 <b>Дата:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📍 <b>Адрес:</b> {order.address}\n\n"
        f"🔍 Подробности заказа доступны на сайте"
    )

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_keyboard())


@dp.message(Command('link'))
async def cmd_link(message: types.Message):
    from telegram_bot.models import TelegramLinkCode, TelegramUser
    from django.utils import timezone

    parts = message.text.split() if message.text else []
    if len(parts) < 2:
        await message.answer(
            "❌ Пожалуйста, отправьте код после команды:\n\n"
            f"<code>/link КОД</code>\n\n"
            f"Код можно получить в личном кабинете на сайте.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard()
        )
        return

    code = parts[1].upper()

    try:
        link_code = TelegramLinkCode.objects.get(code=code)
    except TelegramLinkCode.DoesNotExist:
        await message.answer(
            "❌ Код не найден!\n\nПроверьте правильность кода или запросите новый.",
            reply_markup=get_main_keyboard()
        )
        return

    if not link_code.is_valid():
        await message.answer(
            "⌛ Код истёк или уже использован!\n\nЗапросите новый код в личном кабинете.",
            reply_markup=get_main_keyboard()
        )
        return

    telegram_user, created = TelegramUser.get_or_create_from_telegram(message.from_user)
    telegram_user.user = link_code.user
    telegram_user.save()

    link_code.status = 'confirmed'
    link_code.telegram_id = message.from_user.id
    link_code.confirmed_at = timezone.now()
    link_code.save()

    await message.answer(
        f"🎉 <b>Аккаунты успешно привязаны!</b>\n\n"
        f"👤 <b>Ваш аккаунт:</b> {link_code.user.username}\n"
        f"📧 <b>Email:</b> {link_code.user.email}\n\n"
        f"Теперь вы будете получать уведомления о заказах в Telegram!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )

    logger.info(f"Telegram {message.from_user.id} linked to user {link_code.user.username}")


# ===== ОБРАБОТЧИКИ КНОПОК =====

@dp.message(lambda m: m.text == "📦 Статус заказа")
async def button_status(message: types.Message):
    await cmd_status(message)


@dp.message(lambda m: m.text == "👤 Мой профиль")
async def button_profile(message: types.Message):
    await cmd_profile(message)


@dp.message(lambda m: m.text == "❓ Помощь")  # ← СОВПАДАЕТ с текстом кнопки
async def button_help(message: types.Message):
    await cmd_help(message)


# ===== ЭХО-ОБРАБОТЧИК (последний!) =====

@dp.message()
async def echo_handler(message: types.Message):
    if message.text and message.text.startswith('/'):
        return

    if message.web_app_data:
        await message.answer(
            "Данные получены!",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard()
        )
        return

    await message.answer(
        "❓ Неизвестная команда.\n\nИспользуйте кнопки внизу или /help для списка команд.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )


async def main():
    logger.info("🤖 Telegram бот запущен!")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Бот остановлен пользователем")
    finally:
        try:
            if 'bot' in locals() and bot:
                asyncio.run(bot.session.close())
        except:
            pass
        
