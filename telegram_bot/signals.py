"""
Сигналы Django для автоматической отправки уведомлений
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from shop.models import Order
from telegram_bot.utils import notify_admins_about_order, notify_user_about_order_status

@receiver(post_save, sender=Order)
def order_creater_signal(sender, instance, created, **kwargs):
    """
    Срабатывает при создании или обновлении заказа
    sender = модель Order
    instance - экземпляр класса
    created - True, если создан новыйобъект
    """

    if created:
        # Новый заказ - уведомление админам
        notify_admins_about_order(instance)

        if instance.user:
            # уведомление пользователям
            notify_user_about_order_status(instance.user, instance)

    else:
        # заказ обновился - проверяем статус
        if hasattr(instance, '_old_status'):
            if instance._old_status != instance.status:
                # 
                if instance.user:
                    notify_user_about_order_status(instance.user, instance)
