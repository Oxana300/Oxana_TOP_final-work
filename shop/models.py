"""
Модели для приложения магазина
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
        return self.discount_price if self.discount_price else self.price
    
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