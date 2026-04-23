"""
Представления для приложения магазина
"""
import os
import logging
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from django.utils.html import strip_tags  #  Добавлен импорт
from decimal import Decimal

from .models import (
    Product, Category, Tag, ProductReview, 
    SupportTicket, SupportTicketAttachment, 
    UserProfile, Preorder, Order, OrderItem, Cart, CartItem,   #  Добавлены Order и OrderItem, Cart, Car
    WishlistItem  # ← ДОБАВИТЬ для "избранного" 
)
from .forms import (ProductReviewForm, 
                    SupportTicketForm, 
                    SupportTicketUpdateForm, 
                    SupportResponseForm, 
                    SupportTicketAttachmentForm, 
                    UserRegistrationForm,
                    UserProfileForm,
                    UserAvatarForm,
                    UserInfoForm,
                    PreorderForm
                    )
from .utils import sanitize_text
# ✅ Инициализация логгера
logger = logging.getLogger(__name__)

# В начало файла, после импортов
PRODUCT_IMAGES = {
    'mikrozelen-brokkoli': 'brokkoli.png',
    'mikrozelen-gorchitsa': 'gorchitsa.png',
    'mikrozelen-kolrabi': 'kolrabi.png',
    'mikrozelen-podsolnechnik': 'podsoln.png',
    'mikrozelen-redis-daykon': 'redis-daykon.png',
    'mikrozelen-shpinat': 'shpinat.png',
    'mikrozelen-shavel': 'shavel.png',
    'mikrozelen-amarant': 'amaranth.png',
}

class HomePageView(TemplateView):
    """Главная страница магазина"""
    template_name = 'shop/home.html'  # Обязательно!

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Рекомендуемые товары
        context['featured_products'] = Product.published.filter(is_featured=True)[:6]
        # Новинки
        context['new_products'] = Product.published.order_by('-created_at')[:8]
        # Категории
        context['categories'] = Category.objects.all()[:6]
        # Товары для карусели
        context['carousel_products'] = Product.published.filter(
            images__isnull=False
        ).distinct().order_by('?')[:12]
        return context
    
class ProductListView(ListView):
    """Список товаров"""
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12  # Товаров на страницу

    def get_queryset(self):
        queryset = Product.published.all().select_related('category').prefetch_related('tags')
        
        # Фильтр по категории
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Фильтр по тегу
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # Сортировка
        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'name':
            queryset = queryset.order_by('name')
        elif sort == 'rating':
            queryset = queryset.order_by('-rating')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        
        # Текущая категория
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
        
        # Текущий тег
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            context['current_tag'] = get_object_or_404(Tag, slug=tag_slug)
        
        # Параметры фильтрации
        context['search'] = self.request.GET.get('search', '')
        context['sort'] = self.request.GET.get('sort', '')
        
        return context

class ProductDetailView(DetailView):
    """Страница товара"""
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Путь к папке с фото товара
        product_images_path = os.path.join(settings.BASE_DIR, 'shop', 'static', 'shop', 'images', 'products', product.slug)
        
        # Получаем все PNG файлы в папке
        product_images = []
        if os.path.exists(product_images_path):
            for file in sorted(os.listdir(product_images_path)):
                if file.endswith('.png'):
                    product_images.append(f'shop/images/products/{product.slug}/{file}')
        
        context['product_images'] = product_images
        return context

class ProductCreateView(LoginRequiredMixin, CreateView):
    """Создание товара (только для авторизованных)"""
    model = Product
    template_name = 'shop/product_form.html'
    fields = ['name', 'slug', 'description', 'price', 'discount_price', 
              'category', 'tags', 'is_featured', 'stock_quantity']
    success_url = reverse_lazy('shop:product_list')

    def form_valid(self, form):
        form.instance.status = 'published'
        messages.success(self.request, 'Товар успешно создан!')
        return super().form_valid(form)

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование товара"""
    model = Product
    template_name = 'shop/product_form.html'
    fields = ['name', 'slug', 'description', 'price', 'discount_price', 
              'category', 'tags', 'is_featured', 'stock_quantity', 'status']
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_success_url(self):
        return reverse_lazy('shop:product_detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        messages.success(self.request, 'Товар успешно обновлен!')
        return super().form_valid(form)

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление товара"""
    model = Product
    template_name = 'shop/product_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('shop:product_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Товар успешно удален!')
        return super().delete(request, *args, **kwargs)

class CategoryListView(ListView):
    """Список категорий"""
    model = Category
    template_name = 'shop/category_list.html'
    context_object_name = 'categories'

class TagListView(ListView):
    """Список тегов"""
    model = Tag
    template_name = 'shop/tag_list.html'
    context_object_name = 'tags'

def add_review(request, product_slug):
    """Добавление отзыва к товару"""
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        product = get_object_or_404(Product, slug=product_slug)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            
            # Обновляем рейтинг товара
            avg_rating = product.reviews.aggregate(models.Avg('rating'))['rating__avg']
            product.rating = avg_rating
            product.save()
            
            messages.success(request, 'Отзыв успешно добавлен!')
            return redirect('shop:product_detail', slug=product_slug)
    
    return redirect('shop:product_detail', slug=product_slug)

class AboutPageView(TemplateView):
    """Страница 'О нас'"""
    template_name = 'shop/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Информация о компании
        context['company'] = {
            'name': 'Магазин "Полезная микрозелень"',
            'founded': 2026,
            'description': 'Мы - современный интернет-магазин. Предлагаем свежую микрозелень премиум-класса, выращенную с соблюдением всех стандартов качества и готовые наборы для проращивания с подробными инструкциями.',
            'mission': 'Делать покупки удобными, выгодными и приятными для каждого клиента.',
            'values': [
                'Экологическая чистота продукции – выращиваем без химических удобрений',
                'Высокая концентрация полезных веществ в каждом ростке',
                'Доступные цены и гибкая система скидок',
                'Надёжность — быстрая доставка и гарантия',
            ],
            'stats': {
                'clients': 1500,
                'orders': 2500,
                'products': 50,
                'reviews': 800,
            }
        }
        
        # Команда компании
        context['team'] = [
            {
                'name': 'Иван Петров',
                'position': 'Генеральный директор',
                'bio': 'Основатель магазина, более 10 лет в e-commerce',
                'image': None,  # Здесь можно добавить путь к фото
            },
            {
                'name': 'Елена Соколова',
                'position': 'Руководитель отдела продаж',
                'bio': 'Поможет выбрать идеальный товар',
                'image': None,
            },
            {
                'name': 'Оксана Зайкова',
                'position': 'Главный технолог',
                'bio': 'Отвечает за качество и доставку',
                'image': None,
            },
        ]
        
        return context


class ContactPageView(TemplateView):
    """Страница 'Контакты'"""
    template_name = 'shop/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Контактная информация
        context['contacts'] = {
            'phone': '+7 (921) 459-15-74',
            'email': 'info@myshop.ru',
            'address': 'г. Сыктывкар, ул. Бабушкина, д. 19',
            'work_hours': 'Пн-Пт: 9:00 - 20:00, Сб-Вс: 10:00 - 18:00',
        }
        
        # Социальные сети
        context['social'] = [
            {'name': 'Telegram', 'icon': 'telegram', 'url': 'https://t.me/myshop'},
            {'name': 'VK', 'icon': 'vk', 'url': 'https://vk.com/myshop'},
            {'name': 'WhatsApp', 'icon': 'whatsapp', 'url': 'https://wa.me/79991234567'},
            {'name': 'Instagram', 'icon': 'instagram', 'url': 'https://instagram.com/myshop'},
        ]
        
        # Карта (можно использовать Яндекс.Карты или Google Maps)
        context['map'] = {
            'lat': 61.670411,  # Координаты центра Академии ТОП Сыктывкар
            'lng': 50.833317,
            'zoom': 15,
        }
        
        return context


# Сохраняем старые функции для обратной совместимости
def about_page(request):
    """Страница 'О нас' (для обратной совместимости)"""
    return AboutPageView.as_view()(request)


def contact_page(request):
    """Страница 'Контакты' (для обратной совместимости)"""
    return ContactPageView.as_view()(request)

def cart_page(request):
    """Страница корзины"""
    return render(request, 'shop/cart.html')

def checkout_page(request):
    """Страница оформления заказа"""
    cart = get_cart(request)
    items = cart.items.all()
    total = sum(item.get_subtotal() for item in items)
    
    if not items:
        messages.warning(request, 'Ваша корзина пуста. Добавьте товары перед оформлением заказа.')
        return redirect('shop:cart')
    
    return render(request, 'shop/checkout.html', {
        'cart_items': items,
        'total': total,
        'cart_count': cart.get_total_items()
    })

# === Раздел поддержки ===
class TicketCreateView(CreateView):
    """Создание нового обращения"""
    model = SupportTicket
    form_class = SupportTicketForm
    template_name = 'shop/support/ticket_form.html'
    success_url = reverse_lazy('shop:my_tickets')
    
    def form_valid(self, form):
        # Если пользователь авторизован, то привязываем обращение к нему
        if self.request.user.is_authenticated:
            form.instance.user = self.request.user
            
        ticket = form.save()
        
        # ✅ Очищаем данные от XSS перед отправкой email
        safe_subject = strip_tags(ticket.subject)
        safe_message = strip_tags(ticket.message)
        
        # Отправляем уведомление администраторам
        try:
            send_mail(
                subject=f'Новое обращение #{ticket.id}: {safe_subject}',
                message=f'Категория: {ticket.get_category_display()}\n\n{safe_message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin[1] for admin in settings.ADMINS],
                fail_silently=True,
            )
            logger.info(f"Email notification sent for ticket #{ticket.id}")
        except Exception as e:
            logger.error(f"Failed to send email for ticket #{ticket.id}: {str(e)}")

        # Добавляем сообщение об успехе
        messages.success(
            self.request,
            f'Обращение #{ticket.id} успешно создано! '
            f'Мы ответим вам в течение 3 рабочих дней'
        )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создать обращение'
        context['button_text'] = 'отправить обращение'
        return context
    
class MyTicketsListView(LoginRequiredMixin, ListView):
    """Список обращений пользователя"""
    model = SupportTicket
    template_name = 'shop/support/ticket_list.html'
    context_object_name = 'tickets'
    paginate_by = 10
    
    def get_queryset(self):
        # Возвращение только обращения текущего пользователя
        return SupportTicket.objects.filter(
            user = self.request.user
        ).select_related('user').order_by('-created_at')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мои обращения'
        
        # Статистика
        context['stats'] = {
            'total': SupportTicket.objects.filter(user=self.request.user).count(),
            'new': SupportTicket.objects.filter(
                user=self.request.user,
                status='new'
            ).count(),
            'in_progress': SupportTicket.objects.filter(
                user=self.request.user,
                status='in_progress'
            ).count(),
            'resolved': SupportTicket.objects.filter(
                user=self.request.user,
                is_resolved=True
            ).count(),
        }
        
        return context
    
class TicketDetailView(LoginRequiredMixin, DetailView):
        """Детальный просмотр сообщения"""
        model = SupportTicket
        template_name = 'shop/support/ticket_detail.html'
        context_object_name = 'ticket'
        
        def get_queryset(self):
             # Проверяем, что пользователь имеет доступ только к своим обращениям
            return SupportTicket.objects.filter(
            user = self.request.user
        )
            
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['title'] = f'Обращение #{self.object.id}'
            context['attachment_form'] = SupportTicketAttachmentForm()
            return context
        
class TicketUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """ Редактирование обращения (только владелец)"""
    model = SupportTicket
    form_class = SupportTicketUpdateForm
    template_name = 'shop/support/ticket_form.html'
    
    def test_func(self):
        """Проверка на владельца"""
        ticket = self.get_object()
        return ticket.user == self.request.user 
    
    def get_success_url(self):
        return reverse_lazy('shop:ticket_detail', kwargs={'pk':self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактировать обращение'
        context['button_text'] = 'Сохранить изменения'
        return context
       
    def form_valid(self, form):
        messages.success(self.request, 'Обращение успешно обновлено!')
        return super().form_valid(form)
            
class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление обращения (только владелец)"""
    model = SupportTicket
    template_name = 'shop/support/ticket_confirm_delete.html'
    success_url = reverse_lazy('shop:my_tickets')
    
    def test_func(self):
        """Проверка на владельца"""
        ticket = self.get_object()
        return ticket.user == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Обращение успешно удалено!')
        return super().delete(request, *args, **kwargs)
    
class AdminResponseView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Ответ администрации на обращение"""      
    model = SupportTicket
    form_class = SupportResponseForm
    template_name = 'shop/suport/admin_response.html'
    
    def test_func(self):
        """Проверка: ТОлько суперпользователь или персонал"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_success_url(self):
        return reverse_lazy('admin:shop_supportticket_changelist')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Ответ на обращение #{self.object.id}'
        context['ticket'] = self.object
        return context
          
    def form_valid(self, form):
        ticket = form.save(commit=False)
        
        if form.cleaned_data.get('send_notification') and ticket.is_public:
            try:
                # Очищаем ответ администратора перед отправкой
                safe_response = sanitize_text(ticket.response, 2000)
                
                send_mail(
                    subject=f'Ответ на ваше обращение #{ticket.id}',
                    message=f'Здравствуйте!\n\n{safe_response}\n\nС уважением, администрация магазина.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ticket.email],
                    fail_silently=False,
                )
                logger.info(f"Response email sent for ticket #{ticket.id}")
                messages.success(self.request, 'Ответ отправлен пользователю на email')
            except Exception as e:
                logger.error(f"Failed to send response email for ticket #{ticket.id}: {str(e)}")
                messages.warning(self.request, f'Ошибка отправки email: {str(e)}')
        
        ticket.save()
        messages.success(self.request, 'Ответ сохранен')
        return super().form_valid(form)
    
class AdminTicketListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список всех обращений в админ панели"""
    model = SupportTicket
    template_name = 'shop/suport/admin_tickets.html'    
    context_object_name = 'tickets'
    paginate_by = 20
    
    def test_func(self):
        """Проверка: ТОлько суперпользователь или персонал"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        queryset = SupportTicket.objects.all().select_related('user').order_by('-priority', '-created_at')
        
        # Фильтры
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status = status) 
            
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category = category)
            
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(subject__icontains= search) |
                Q(email__icontains = search) |
                Q(message__icontains = search)
            )   
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Все обращения'
        context['categories'] = SupportTicket.CATEGORY_CHOICES
        context['statuses'] = SupportTicket.STATUS_CHOICES
        
        context ['stats'] = {
            'total': SupportTicket.objects.count(),
            'new': SupportTicket.objects.filter(status = 'new').count(),
            'in_progress': SupportTicket.objects.filter(status = 'in_progress').count(),
            'resolved': SupportTicket.objects.filter(is_resolved = True).count(),
            'overdue':SupportTicket.objects.filter(
                status__in=['new', 'in_progress']
            ).filter(created_at__lt=timezone.now()-timedelta(days=7)).count(),
        }
        
        return context
    
@login_required
def add_attachment(request, pk):
    """Добавления вложения к обращению"""
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    if request.method == 'POST':
        form = SupportTicketAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.ticket = ticket
            attachment.save()
            messages.success(request, 'Файл успешно загружен')
            return redirect('shop:ticket_detail', pk=pk)
    else:
        form = SupportTicketAttachmentForm()
        
    return render(request, 'shop/support/add_attachment.html', {
        'form': form,
        'ticket': ticket
    })

@login_required
def check_email_ajax(request):
    """AJAX проверка email на наличие активных обращений"""
    if request.method == 'GET':
        email = request.GET.get('email', '')
        
        if email:
            active_count= SupportTicket.objects.filter(
                email = email,
                status__in=['nem', 'in_progress']
            ).count()
            
            return JsonResponse({
                'valid': active_count < 3,
                'active_count': active_count,
                'message': f'Активных обращений: {active_count} / 3' if active_count>=3 else ''
            }) 
    return JsonResponse({'error':'Invalid request'}, status=400)

def register_view(request):
    """Страница регистрации пользователя"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Дополнительная информация (если нужно сохранить телефон и возраст)
            # profile = UserProfile.objects.create(
            #     user=user,
            #     phone=form.cleaned_data.get('phone'),
            #     age=form.cleaned_data.get('age')
            # )
            
            messages.success(
                request, 
                'Регистрация прошла успешно! Теперь вы можете войти в свой аккаунт.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'shop/register.html', {
        'form': form,
        'title': 'Регистрация',
        'page_type': 'auth'
    })

class ProfileView(LoginRequiredMixin, DetailView):
    """Просмотр профиля пользователя"""
    model = UserProfile
    template_name = 'shop/profile/profile_detail.html'
    context_object_name = 'profile'
    
    def get_object(self, queryset=None):
        # Возвращаем профиль текущего пользователя
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мой профиль'
        
        # Получаем статистику пользователя
        from .models import SupportTicket, ProductReview
        
        context['stats'] = {
            'tickets_count': SupportTicket.objects.filter(user=self.request.user).count(),
            'reviews_count': ProductReview.objects.filter(user=self.request.user).count(),
            'open_tickets': SupportTicket.objects.filter(
                user=self.request.user, 
                status__in=['new', 'in_progress']
            ).count(),
        }
        
        return context


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserInfoForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('shop:profile')
    else:
        user_form = UserInfoForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    
    return render(request, 'shop/profile/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Редактирование профиля'
    })


@login_required
def profile_avatar_upload(request):
    """Загрузка аватара"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserAvatarForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Фотография профиля обновлена!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = UserAvatarForm(instance=profile)
    
    return redirect('shop:profile_edit')


@login_required
def profile_avatar_delete(request):
    """Удаление аватара"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.avatar:
        # Удаляем файл
        profile.avatar.delete()
        profile.avatar = None
        profile.save()
        messages.success(request, 'Фотография профиля удалена')
    else:
        messages.info(request, 'У вас нет фотографии профиля')
    
    return redirect('shop:profile_edit')


@login_required
def profile_orders(request):
    """История заказов пользователя"""
    # Здесь будет логика заказов
    return render(request, 'shop/profile/profile_orders.html', {
        'title': 'Мои заказы'
    })


@login_required
def profile_reviews(request):
    """Отзывы пользователя"""
    from .models import ProductReview
    
    reviews = ProductReview.objects.filter(user=request.user).select_related('product')
    
    return render(request, 'shop/profile/profile_reviews.html', {
        'reviews': reviews,
        'title': 'Мои отзывы'
    })


@login_required
def profile_tickets(request):
    """Обращения в поддержку"""
    from .models import SupportTicket
    
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'shop/profile/profile_tickets.html', {
        'tickets': tickets,
        'title': 'Мои обращения'
    })

# ручная пагинация
def product_list_fbv(request):
    """
    Список товаров с ручной пагинацией
    """
    # Получаем все товары
    products = Product.objects.filter(status='published').order_by('-created_at')
    # Создаем пагинатор
    # products - queryset 
    # 12 - количество товаров на одной странице
    paginator = Paginator(products,12)
    # Получаем номер из GET параметра (?page=2)
    page_number = request.GET.get('page')

    try:
        # Получаем объекты для текущей страницы
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Если номер страницы не число - показываем первую
        page_obj = paginator.page(1)
    except EmptyPage:
        # Если страницы не существует - показываем последнюю
        page_obj = paginator.page(paginator.num_pages)
    
    context= {
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(), #Есть ли другие объекты
        'title': 'Каталог товаров',

    }
    return render(request, 'shop/product_list.html', context)

@login_required
def preorder_view(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    
    if request.method == 'POST':
        form = PreorderForm(request.POST)
        if form.is_valid():
            preorder = form.save(commit=False)
            preorder.product = product
            preorder.user = request.user if request.user.is_authenticated else None
            preorder.save()
            
            # Отправка уведомления
            messages.success(request, f'Предзаказ на {product.name} оформлен! Мы свяжемся с вами.')
            return redirect('shop:product_detail', slug=product_slug)
    else:
        form = PreorderForm(initial={'customer_name': request.user.get_full_name(), 'email': request.user.email})
    
    return render(request, 'shop/preorder.html', {'form': form, 'product': product})


# Исправление корзины
from .models import Cart, CartItem

def get_cart(request):
    """Получение или создание корзины"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def add_to_cart(request, product_slug):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, slug=product_slug)
    cart = get_cart(request)
    
    # Проверяем, есть ли уже такой товар в корзине
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'Товар "{product.name}" добавлен в корзину!')
    
    # Возвращаемся на предыдущую страницу или на страницу корзины
    next_url = request.POST.get('next', request.GET.get('next', 'shop:cart'))
    return redirect(next_url)

def cart_page(request):
    cart = get_cart(request)
    items = cart.items.all()
    total = sum(item.get_subtotal() for item in items)
    
    return render(request, 'shop/cart.html', {
        'cart_items': items,
        'total': total,
        'cart_count': cart.get_total_items()
    })

def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('shop:cart')

@login_required
def create_order(request):
    """Создание заказа из корзины"""
    if request.method == 'POST':
        cart = get_cart(request)
        
        if not cart.items.exists():
            messages.error(request, 'Корзина пуста!')
            return redirect('shop:cart')
        
        # Создаем заказ
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=request.POST.get('email', request.user.email if request.user.is_authenticated else ''),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            postal_code=request.POST.get('postal_code', ''),
            payment_method=request.POST.get('payment_method', 'card'),
            delivery_method=request.POST.get('delivery_method', 'courier'),
            comment=request.POST.get('comment', ''),
            discount=Decimal('0.00')  # ✅ Явно указываем Decimal
        )
        
        # Переносим товары
        total = Decimal('0.00')
        for cart_item in cart.items.all():
            item_price = cart_item.product.get_final_price()
            subtotal = item_price * cart_item.quantity
            
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=item_price,
                subtotal=subtotal
            )
            total += subtotal
        
        # Обновляем суммы
        order.total_price = total
        order.final_price = total  # без скидки пока
        order.save()
        
        # Очищаем корзину
        cart.items.all().delete()
        
        messages.success(request, f'Заказ #{order.id} успешно оформлен!')
        return redirect('shop:order_confirmation', order_id=order.id)
    
    return redirect('shop:cart')


def order_confirmation(request, order_id):
    """Страница подтверждения заказа"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_confirmation.html', {'order': order})

# ==========================================
# КАСТОМНЫЙ ВХОД (LOGIN)
# ==========================================
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import UserLoginForm
import logging

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """
    Кастомизированная страница входа
    """
    authentication_form = UserLoginForm
    template_name = 'shop/login.html'
    next_page = reverse_lazy('shop:home')
    redirect_authenticated_user = True

    def get_success_url(self):
        """Определяет URL для перенаправления после входа"""
        url = self.request.GET.get('next')
        if url and url_has_allowed_host_and_scheme(url, allowed_hosts={self.request.get_host()}):
            return url
        return self.next_page

    def form_valid(self, form):
        """Обработка успешного входа"""
        response = super().form_valid(form)
        user = form.get_user()
        messages.success(
            self.request,
            f'С возвращением, {user.first_name or user.username}!'
        )
        logger.info(f'User {user.username} logged in from IP {self.request.META.get("REMOTE_ADDR")}')
        return response


# ==========================================
# ИЗБРАННОЕ (WISHLIST)
# ==========================================

@login_required
def toggle_wishlist(request, product_slug):
    """Добавление/удаление из избранного"""
    product = get_object_or_404(Product, slug=product_slug)
    
    item, created = WishlistItem.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        # Уже в избранном — удаляем
        item.delete()
        messages.info(request, f'"{product.name}" удалён из избранного 💔')
    else:
        messages.success(request, f'"{product.name}" добавлен в избранное! ❤️')
    
    # Возвращаемся туда, откуда пришли
    next_url = request.META.get('HTTP_REFERER', reverse('shop:product_list'))
    return redirect(next_url)


# ==========================================
# ИСПРАВЛЕННЫЙ create_order С БОНУСАМИ
# ==========================================

@login_required
def create_order(request):
    """Создание заказа из корзины"""
    if request.method != 'POST':
        return redirect('shop:cart')
    
    cart = get_cart(request)
    
    if not cart.items.exists():
        messages.error(request, 'Корзина пуста!')
        return redirect('shop:cart')
    
    # Создаем заказ
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        email=request.POST.get('email', request.user.email if request.user.is_authenticated else ''),
        phone=request.POST.get('phone', ''),
        address=request.POST.get('address', ''),
        city=request.POST.get('city', ''),
        postal_code=request.POST.get('postal_code', ''),
        payment_method=request.POST.get('payment_method', 'card'),
        delivery_method=request.POST.get('delivery_method', 'courier'),
        comment=request.POST.get('comment', ''),
        discount=Decimal('0.00')
    )
    
    # Переносим товары
    total = Decimal('0.00')
    for cart_item in cart.items.all():
        item_price = cart_item.product.get_final_price()
        subtotal = item_price * cart_item.quantity
        
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            price=item_price,
            subtotal=subtotal
        )
        total += subtotal
    
    # БОНУСНАЯ СИСТЕМА: обработка баллов
    use_points = int(request.POST.get('use_bonus_points', 0))
    if use_points > 0 and request.user.is_authenticated:
        profile = request.user.profile
        if use_points <= profile.bonus_points:
            discount = Decimal(use_points)
            profile.bonus_points -= use_points
            profile.save()
            order.discount = discount
            order.bonus_points_used = use_points
    
    order.total_price = total
    order.final_price = total - order.discount
    order.save()
    
    # Начисляем бонусы
    if request.user.is_authenticated:
        profile = request.user.profile
        earned = int(order.final_price)  # 1 рубль = 1 балл
        profile.bonus_points += earned
        profile.save()
        order.bonus_points_earned = earned
        order.save()
    
    # Очищаем корзину
    cart.items.all().delete()
    
    messages.success(
        request, 
        f'Заказ #{order.id} успешно оформлен! '
        f'Начислено бонусов: {order.bonus_points_earned} ✨'
    )
    return redirect('shop:order_confirmation', order_id=order.id)