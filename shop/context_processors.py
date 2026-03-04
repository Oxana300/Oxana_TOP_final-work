from .models import Category, Tag, SupportTicket

def shop_context(request):
    '''Добавляет в контекст категории и теги'''
    return{
        'categories': Category.objects.all(),
        'tags': Tag.objects.all(),
        'cart_count': 5, # пример - количество товаров в корзине
    }

def support_context(request):
    '''Добавляет статистику обращений в контекст всех шаблонов'''
    
    context = {
        'open_ticket_count': 0,
        'resolved_tickets_count': 0,
    }
    
    if request.user.is_authenticated:
        # Количество открытых обращений (новые + в работе)
        context['open_ticket_count'] = SupportTicket.objects.filter(
            user=request.user,
            status__in=['new', 'in_progress']
        ).count()
        
        # Количество решенных обращений
        context['resolved_tickets_count'] = SupportTicket.objects.filter(
            user=request.user,
            is_resolved=True
        ).count()
    
    return context