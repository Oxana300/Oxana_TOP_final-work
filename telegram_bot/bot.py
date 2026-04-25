import asyncio
import logging
import os
import sys


# Настройка бота для работы с моделями django
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
    format= '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')

SITE_URL = config('SITE_URL', default = 'https://web-production-b552f.up.railway.app/')

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()

def get_main_keyboard():
    web_app_btn = KeyboardButton(
        text='Открыть магазин',
        web_app = WebAppInfo(url=SITE_URL)
    )
    
    # КНОПКА ПРОВЕРКИ СТАТУСА ЗАКАЗА
    order_status_btn = KeyboardButton(text='Статус заказа')
    # КНОПКА ПОМОЩИ
    help_btn = KeyboardButton(text='Помощь')
    # Кнопка профиля
    profile_btn = KeyboardButton(text='Мой профиль')
    
    kb = [
        [web_app_btn],
        [order_status_btn],
        [profile_btn, help_btn],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard= kb,
        resize_keyboard=True, # параметр компактных кнопок
        one_time_keyboard= False # Не скрывать после использования
    )
    
@dp.message(Command('start'))
async def cmd_start(message:types.Message):
    # сохранение пользователя в базу
    from telegram_bot.models import TelegramUser
    tg_user,created = TelegramUser.get_or_create_from_telegram(message.from_user)
    
    if created:
        text = (
            f'<b>👋 Добро пожаловать, {message.from_user.first_name}!</b>\n\n'
            f'Я бот магазина Django.\n\n'
            f'<b>Что я умею:</b>\n'
            f'- Показывать товары'
            f'- Отслеживать заказы'
            f'- Присылать уведомления'
        )
    else:
        text = (
            f'<b>С возвращением, {message.from_user.first_name}!</b>\n\n'
            f'Рад видеть вас снова! 👋'
        )
    await message.answer(
        text,
        parse_mode= ParseMode.HTML,
        reply_markup = get_main_keyboard()
    )    
    
    logger.info(f'User {tg_user.telegram_id} started the bot')
    
@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    """
    Обработчик команды /help
    
    Показывает справку по боту
    """
    text = (
        '<b>📚 Справка по боту</b>\n\n'
        '<b>Команды:</b>\n'
        '/start - Запустить бота\n'
        '/help - Эта справка\n'
        '/status - Статус последнего заказа\n'
        '/profile - Мой профиль\n\n'
        '<b>Кнопки:</b>\n'
        '🛒 Открыть магазин - Переход на сайт\n'
        '📦 Статус заказа - Проверить заказ\n'
        '👤 Мой профиль - Информация о вас\n\n'
        '<b>Нужна помощь?</b>\n'
        'Напишите нам: support@example.com'
    )
    
    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )
    
@dp.message(Command('status'))
async def cmd_status(message:types.Message):
    """
    Обработчик команды статус
    Показывает статус последнего заказа пользователя
    """
    from telegram_bot.models import TelegramUser
    from shop.models import Order
    
    # Получаем Telegram пользователя
    try:
        tg_user = TelegramUser.objects.get(telegram_id = message.from_user.id)
    except TelegramUser.DoesNotExist:
        await message.answer("Нажмите /start для регистрации")
        return
    # Проверяем есть Django пользователь у этого telegram пользователя
    if not tg_user.user:
        await message.answer(
            "Ваш телеграм еще не привязан к аккаунту!\n\n"
            "Зайдите на сайт и привяжите аккаунт в личном кабинете."
            )
        return
    # Ищем последний заказ пользователя
    order = Order.objects.filter(user=tg_user.user).order_by('-created_at').first()
    if not order:
        await message.answer("У вас пока нет заказов")
        return
    
    # Статусы - emoji
    status_emoji = {
        'new': '🆕',
        'processing': '🔄',
        'shipped': '📦',
        'delivered': '✅',
        'cancelled': '❌',
    }
    
    text = (
        f'<b> Статус заказа# {order.id}</b>\n\n'
        f'{status_emoji.get(order.status)} <b> Статус:</b> {order.get_status_display_emoji()}\n'
        f'<b>Сумма:</b> {order.total_price} руб\n'
        f'<b>Дата создания:</b> {order.created_at.strftime("%d.%m.%Y %H:%M")}\n'
        f'<b>Адрес: </b> {order.address}\n\n'
        f'<i>Детали заказа доступны на сайте</i>'
    )
    
    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )
    
        
@dp.message(Command('profile'))
async def cmd_profile(message: types.Message):
    """
    Обработчик команды profile
    Показывает информацию о профиле
    """
    from telegram_bot.models import TelegramUser
    
    tg_user, created = TelegramUser.get_or_create_from_telegram(message.from_user)
    
    if tg_user.user:
        django_user = tg_user.user
        linked_text = f'Привязан к аккаунту: {django_user.username}'
    else: 
        linked_text = f'Не привязан к аккаунту Django'
        
    text = (
        f'<b>Ваш профиль:</b>\n\n'
        f'<b>Telegram ID:</b> <code>{tg_user.telegram_id}</code>\n'
        f'<b>Имя:</b> {tg_user.first_name or message.from_user.first_name}\n'
        f'<b>Username: </b>@{tg_user.username or message.from_user.username}\n'
        f'<b>В боте с:</b> {tg_user.created_at.strftime("%d.%m.%Y")}\n\n'
        f'{linked_text}'
    )
    
    await message.answer(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )

@dp.message(Command('link'))
async def cmd_link(message: types.Message):
    """
    Обработчик команды /link для привязки аккаунта
    
    Пользователь отправляет код который получил на сайте
    """
    from telegram_bot.models import TelegramLinkCode, TelegramUser
    from django.utils import timezone
    
    # Проверяем есть ли текст после команды
    if not message.text or len(message.text.split()) < 2:
        await message.answer(
            "❌ Пожалуйста, отправьте код после команды:\n\n"
            f"<code>/link {code}</code>\n\n"
            f"Код можно получить в личном кабинете на сайте.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Получаем код
    code = message.text.split()[1].upper()
    
    # Ищем код в базе
    try:
        link_code = TelegramLinkCode.objects.get(code=code)
    except TelegramLinkCode.DoesNotExist:
        await message.answer(
            "❌ Код не найден!\n\n"
            "Проверьте правильность кода или запросите новый в личном кабинете."
        )
        return
    
    # Проверяем статус
    if link_code.status == 'confirmed':
        await message.answer(
            "⚠️ Этот код уже был использован!\n\n"
            "Запросите новый код в личном кабинете."
        )
        return
    
    if link_code.status == 'expired':
        await message.answer(
            "⌛ Срок действия кода истёк!\n\n"
            "Запросите новый код в личном кабинете."
        )
        return
    
    if not link_code.is_valid():
        await message.answer(
            "⌛ Код больше не действителен!\n\n"
            "Запросите новый код в личном кабинете."
        )
        return
    
    # Проверяем не привязан ли уже этот Telegram
    existing_link = TelegramUser.objects.filter(
        telegram_id=message.from_user.id
    ).first()
    
    if existing_link and existing_link.user:
        await message.answer(
            f"✅ Ваш Telegram уже привязан к аккаунту {existing_link.user.username}!"
        )
        return
    
    # Привязываем аккаунты!
    telegram_user, created = TelegramUser.get_or_create_from_telegram(message.from_user)
    telegram_user.user = link_code.user
    telegram_user.save()
    
    # Обновляем код
    link_code.status = 'confirmed'
    link_code.telegram_id = message.from_user.id
    link_code.confirmed_at = timezone.now()
    link_code.save()
    
    # Поздравляем!
    await message.answer(
        f"🎉 <b>Аккаунты успешно привязаны!</b>\n\n"
        f"👤 <b>Ваш аккаунт:</b> {link_code.user.username}\n"
        f"📧 <b>Email:</b> {link_code.user.email}\n\n"
        f"Теперь вы будете получать уведомления о заказах в Telegram!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard()
    )
    
    # Уведомляем пользователя на сайте (можно добавить в будущем)
    logger.info(f"Telegram {message.from_user.id} linked to user {link_code.user.username}")

@dp.message()
async def echo_handler(message:types.Message):
    """
    Обработчик всех остальных команд/сообщений (эхо заглушка)
    """
    # Если данные из WebApp
    if message.web_app_data:
        await message.answer(
            f'Данные получены!\n\n'
            f'<code>{message.web_app_data.data}</code>',
            parse_mode=ParseMode.HTML
        )
        return
    
    if message.text and message.text.upper().startswith('TG-'):
        # Автоматически пытаемся привязать
        from telegram_bot.models import TelegramLinkCode, TelegramUser
        from django.utils import timezone
        
        code = message.text.upper().strip()
        
        try:
            link_code = TelegramLinkCode.objects.get(code=code)
            
            if link_code.is_valid():
                # Привязываем
                telegram_user, created = TelegramUser.get_or_create_from_telegram(message.from_user)
                telegram_user.user = link_code.user
                telegram_user.save()
                
                link_code.status = 'confirmed'
                link_code.telegram_id = message.from_user.id
                link_code.confirmed_at = timezone.now()
                link_code.save()
                
                await message.answer(
                    f"🎉 <b>Аккаунты успешно привязаны!</b>\n\n"
                    f"👤 <b>Ваш аккаунт:</b> {link_code.user.username}\n\n"
                    f"Теперь вы будете получать уведомления о заказах!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_main_keyboard()
                )
                return
        except:
            pass    
    
    # Обычное сообщение
    await message.answer(
        f'Вы написали: {message.text}'
        f'Используйте кнопки внизу для навигации',
        parse_mode= ParseMode.HTML,
        reply_to = message.message_id,
        reply_markup=get_main_keyboard()
    )

@dp.message()
async def echo_handler(message: types.Message):
    """
    Обработчик всех остальных сообщений
    """
    # Если данные из WebApp
    if message.web_app_data:
        await message.answer(
            f'✅ Данные получены!\n\n'
            f'<code>{message.web_app_data.data}</code>',
            parse_mode=ParseMode.HTML
        )
        return
    
    # Проверяем не код ли привязки (если нет команды /link)
    if message.text and message.text.upper().startswith('TG-'):
        # Автоматически пытаемся привязать
        from telegram_bot.models import TelegramLinkCode, TelegramUser
        from django.utils import timezone
        
        code = message.text.upper().strip()
        
        try:
            link_code = TelegramLinkCode.objects.get(code=code)
            
            if link_code.is_valid():
                # Привязываем
                telegram_user, created = TelegramUser.get_or_create_from_telegram(message.from_user)
                telegram_user.user = link_code.user
                telegram_user.save()
                
                link_code.status = 'confirmed'
                link_code.telegram_id = message.from_user.id
                link_code.confirmed_at = timezone.now()
                link_code.save()
                
                await message.answer(
                    f"🎉 <b>Аккаунты успешно привязаны!</b>\n\n"
                    f"👤 <b>Ваш аккаунт:</b> {link_code.user.username}\n\n"
                    f"Теперь вы будете получать уведомления о заказах!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=get_main_keyboard()
                )
                return
        except:
            pass
    
    # Обычное сообщение - эхо
    await message.answer(
        f'💬 Вы написали: <b>{message.text}</b>\n\n'
        f'Используйте кнопки внизу для навигации 👇',
        parse_mode=ParseMode.HTML,
        reply_to=message.message_id,
        reply_markup=get_main_keyboard()
    )
    
async def main():
    """
    Главная функция запуска бота
    """
    logger.info("Бот запущен")
    # Запускаем polling (пулинг) (опрос серверов Telegram)    
    await dp.start_polling(bot, skip_updates = True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
    finally:
        bot.session.close()
        
        
    
        