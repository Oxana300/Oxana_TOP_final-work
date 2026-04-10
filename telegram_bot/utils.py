import logging
import asyncio
from django.conf import settings
from telegram_bot.models import TelegramNotification, TelegramUser


logger = logging.getLogger(__name__)

async def send_telegram_message_async(bot, telegram_id, message, timeout=30):
    """Асинхронная отправка сообщения с таймаутом"""
    try:
        await asyncio.wait_for(
            bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='HTML'
            ),
            timeout=timeout
        )
        return True, None
    except asyncio.TimeoutError:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def send_telegram_message(telegram_id, message):
    """Отправка сообщения в Telegram (синхронная обертка)"""
    from aiogram import Bot
    from decouple import config
    
    bot_token = config('TELEGRAM_BOT_TOKEN')
    bot = Bot(token=bot_token)
    
    try:
        # Проверяем, запущен ли цикл событий
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Нет запущенного цикла - используем asyncio.run()
            success, error = asyncio.run(send_telegram_message_async(bot, telegram_id, message))
        else:
            # Цикл уже запущен - создаем задачу
            if loop.is_running():
                task = asyncio.create_task(send_telegram_message_async(bot, telegram_id, message))
                # Даем время на выполнение (опционально)
                success, error = loop.run_until_complete(task)
            else:
                success, error = asyncio.run(send_telegram_message_async(bot, telegram_id, message))
        
        if success:
            # Сохраняем успешное уведомление
            try:
                tg_user = TelegramUser.objects.get(telegram_id=telegram_id)
                TelegramNotification.objects.create(
                    telegram_user=tg_user,
                    message=message,
                    status='sent'
                )
            except TelegramUser.DoesNotExist:
                pass
            
            logger.info(f'Message sent to {telegram_id}')
            return True
        else:
            raise Exception(error)
            
    except Exception as e:
        logger.error(f'Failed to send message to {telegram_id}: {e}')
        
        # Логируем ошибку
        try:
            tg_user = TelegramUser.objects.get(telegram_id=telegram_id)
            TelegramNotification.objects.create(
                telegram_user=tg_user,
                message=message,
                status='failed',
                error_message=str(e)
            )
        except TelegramUser.DoesNotExist:
            pass
        
        return False
    finally:
        # Закрываем сессию бота
        asyncio.create_task(bot.session.close())