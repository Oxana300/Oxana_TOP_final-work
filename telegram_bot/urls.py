from django.urls import path
from . import views

app_name = 'telegram_bot'

urlpatterns = [
    path('link/', views.link_telegram_view, name='link_telegram'),
    path('linked/', views.telegram_linked_view, name='telegram_linked'),
    path('unlink/', views.unlink_telegram_view, name='unlink_telegram'),
]