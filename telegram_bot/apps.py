from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    name = 'telegram_bot'
    default_auto_fierd = 'django.db.models.BigAutoField'
    verbose_name = 'Tekegram бот'

    def ready(self):
        """
        Регистрация сигналов при запуске джанго
        """
        import telegram_bot.signals