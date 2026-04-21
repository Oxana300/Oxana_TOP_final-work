"""
Сигналы Django для автоматической отправки уведомлений
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from shop.models import Order
from telegram_bot.utils import notify_admins_about_order, notify_user_about_order_status

@receiver(post_save, sender=Order)
def order_created_signal(sender,instance,created, **kwargs):
    '''
    Срабатывает при создании или обновлении заказа
    sender - Модель Order
    instance - Экземпляр класса
    created - True, если создан новый объект
    '''
    
    if created:
        notify_admins_about_order(instance)
        
        if instance.user:
            # ✅ Правильно: передаем только заказ (user есть внутри instance)
            notify_user_about_order_status(instance)
    else:
        if instance.pk:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.status != instance.status:
                if instance.user:
                    # ✅ Правильно: передаем только заказ
                    notify_user_about_order_status(instance)
                    