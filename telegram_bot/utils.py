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

def notify_admins_about_order(order):
    """Уведомление администраторов о новом заказе"""
    try:
        from asgiref.sync import async_to_sync
        from aiogram import Bot
        from decouple import config
        from django.contrib.auth.models import User
        
        bot_token = config('TELEGRAM_BOT_TOKEN')
        bot = Bot(token=bot_token)
        
        # Получаем всех администраторов (is_staff=True или is_superuser)
        admins = User.objects.filter(is_staff=True)
        
        # Формируем сообщение о заказе
        message = f"🆕 <b>Новый заказ #{order.id}</b>\n\n"
        message += f"Клиент: {order.user.get_full_name() or order.user.username}\n"
        message += f"Сумма: {order.total_price} руб.\n"
        message += f"Статус: {order.get_status_display()}\n"
        # Добавьте другие поля заказа по необходимости
        
        # Отправляем сообщение каждому админу, у которого есть Telegram
        for admin in admins:
            try:
                telegram_user = TelegramUser.objects.get(user=admin)
                if telegram_user.telegram_id:
                    async_to_sync(send_telegram_message_async)(
                        bot, 
                        telegram_user.telegram_id, 
                        message
                    )
            except TelegramUser.DoesNotExist:
                continue
                
    except Exception as e:
        logger.error(f"Ошибка при уведомлении админов о заказе #{order.id}: {e}")

def notify_user_about_order_status(order):
    """Уведомление пользователя об изменении статуса заказа"""
    try:
        from asgiref.sync import async_to_sync
        from aiogram import Bot
        from decouple import config
        
        bot_token = config('TELEGRAM_BOT_TOKEN')
        bot = Bot(token=bot_token)
        
        # Получаем Telegram пользователя
        try:
            telegram_user = TelegramUser.objects.get(user=order.user)
            if not telegram_user.telegram_id:
                return
        except TelegramUser.DoesNotExist:
            return
        
        # Формируем сообщение об изменении статуса
        message = f"📦 <b>Обновление статуса заказа #{order.id}</b>\n\n"
        message += f"Новый статус: <b>{order.get_status_display()}</b>\n\n"
        
        # Добавляем дополнительную информацию в зависимости от статуса
        status_display = order.get_status_display()
        if 'доставлен' in status_display.lower() or order.status == 'delivered':
            message += "✅ Ваш заказ доставлен. Спасибо за покупку!"
        elif 'отмен' in status_display.lower() or order.status == 'cancelled':
            message += "❌ Ваш заказ отменен."
        elif 'отправлен' in status_display.lower() or order.status == 'shipped':
            message += "🚚 Ваш заказ отправлен. Ожидайте доставку."
        
        
        # Отправляем сообщение
        async_to_sync(send_telegram_message_async)(
            bot,
            telegram_user.telegram_id,
            message
        )
        
    except Exception as e:
        logger.error(f"Ошибка при уведомлении пользователя о заказе #{order.id}: {e}")


# ОКСАНА Убрала пока не определюсь.
"""
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
"""

