"""
URL конфигурация для приложения shop
"""
from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

app_name = 'shop'

urlpatterns = [
    # Главная страница
    path('', views.HomePageView.as_view(), name='home'),
    
    # Страницы "О нас" и "Контакты" (используем классы)
    path('about/', views.AboutPageView.as_view(), name='about'),
    path('contact/', views.ContactPageView.as_view(), name='contact'),
    
    # Список товаров
    path('products/', views.ProductListView.as_view(), name='product_list'),
    
    # Фильтр по категории
    path('category/<slug:category_slug>/', 
         views.ProductListView.as_view(), name='product_list_by_category'),
    
    # Фильтр по тегу
    path('tag/<slug:tag_slug>/', 
         views.ProductListView.as_view(), name='product_list_by_tag'),
    
    # Детальная страница товара
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Создание товара
    path('product/create/', views.ProductCreateView.as_view(), name='product_create'),
    
    # Редактирование товара
    path('product/<slug:slug>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    
    # Удаление товара
    path('product/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Список категорий
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # Список тегов
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    
    # Добавление отзыва
    path('product/<slug:product_slug>/review/add/', views.add_review, name='add_review'),
    
    # Корзина и оформление заказа
    path('cart/', views.cart_page, name='cart'),
    path('cart/add/<slug:product_slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    
    path('checkout/', views.checkout_page, name='checkout'),
    path('create-order/', views.create_order, name='create_order'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # === РАЗДЕЛ ПОДДЕРЖКИ ===
    # Публичные страницы
    path('support/create/', views.TicketCreateView.as_view(), name = 'ticket_create'),
    path('support/register', views.register_view, name='register'),
    
    # AJAX
    path('support/check-email/', views.check_email_ajax, name = 'check_email_ajax'),
    
    # Авторизованные пользователи
    path('support/my-tickets/', views.MyTicketsListView.as_view(), name = 'my_tickets'),
    path('support/ticket/<int:pk>/', views.TicketDetailView.as_view(), name = 'ticket_detail'),
    path('support/ticket/<int:pk>/edit', views.TicketUpdateView.as_view(), name = 'ticket_edit'),
    path('support/ticket/<int:pk>/delete/', views.TicketDeleteView.as_view(), name='ticket_delete'),
    path('support/ticket/<int:pk>/attach/', views.add_attachment, name='add_attachment'),
    
    # Админка
    path('support/admin/tickets/', views.AdminTicketListView.as_view(), name = 'admin_tickets'),
    path('support/admin/response/<int:pk>/', views.AdminResponseView.as_view(), name = 'admin_response'),

      # Вход - использует шаблон из папки registration
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # Выход
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Регистрация
    path('register/', views.register_view, name='register'),     

      # Профиль пользователя
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/avatar/upload/', views.profile_avatar_upload, name='profile_avatar_upload'),
    path('profile/avatar/delete/', views.profile_avatar_delete, name='profile_avatar_delete'),
    path('profile/orders/', views.profile_orders, name='profile_orders'),
    path('profile/reviews/', views.profile_reviews, name='profile_reviews'),
    path('profile/tickets/', views.profile_tickets, name='profile_tickets'),
    path('telegram/', include('telegram_bot.urls', namespace='telegram_bot')),
        # Предзаказ с указанием дней до исполнения
    path('preorder/<slug:product_slug>/', views.preorder_view, name='preorder'),

    

]