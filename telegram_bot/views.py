from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import TelegramLinkCode, TelegramUser
from decouple import config

@login_required
def link_telegram_view(request):
    """
    Страница привязки Telegram аккаунта
    
    Показывает код который нужно отправить боту
    """
    # Проверяем уже ли привязан
    try:
        existing_link = request.user.telegram_profile
        return redirect('telegram_bot:telegram_linked')
    except:
        pass
    
    # Генерируем новый код если нет активного
    active_code = TelegramLinkCode.objects.filter(
        user=request.user,
        status='pending',
        expires_at__gt=timezone.now()
    ).first()
    
    if not active_code:
        active_code = TelegramLinkCode.generate_code(request.user)
    
    context = {
        'code': active_code.code,
        'expires_at': active_code.expires_at,
        'bot_username': config('TELEGRAM_BOT_USERNAME', default='myshop_bot'), 
    }
    
    return render(request, 'telegram_bot/link_telegram.html', context)


@login_required
def telegram_linked_view(request):
    """Страница успешной привязки"""
    try:
        telegram_profile = request.user.telegram_profile
        if not telegram_profile.user:  # Проверяем, что привязан
            return redirect('telegram_bot:link_telegram')
            
        context = {
            'telegram_username': telegram_profile.username or 'не указан',
            'telegram_id': telegram_profile.telegram_id,
        }
        return render(request, 'telegram_bot/telegram_linked.html', context)
    except (TelegramUser.DoesNotExist, AttributeError):
        messages.info(request, 'Telegram аккаунт не привязан')
        return redirect('telegram_bot:link_telegram')
    
@login_required
def unlink_telegram_view(request):
    """
    Отвязка Telegram аккаунта
    """
    try:
        telegram_profile = request.user.telegram_profile
        telegram_profile.user = None
        telegram_profile.save()
        
        messages.success(request, '✅ Telegram аккаунт отвязан!')
    except:
        messages.error(request, '❌ Telegram аккаунт не был привязан!')
    
    return redirect('shop:profile')