import logging
import asyncio
from django.conf import settings
from telegram_bot.models import TelegramNotification, TelegramUser

logger = logging.getLogger(__name__)

def send_telegram_message(telegram_id, message):
    """
    Отправка сообщения только заданному Telegram id
    """
    from aiogram import Bot
    from decouple import config
    
    bot_token = config('TELEGRAM_BOT_TOKEN')
    bot = Bot(token= bot_token)
    
    
    try:
        asyncio.run(bot.send_message(
            chat_id = telegram_id,
            text = message,
            parse_mode = 'HTML'
        ))     
        TelegramNotification.objects.create(
            telegram_user = TelegramUser.objects.get(telegram_id = telegram_id),
            message = message,
            status = 'sent'
        )
        
        logger.info(f'Message sent to {telegram_id}')
        return True
    except Exception as e:
        logger.error(f'Failed to send message to {telegram_id}: {e}')
        # логируем ошибку
        try: 
            tg_user = TelegramUser.objects.get(telegram_id = telegram_id)
            TelegramNotification.objects.create(
                telegram_user = tg_user,
                message = message,
                status = 'failed',
                error_message = str(e)
            )
        except:
            pass
        return False
    finally:
        asyncio.run(bot.session.close())


def notify_admins_about_order(order):
    """
    Уведомляет админов о новом заказе
    """
    
    from decouple import config
    
    admin_ids = config('TELEGRAM_ADMIN_IDS', default='', cast= lambda x: [int(i) for i in x.split(',')])
    
    if not admin_ids:
        logger.warning("TELEGRAM_ADMIN_IDS not configured")
        return
    
    message = (
        f'<b>Новый заказ #{order.id}</b>\n\n'
        f'<b>Клиент: {order.user.get_full_name() or order.user.username} </b>\n'
        f'<b>Email: {order.user.email}</b>\n'
        f'<b>Сумма: </b> {order.total_price} руб\n'
        f'<b>Адрес:</b>{order.address}\n\n'
        f'Проверьте админку для деталей'
    )
    
    for admin_id in admin_ids:
        send_telegram_message(admin_id, message)
        
def notify_user_about_order_status(user, order):
    """
    Уведомление пользователя об изменении статуса заказа
    """
    try:
        tg_user = user.telegram_profile
    except:
        return
    
    status_emoji = {
        'new': '🆕',
        'processing': '🔄',
        'shipped': '📦',
        'delivered': '✅',
        'cancelled': '❌',
    }
    
    message = (
        f'{status_emoji.get(order.status)} <b>Статус заказа # {order.id} изменен </b>\n\n'
        f'Текущий статус: <b>{order.get_status_display()}</b>\n\n'
        f'Проверьте детали в личном кабинете'
    )
    send_telegram_message(tg_user.telegram_id, message )