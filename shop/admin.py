"""
Административная панель для приложения shop
"""
from django.contrib import admin
from .models import Product, Category, Tag, ProductImage, ProductReview, SupportTicket, SupportTicketAttachment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий"""
    
    # Поля, отображаемые в списке
    list_display = ('name', 'slug', 'created_at', 'get_product_count')
    
    # Поля для поиска
    search_fields = ('name', 'description')
    
    # Поля для фильтрации
    list_filter = ('created_at',)
    
    # Поля для редактирования (в форме)
    fields = ('name', 'slug', 'description')
    
    # Поля, которые нельзя редактировать
    readonly_fields = ('created_at', 'updated_at')
    
    # Автоматическое заполнение slug из name
    prepopulated_fields = {'slug': ('name',)}
    
    # Количество элементов на странице
    list_per_page = 20
    
    def get_product_count(self, obj):
        """Возвращает количество товаров в категории"""
        return obj.products.count()
    
    get_product_count.short_description = "Товаров"
    get_product_count.admin_order_field = 'products__count'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов"""
    
    list_display = ('name', 'slug', 'created_at', 'get_product_count')
    search_fields = ('name',)
    list_filter = ('created_at',)
    fields = ('name', 'slug')
    readonly_fields = ('created_at',)
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 30
    
    def get_product_count(self, obj):
        """Возвращает количество товаров с этим тегом"""
        return obj.products.count()
    
    get_product_count.short_description = "Товаров"
    get_product_count.admin_order_field = 'product__count'


class ProductImageInline(admin.TabularInline):
    """Встроенный редактор изображений в форме товара"""
    model = ProductImage
    extra = 1  # Количество пустых форм для добавления
    fields = ('image', 'alt_text', 'is_main')
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для товаров"""
    
    # Поля в списке
    list_display = (
        'name',
        'slug',
        'category',
        'price',
        'discount_price',
        'get_final_price',
        'status',
        'is_featured',
        'is_in_stock',
        'rating',
        'stock_quantity',
        'created_at'
    )
    
    # Поля для поиска
    search_fields = ('name', 'description', 'slug')
    
    # Поля для фильтрации
    list_filter = (
        'status',
        'is_featured',
        'category',
        'created_at',
        'tags'
    )
    
    # Поля для редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Цены', {
            'fields': ('price', 'discount_price'),
            'classes': ('collapse',)  # Сворачиваемая секция
        }),
        ('Категоризация', {
            'fields': ('category', 'tags')
        }),
        ('Статус и наличие', {
            'fields': ('status', 'is_featured', 'stock_quantity', 'rating')
        }),
    )
    
    # Встроенные формы для связанных моделей
    inlines = [ProductImageInline]
    
    # Автозаполнение slug
    prepopulated_fields = {'slug': ('name',)}
    
    # Количество элементов на странице
    list_per_page = 25
    
    # Действия (кнопки в админке)
    actions = ['mark_as_published', 'mark_as_draft', 'mark_as_archived', 'reset_price_to_zero']
    
    # Поля только для чтения
    readonly_fields = ('created_at', 'updated_at')
    
    # Форматирование полей
    list_editable = ('price', 'status', 'is_featured')  # Редактирование прямо в списке
    
    def mark_as_published(self, request, queryset):
        """Действие: отметить как опубликованный"""
        count = queryset.update(status='published')
        self.message_user(request, f"Опубликовано {count} товаров")
    
    mark_as_published.short_description = "Опубликовать выбранные"
    
    def mark_as_draft(self, request, queryset):
        """Действие: отметить как черновик"""
        count = queryset.update(status='draft')
        self.message_user(request, f"Переведено в черновики {count} товаров")
    
    mark_as_draft.short_description = "Сделать черновиком"
    
    def mark_as_archived(self, request, queryset):
        """Действие: отметить как архив"""
        count = queryset.update(status='archived')
        self.message_user(request, f"Перемещено в архив {count} товаров")
    
    mark_as_archived.short_description = "Переместить в архив"
    
    def reset_price_to_zero(self, request, queryset):
        """Действие: сбросить цену до 0"""
        count = queryset.update(price=0.00)
        self.message_user(request, f"Цена сброшена до 0 для {count} товаров")
    
    reset_price_to_zero.short_description = "Сбросить цену до 0"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Админка для изображений товаров"""
    
    list_display = ('product', 'image', 'alt_text', 'is_main', 'created_at')
    list_filter = ('is_main', 'created_at', 'product')
    search_fields = ('product__name', 'alt_text')
    list_per_page = 30


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """Админка для отзывов"""
    
    list_display = ('product', 'user', 'rating', 'created_at', 'get_short_comment')
    list_filter = ('rating', 'created_at', 'product')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)
    list_per_page = 20
    
    def get_short_comment(self, obj):
        """Обрезает комментарий до 50 символов"""
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    
    get_short_comment.short_description = "Комментарий"
    
@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'email','category', 'status', 'priority', 'is_resolved', 'created_at', 'days_display')
    
    list_filter = ('status', 'category', 'priority', 'is_resolved', 'created_at')
    
    search_fields = ('subject', 'email', 'message', 'response')
    
    readonly_fields = ('created_at', 'updated_at', 'user')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'email', 'subject', 'category', 'message')
        }),
        ('Статус и приоритет',{
            'fields': ('status', 'priority', 'is_resolved')
        }),
        ('Ответ администрации',{
            'fields': ('response', 'is_public'),
            'classes': ('collapse',)
        }),
        ('Даты',{
            'fields':('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_resolved', 'mark_as_in_progress', 'set_high_priority']
    
    def mark_as_resolved(self, request, queryset):
        count = queryset.update(status = 'resolved', is_resolved = True)
        self.message_user(request, f'Отмечено как решенное: {count}')
    mark_as_resolved.short_description = 'Отметить как решенное'    
    
    def mark_as_in_progress(self, request, queryset):
        count = queryset.update(status = 'in_progress')
        self.message_user(request, f'Отмечено как в работе: {count}')
    mark_as_in_progress.short_description = 'Отметить как в работе'
    
    def set_high_priority(self, request, queryset):
        count = queryset.update(priority = 'high')
        self.message_user(request, f'Установлен высокий приоритет: {count}')
    set_high_priority.short_description = 'Высокий приоритет'
    
    def days_display(self, obj):
        '''Отображение количества дней с создания'''
        days = obj.days_since_created()
        if obj.is_overdue():
            return f'Внимание {days} дней'
        return f'{days} дней'
    days_display.short_description = 'Дней'
    
@admin.register(SupportTicketAttachment)
class SupportTicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'file', 'description', 'uploaded_at', 'file_size_mb')
    list_filter = ('uploaded_at',)
    search_fields = ('ticket__subject', 'description')
    readonly_fields = ('uploaded_at',)