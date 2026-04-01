from django.db import models

# Create your models here.
# telegram_bot/models.py

from django.contrib.auth.models import User

# telegram_bot/models.py

import secrets
import string

class TelegramLinkCode(models.Model):
    """
    Временный код для привязки Telegram к аккаунту Django
    
    Как работает:
    1. Пользователь запрашивает код на сайте
    2. Код сохраняется в базе (действует 10 минут)
    3. Пользователь отправляет код боту
    4. Бот проверяет код и привязывает аккаунты
    """
    
    # Уникальный код (например: TG-ABC123)
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Код привязки"
    )
    
    # Пользователь Django
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='telegram_link_codes',
        verbose_name="Пользователь"
    )
    
    # Telegram ID (заполняется когда бот проверит код)
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Telegram ID"
    )
    
    # Статус
    STATUS_CHOICES = [
        ('pending', '⏳ Ожидает'),
        ('confirmed', '✅ Подтверждён'),
        ('expired', '⌛ Истёк'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    
    # Даты
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    expires_at = models.DateTimeField(
        verbose_name="Действует до"
    )
    
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата подтверждения"
    )
    
    class Meta:
        verbose_name = "Код привязки Telegram"
        verbose_name_plural = "Коды привязки Telegram"
        db_table = 'telegram_link_codes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} ({self.user.username})"
    
    def is_valid(self):
        """Проверяет действителен ли код"""
        from django.utils import timezone
        return (
            self.status == 'pending' and
            timezone.now() < self.expires_at
        )
    
    def generate_code(cls, user, valid_minutes=10):
        """
        Генерирует новый код привязки
        
        Args:
            user: Пользователь Django
            valid_minutes: Сколько минут действует код
        
        Returns:
            TelegramLinkCode: Новый объект кода
        """
        from django.utils import timezone
        import random
        
        # Генерируем случайный код (6 символов)
        chars = string.ascii_uppercase + string.digits
        code = 'TG-' + ''.join(random.choices(chars, k=6))
        
        # Проверяем что код уникальный
        while cls.objects.filter(code=code).exists():
            code = 'TG-' + ''.join(random.choices(chars, k=6))
        
        # Создаём код
        expires_at = timezone.now() + timezone.timedelta(minutes=valid_minutes)
        
        link_code = cls.objects.create(
            code=code,
            user=user,
            expires_at=expires_at
        )
        
        return link_code
    
    generate_code = classmethod(generate_code)


# Обновите существующую модель TelegramUser
class TelegramUser(models.Model):
    """
    Привязка пользователя Django к Telegram аккаунту
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='telegram_profile',
        null=True,
        blank=True,
        verbose_name="Пользователь Django"
    )
    
    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name="Telegram ID"
    )
    
    username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Username Telegram"
    )
    
    first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Имя"
    )
    
    is_bot_user = models.BooleanField(
        default=False,
        verbose_name="Это бот?"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата привязки"
    )
    
    class Meta:
        verbose_name = "Telegram пользователь"
        verbose_name_plural = "Telegram пользователи"
        db_table = 'telegram_users'
    
    def __str__(self):
        return f"@{self.username} ({self.telegram_id})"
    
    @classmethod
    def get_or_create_from_telegram(cls, telegram_user):
        """
        Создаёт или получает TelegramUser из данных Telegram
        """
        obj, created = cls.objects.get_or_create(
            telegram_id=telegram_user.id,
            defaults={
                'username': telegram_user.username or '',
                'first_name': telegram_user.first_name or '',
                'is_bot_user': telegram_user.is_bot,
            }
        )
        
        if not created:
            obj.username = telegram_user.username or ''
            obj.first_name = telegram_user.first_name or ''
            obj.save()
        
        return obj, created
    
class TelegramNotification(models.Model):
    """
    История отправленных уведомлений
    """
    
    STATUS_CHOICES = [
        ('pending', '⏳ Ожидает'),
        ('sent', '✅ Отправлено'),
        ('failed', '❌ Не удалось'),
    ]
    
    telegram_user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Получатель"
    )
    
    message = models.TextField(
        verbose_name="Текст сообщения"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата отправки"
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name="Ошибка"
    )
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-sent_at']
        db_table = 'telegram_notifications'
    
    def __str__(self):
        return f"{self.telegram_user} - {self.status}"
    
# telegram_bot/models.py

from django.db import models
from django.contrib.auth.models import User
import secrets
import string


class TelegramLinkCode(models.Model):
    """
    Временный код для привязки Telegram к аккаунту Django
    
    Как работает:
    1. Пользователь запрашивает код на сайте
    2. Код сохраняется в базе (действует 10 минут)
    3. Пользователь отправляет код боту
    4. Бот проверяет код и привязывает аккаунты
    """
    
    # Уникальный код (например: TG-ABC123)
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Код привязки"
    )
    
    # Пользователь Django
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='telegram_link_codes',
        verbose_name="Пользователь"
    )
    
    # Telegram ID (заполняется когда бот проверит код)
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Telegram ID"
    )
    
    # Статус
    STATUS_CHOICES = [
        ('pending', '⏳ Ожидает'),
        ('confirmed', '✅ Подтверждён'),
        ('expired', '⌛ Истёк'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Статус"
    )
    
    # Даты
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    expires_at = models.DateTimeField(
        verbose_name="Действует до"
    )
    
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата подтверждения"
    )
    
    class Meta:
        verbose_name = "Код привязки Telegram"
        verbose_name_plural = "Коды привязки Telegram"
        db_table = 'telegram_link_codes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} ({self.user.username})"
    
    def is_valid(self):
        """Проверяет действителен ли код"""
        from django.utils import timezone
        return (
            self.status == 'pending' and
            timezone.now() < self.expires_at
        )
    
    def generate_code(cls, user, valid_minutes=10):
        """
        Генерирует новый код привязки
        
        Args:
            user: Пользователь Django
            valid_minutes: Сколько минут действует код
        
        Returns:
            TelegramLinkCode: Новый объект кода
        """
        from django.utils import timezone
        import random
        
        # Генерируем случайный код (6 символов)
        chars = string.ascii_uppercase + string.digits
        code = 'TG-' + ''.join(random.choices(chars, k=6))
        
        # Проверяем что код уникальный
        while cls.objects.filter(code=code).exists():
            code = 'TG-' + ''.join(random.choices(chars, k=6))
        
        # Создаём код
        expires_at = timezone.now() + timezone.timedelta(minutes=valid_minutes)
        
        link_code = cls.objects.create(
            code=code,
            user=user,
            expires_at=expires_at
        )
        
        return link_code
    
    generate_code = classmethod(generate_code)
