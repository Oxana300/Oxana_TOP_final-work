"""
Сигналы Django для автоматической отправки уведомлений.

Уведомление о новом заказе НЕ отправляется через post_save,
потому что при первом save() сумма заказа еще 0, а позиции заказа
создаются позже. Уведомление о новом заказе отправляется вручную
в shop/views.py после полного расчета заказа.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from shop.models import Order
from telegram_bot.utils import notify_user_about_order_status


@receiver(pre_save, sender=Order)
def remember_old_order_status(sender, instance, **kwargs):
    """Запоминаем старый статус перед сохранением заказа."""
    if not instance.pk:
        instance._old_status = None
        return

    try:
        instance._old_status = Order.objects.only('status').get(pk=instance.pk).status
    except Order.DoesNotExist:
        instance._old_status = None


@receiver(post_save, sender=Order)
def order_status_changed_signal(sender, instance, created, **kwargs):
    """Уведомляем пользователя только при изменении статуса заказа."""
    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    if old_status and old_status != instance.status and instance.user:
        notify_user_about_order_status(instance.user, instance)
