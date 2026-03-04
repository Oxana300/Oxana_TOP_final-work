"""
Конфигурация приложения shop
"""
from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    verbose_name = 'Магазин'

    def ready(self):
        """Выполняется при запуске приложения"""
        # Здесь можно подключить сигналы, если они есть
        # import shop.signals
        pass