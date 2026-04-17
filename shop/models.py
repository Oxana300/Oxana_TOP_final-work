"""
Модели для приложения магазина
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date
from PIL import Image

import os

class PublishedProductManager(models.Manager):
    """Менеджер для опубликованных товаров"""
    def get_queryset(self):
        """Возвращает только опубликованные товары"""
        return super().get_queryset().filter(status='published')

class InStockProductManager(models.Manager):
    """Менеджер для товаров в наличии"""
    def get_queryset(self):
        """Возвращает только товары с количеством > 0"""
        return super().get_queryset().filter(stock_quantity__gt=0)

class DiscountedProductManager(models.Manager):
    """Менеджер для товаров со скидкой"""
    def get_queryset(self):
        """Возвращает только товары со скидкой"""
        return super().get_queryset().filter(discount_price__isnull=False)

class Category(models.Model):
    """Модель категории товаров"""
    
    name = models.CharField(
        max_length=100,
        verbose_name="Название",
        unique=True
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="URL",
        help_text="Используется для создания человеко-понятного URL"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
        help_text="Описание категории"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
        db_table = 'categories'
    
    def __str__(self):
        """Отображение объекта в админке и при отладке"""
        return self.name
    
    def get_product_count(self):
        """Возвращает количество товаров в категории"""
        return self.products.count()
    
    get_product_count.short_description = "Количество товаров"

class Tag(models.Model):
    """Модель тегов для товаров"""
    
    name = models.CharField(
        max_length=50,
        verbose_name="Название",
        unique=True
    )
    
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="URL"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']
        db_table = 'tags'
    
    def __str__(self):
        """Отображение объекта в админке и при отладке"""
        return self.name
    
    def get_product_count(self):
        """Возвращает количество товаров с этим тегом"""
        return self.product_set.count()
    
    get_product_count.short_description = "Количество товаров"

class Product(models.Model):
    """Модель товара"""
    
    # Статусы товара
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('archived', 'В архиве'),
    ]
    
    # Основная информация
    name = models.CharField(
        max_length=255,
        verbose_name="Название",
        help_text="Введите название товара"
    )
    
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="URL",
        help_text="Используется для создания человеко-понятного URL"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Подробное описание товара"
    )
    
    # Цены
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        default=0.00
    )
    
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена со скидкой",
        blank=True,
        null=True,
        help_text="Оставьте пустым, если скидки нет"
    )
    
    # Связи
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Категория",
        related_name="products",
        help_text="Выберите категорию товара"
    )
    
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
        blank=True,
        related_name="products",
        help_text="Выберите теги для товара"
    )
    
    # Статус и даты
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    # Дополнительные поля
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Рекомендуемый",
        help_text="Отображать товар на главной странице"
    )
    
    rating = models.FloatField(
        default=0.0,
        verbose_name="Рейтинг",
        help_text="Средний рейтинг товара (0.0 - 5.0)"
    )
    
    stock_quantity = models.IntegerField(
        default=0,
        verbose_name="Количество на складе",
        help_text="Количество доступных единиц товара"
    )
    
    # Менеджеры моделей
    objects = models.Manager()  # Стандартный менеджер
    
    published = PublishedProductManager()
    in_stock = InStockProductManager()
    discounted = DiscountedProductManager()
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']
        db_table = 'products'
        indexes = [
            models.Index(fields=['slug'], name='product_slug_idx'),
            models.Index(fields=['status'], name='product_status_idx'),
            models.Index(fields=['category'], name='product_category_idx'),
        ]
    
    def __str__(self):
        """Отображение объекта в админке и при отладке"""
        return f"{self.name} - ${self.get_final_price()}"
    
    def get_final_price(self):
        """Возвращает цену со скидкой, если она есть, иначе обычную цену"""
        return self.discount_price if self.discount_price and self.discount_price > 0 else self.price
    
    
    get_final_price.short_description = "Итоговая цена"
    
    def is_in_stock(self):
        """Проверяет, есть ли товар в наличии"""
        return self.stock_quantity > 0
    
    is_in_stock.boolean = True  # Отображает как иконку в админке
    is_in_stock.short_description = "В наличии"
    
    def get_discount_percentage(self):
        """Возвращает процент скидки"""
        if self.discount_price and self.price > 0:
            return round((1 - self.discount_price / self.price) * 100, 1)
        return 0
    
    get_discount_percentage.short_description = "Скидка (%)"
    
    def get_absolute_url(self):
        """Возвращает абсолютный URL товара"""
        return f'/product/{self.slug}/'

class ProductImage(models.Model):
    """Модель изображений товара"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name="images"
    )
    
    image = models.ImageField(
        upload_to='products/',
        verbose_name="Изображение",
        help_text="Загрузите изображение товара"
    )
    
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Описание изображения",
        help_text="Текст для доступности (alt attribute)"
    )
    
    is_main = models.BooleanField(
        default=False,
        verbose_name="Главное изображение"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата загрузки"
    )
    
    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ['-is_main', 'id']
        db_table = 'product_images'
    
    def __str__(self):
        """Отображение объекта в админке и при отладке"""
        return f"{self.product.name} - {self.alt_text or 'Изображение'}"

class ProductReview(models.Model):
    """Модель отзывов о товаре"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name="reviews"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name="Рейтинг",
        help_text="Оцените товар от 1 до 5"
    )
    
    comment = models.TextField(
        verbose_name="Отзыв",
        help_text="Напишите ваш отзыв о товаре"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    class Meta:
        verbose_name = "Отзыв о товаре"
        verbose_name_plural = "Отзывы о товарах"
        ordering = ['-created_at']
        db_table = 'product_reviews'
    
    def __str__(self):
        """Отображение объекта в админке и при отладке"""
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"
    
class SupportTicket(models.Model):
    """Модель обращения в поддержку"""
    CATEGORY_CHOICES = [
        ('question', 'Вопрос'),
        ('complant', 'Жалоба'),
        ('suggestion', 'Предложение'),
        ('technical', 'Техническая проблема'),
        ('other', 'Другое'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'Новые'),
        ('in_progress', 'В работе'),
        ('resolved', 'Решено'),
        ('closed', 'Закрыто'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'низкий'),
        ('medium', 'средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete= models.CASCADE,
        verbose_name= "Пользователь",
        related_name="support_tickets",
        null=True,
        blank=True
    )
    
    email = models.EmailField(
        verbose_name="Email для связи",
        help_text="На этот email придёт ответ"
    )
    
    # Основная информация
    subject = models.CharField(
        max_length=200,
        verbose_name="Тема обращения",
        help_text="Кратко опишите суть вопроса"
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='question',
        verbose_name="Категория"
    )
    
    message = models.TextField(
        verbose_name="Текст обращения",
        help_text="Подробно опишите вашу проблему или вопрос",
        max_length=5000
    )
    
    # Статус и приоритет
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Приоритет"
    )
    
    # Ответ администрации
    response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ответ администрации",
        help_text="Ответ будет виден только после публикации"
    )
    
    # Даты
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    # Флаги
    is_resolved = models.BooleanField(
        default=False,
        verbose_name="Обращение решено"
    )
    
    is_public = models.BooleanField(
        default=False,
        verbose_name="Опубликовать ответ",
        help_text="Если отмечено, ответ будет виден пользователю"
    )    
    
    class Meta:
        verbose_name = "Обращение в поддержку"
        verbose_name_plural = 'Обращение в поддержку'
        ordering = ['-priority','-created_at']
        db_table = 'support_tickets'
        indexes = [
            models.Index(fields=['status'], name='tickets_status_idx'),
            models.Index(fields=['category'], name='ticket_category_idx'),
            models.Index(fields=['email'], name = 'ticket_email_idx'),
        ]
    
    def __str__(self):
        """Отображение объекта в админ панели"""
        return f'#{self.id} - {self.subject} ({self.get_status_display()})'
    
    def get_priority_order(self):
        """Возвращает числовое значение приоритета для сортировки"""
        priority_order = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1 }
        return priority_order.get(self.priority, 0)
    
    def days_since_created(self):
        """Возвращает количество дней с момента создания"""
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        return delta.days
    
    def is_overdue(self):
        """Проверяет просрочено ли обращение (7 дней)"""
        return self.days_since_created() > 7 and self.status != 'resolved'
    
class SupportTicketAttachment(models.Model):
    """Вложения к обращениям"""
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        verbose_name= 'Образение',
        related_name="attachments"
    )
    
    file = models.FileField(
        upload_to='support_attachments/',
        verbose_name='Файл',
        help_text = "Максимальный размер 5МБ"
    )
    
    description = models.CharField(
        max_length=200,
        blank = True,
        verbose_name='Описание'
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add = True,
        verbose_name = "Дата загрузки"
    )
    
    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = "Вложение"
        db_table = 'support_ticket_attachments'
        
    def __str__(self):
        return f'{self.ticket.subject} - {self.file.name}'
    
    def file_size_mb(self):
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0
    
    def clean(self):
        if self.file and self.file.size > 5 * 1024 * 1024:
            raise ValidationError('Файл не должен превышать 5 МБ')
    
class UserProfile(models.Model):
    """Профиль пользователя магазина"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name='profile'
    )
    
    # Личная информация
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон",
        blank=True,
        null=True
    )
    
    birth_date = models.DateField(
        verbose_name="Дата рождения",
        blank=True,
        null=True
    )
    
    # Адрес доставки по умолчанию
    default_address = models.TextField(
        verbose_name="Адрес доставки",
        blank=True,
        null=True,
        help_text="Адрес доставки по умолчанию"
    )
    
    # Фотография профиля
    avatar = models.ImageField(
        upload_to='avatars/',
        verbose_name="Фотография профиля",
        blank=True,
        null=True,
        help_text="Загрузите ваше фото (до 2 МБ, форматы: JPG, PNG)"
    )
    
    # Дополнительные поля
    bio = models.TextField(
        verbose_name="О себе",
        blank=True,
        null=True,
        max_length=500,
        help_text="Расскажите немного о себе"
    )
    
    # Настройки уведомлений
    email_notifications = models.BooleanField(
        verbose_name="Получать email-уведомления",
        default=True
    )
    
    # Дата регистрации профиля
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания профиля"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Профиль: {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Переопределяем save для обработки изображения"""
        super().save(*args, **kwargs)
        
        # Если загружено изображение, обрабатываем его
        if self.avatar:
            self.resize_avatar()
    
    def resize_avatar(self):
        """Изменяет размер аватара до оптимальных размеров"""
        try:
            img_path = self.avatar.path
            if os.path.exists(img_path):
                img = Image.open(img_path)
                
                # Изменяем размер до 300x300, сохраняя пропорции
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(img_path)
        except Exception as e:
            print(f"Ошибка при обработке изображения: {e}")
    
    def avatar_url(self):
        """Возвращает URL аватара или путь к изображению по умолчанию"""
        if self.avatar:
            return self.avatar.url
        return '/static/img/default-avatar.png'
    
    def get_full_name_or_username(self):
        """Возвращает полное имя или username"""
        if self.user.get_full_name():
            return self.user.get_full_name()
        return self.user.username
    
    @property
    def initials(self):
        """Возвращает инициалы пользователя"""
        name_parts = self.user.get_full_name().split()
        if len(name_parts) >= 2:
            return f"{name_parts[0][0]}{name_parts[1][0]}".upper()
        elif self.user.username:
            return self.user.username[0].upper()
        return "U"
    
    @property
    def age(self):
        """Возвращает возраст пользователя на основе даты рождения"""
        if self.birth_date:
            today = date.today()
            age = today.year - self.birth_date.year
            # Корректировка, если день рождения еще не наступил в этом году
            if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
                age -= 1
            return age
        return None
    
    @property
    def is_adult(self):
        """Проверяет, является ли пользователь совершеннолетним"""
        age = self.age
        return age is not None and age >= 18
    
class Order(models.Model):
    """
    Модель заказа покупателя
    
    Содержит информацию о заказе:
    - Кто заказал (пользователь)
    - Что заказал (товары через OrderItem)
    - Куда доставить (адрес)
    - Статус заказа
    - Общая сумма
    """
    
    # СТАТУСЫ ЗАКАЗА
    STATUS_CHOICES = [
        ('new', '🆕 Новый'),
        ('processing', '🔄 В обработке'),
        ('paid', '💳 Оплачен'),
        ('shipped', '📦 Отправлен'),
        ('delivered', '✅ Доставлен'),
        ('cancelled', '❌ Отменён'),
    ]
    
    # СПОСОБЫ ОПЛАТЫ
    PAYMENT_CHOICES = [
        ('card', '💳 Банковская карта'),
        ('cash', '💵 Наличные'),
        ('online', '🌐 Онлайн оплата'),
    ]
    
    # СПОСОБЫ ДОСТАВКИ
    DELIVERY_CHOICES = [
        ('pickup', '🏪 Самовывоз'),
        ('courier', '🚚 Курьер'),
        ('post', '📮 Почта'),
        ('cdek', '📦 CDEK'),
    ]
    
    # ===== СВЯЗЬ С ПОЛЬЗОВАТЕЛЕМ =====
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Пользователь",
        null=True,
        blank=True
    )
    
    # ===== КОНТАКТНЫЕ ДАННЫЕ (для гостей) =====
    email = models.EmailField(
        verbose_name="Email",
        help_text="Для связи и уведомлений"
    )
    
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон",
        help_text="Формат: +7 (XXX) XXX-XX-XX"
    )
    
    # ===== АДРЕС ДОСТАВКИ =====
    address = models.TextField(
        verbose_name="Адрес доставки",
        help_text="Город, улица, дом, квартира"
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name="Город"
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Почтовый индекс"
    )
    
    # ===== ДЕТАЛИ ЗАКАЗА =====
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус"
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='card',
        verbose_name="Способ оплаты"
    )
    
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='courier',
        verbose_name="Способ доставки"
    )
    
    # ===== ЦЕНЫ =====
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Общая сумма"
    )
    
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Скидка"
    )
    
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Итоговая сумма"
    )
    
    # ===== КОММЕНТАРИИ =====
    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий к заказу",
        help_text="Пожелания к доставке"
    )
    
    # ===== ДАТЫ =====
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата оплаты"
    )
    
    shipped_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата отправки"
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата доставки"
    )
    
    # ===== TRACKING =====
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Трекинг номер"
    )
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']
        db_table = 'orders'
        indexes = [
            models.Index(fields=['status'], name='order_status_idx'),
            models.Index(fields=['user'], name='order_user_idx'),
            models.Index(fields=['created_at'], name='order_created_idx'),
        ]
    
    def __str__(self):
        return f"Заказ #{self.id} от {self.email}"
    
    def save(self, *args, **kwargs):
        """
        Автоматически рассчитывает итоговую сумму
        """
        # Считаем сумму товаров
        self.total_price = sum(item.get_subtotal() for item in self.items.all())
        
        # Применяем скидку
        self.final_price = self.total_price - self.discount
        
        super().save(*args, **kwargs)
    
    def get_status_display_emoji(self):
        """Возвращает эмодзи статуса"""
        emoji_map = {
            'new': '🆕',
            'processing': '🔄',
            'paid': '💳',
            'shipped': '📦',
            'delivered': '✅',
            'cancelled': '❌',
        }
        return emoji_map.get(self.status, '📦')
    
    def items_count(self):
        """Возвращает количество товаров в заказе"""
        return sum(item.quantity for item in self.items.all())
    
    items_count.short_description = "Количество товаров"


class OrderItem(models.Model):
    """
    Позиция заказа (товар в заказе)
    
    Связывает заказ с конкретными товарами
    Один заказ может содержать много позиций (OrderItem)
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Заказ"
    )
    
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена за единицу",
        help_text="Цена на момент заказа"
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма позиции",
        editable=False
    )
    
    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        db_table = 'order_items'
        unique_together = ['order', 'product']
    
    def __str__(self):
        return f"{self.product.name} × {self.quantity}"
    
    def save(self, *args, **kwargs):
        """
        Автоматически рассчитывает сумму позиции
        """
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
    
    def get_subtotal(self):
        """Возвращает сумму позиции"""
        return self.subtotal


class Cart(models.Model):
    """
    Корзина покупателя
    
    Хранит товары до оформления заказа
    Может быть привязана к пользователю или сессии
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Пользователь"
    )
    
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Ключ сессии"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        db_table = 'carts'
    
    def __str__(self):
        if self.user:
            return f"Корзина {self.user.username}"
        return f"Корзина (сессия: {self.session_key[:8]}...)"
    
    def get_total_items(self):
        """Общее количество товаров в корзине"""
        return sum(item.quantity for item in self.items.all())
    
    def get_total_price(self):
        """Общая сумма корзины"""
        return sum(item.get_subtotal() for item in self.items.all())
    
    def clear(self):
        """Очистить корзину"""
        self.items.all().delete()    


class CartItem(models.Model):
    """
    Товар в корзине
    """
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Корзина"
    )
    
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )
    
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлен"
    )
    
    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        db_table = 'cart_items'
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.product.name} × {self.quantity}"
    
    def get_subtotal(self):
        """Сумма позиции"""
        return self.product.get_final_price() * self.quantity
    
    
class Preorder(models.Model):
    """Модель предзаказа"""
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        verbose_name="Товар",
        related_name="preorders"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Пользователь"
    )
    customer_name = models.CharField(max_length=100, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    days_to_delivery = models.PositiveIntegerField(verbose_name="Дней до исполнения")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_processed = models.BooleanField(default=False, verbose_name="Обработан")
    
    class Meta:
        verbose_name = "Предзаказ"
        verbose_name_plural = "Предзаказы"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Предзаказ #{self.id} - {self.product.name} ({self.customer_name})"