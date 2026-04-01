'''
Представления для системы аутентификации

-Обработка запросов на регистрацию
-Обработка вход/ выход
-Показ личного кабинета
-Редактирование профиля
'''

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.contrib.auth.models import User
from django.db.models import Count
from .forms_auth import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    CustomPasswordChangeForm
)

#=======================================
# РЕГИСТРАЦИЯ
#=======================================

def register_view(request):
    '''
    Представление страницы регистрации
    Обработка GET и POST запросов:
    - GET показывает пустую форму регистрации
    - POST обрабатывает отправку формы и создает пользователя

    Args:
        request (HTTP запрос от браузера)
    Returns:
        HttpResponse: рендерит шаблон register.html или перенаправляет
    '''
    # Проверка 1 - пользователь уже авторизован
    if request.user.is_authenticated:
        # Перенаправляем на главную страницу
        return redirect('shop:home')
    # Проверка 2 - Определяем тип запроса
    if request.method == 'POST':
        # POST запрос означает, что пользователь отправил форму
        # Создаем экземпляр формы с данными из request.POST
        # request.POST - словарь со всеми данными из формы
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Сохранение: СОздается новый пользователь в БД
            # commit = False означает "не сохранять сразу в БД"
            # Это нужно для того, чтобы мы могли дополнительно настроить или проверить пользователя
            user = form.save(commit=False)
            # Устанавливаем активный статус
            user.is_active = True
            # Теперь сохраняем в БД
            user.save()
            # Автоматический вход- после регистрации пользователь сразу входить
            # login() создает сессию для пользователя
            login(request, user)

            messages.success(
                request,
                f'Добро пожаловать, {user.first_name}!'
                f'Ваш аккаунт успешно создан'
            )

            # Перенаправление на главную страницу
            return redirect('shop:home')
        else:
            # Ошибка при проверке формы на валидацию
            messages.error(
                request,
                "Пожалуйста, исправьте ошибки в форме ниже"
            )
    else:
        # Это GET = Пустая форма. Создаем новую пустую форму без данных
        form = UserRegistrationForm()

    # Рендеринг: Показываем шаблон с формой
    # context - словарь переменных, доступных в шаблоне

    return render(request, 'shop/register.html',{
        'form': form, # Форма (пустая или с ошибками)
        'title': 'Регистрация', # Заголовок страницы
        'page-type': 'auth' # Тип страницы (для стилей)
    })

#====================================================
# ВХОД (ЛОГИН)
#====================================================

def login_view(request):
    '''
    Представление страницы входа
    Обработка аутентификации пользователя по логину/паролю
    '''
    # Проверка- если пользватель уже авторизован - не показываем форму входа
    if request.user.is_authenticated:
        messages.info(request, 'Вы уже вошли в систему.')
        return redirect('shop:home')
    
    if request.method == 'POST':
        # Если POST-запрос - пользователь отправил форму входа
        # создаем форму с данными
        form = UserLoginForm(request, data = request.POST)
        # Проверка на валидацию
        if form.is_valid():
            # Аутентификация: получаем объект пользователя
            user = form.get_user()
            #Вход в систему: создание сессии
            # После этого request.user.is_authenticated АВТОМАТИЧЕСКИ будет True
            login(request,user)

            messages.success(
                request,
                f'С возвращением, {user.first_name}!'
            )

            # Перенаправление:
            # next_url - откуда пришел пользователь (защищенная страница)
            # Если next_url есть- идем туда, иначе - на главную
            next_url = request.GET.get('next', 'shop:home')
            return redirect(next_url)
        else:
            # Неверный логин или пароль
            messages.error(
                request,
                'Неверный логин или пароль. Попробуйте еще раз'
            )
    else:
        # GET-запрос. Показываем пустую форму
        form = UserLoginForm()
    # Рендеринг шаблона
    return render(request, 'shop/login.html', {
        'form': form,
        'title': 'Вход в аккаунт',
        'page_type': "auth"
    })

#============================================
# ВЫХОД (ЛОГАУТ)
#============================================

@login_required
def logout_view(request):
    """
    Представление выхода из аккаунта
    
    @login_required - декоратор, требующий авторизации
    Если пользователь не авторизован, его перенаправит на LOGIN_URL
    """

    # Получаем имя пользователя для сообщения
    user_name = request.user.first_name or request.user.username
    # Выход - Удаляем сессию пользователя
    # После этого request.user.is_authenticated будет False
    logout(request)

    messages.info(
        request,
        f'Вы вышли из аккаунта, {user_name}. До встречи!'
    )

    return redirect('shop:home')

#============================================
# Личный кабинет
#============================================
@login_required
def profile_view(request):
    '''
    Представление личного кабинета

    - Основная информация о пользователе
    - История заказов (если есть)
    - Статистика активности
    '''
    # Получаем текущего пользователя
    # request.user - Объект User, который добавил middleware аутентификации
    user = request.user

    # Статистика: считаем различные показатели
    from shop.models import ProductReview, SupportTicket
    # Количество отзывов пользователя
    reviews_count = ProductReview.objects.filter(user=user).count()
    # Количество обращений в поддержку
    ticket_count = SupportTicket.objects.filter(
        user=user,
        email=user.email
    ).count() if hasattr(SupportTicket, 'objects') else 0
    # Дата регистрации (первый вход в систему)
    data_joined = user.date_joined.strftime('%d.%m.%Y')
    # Последняя активность
    last_login = user.last_login.strftime('%d.%m.%Y %H:%M') if user.last_login else 'Не входил'
    # Контекст - данные для передачи в шаблон
    context = {
        'user': user,
        'title': 'Личный кабинет',
        'reviews_count': reviews_count,
        'ticket_count': ticket_count,
        'data_joined': data_joined,
        'last_login': last_login,
        'page_type': 'profile'
    }

    # Рендеринг шаблона
    return render (request, 'shop/profile.html', context)

#============================================
# Редактирование профиля
#============================================
@login_required
def profile_edit_view(request):
    '''
    представление редактирования профиля
    Позволяет изменить Имя, фамилию, email
    '''
    user = request.user

    if request.method =='POST':
        # instance - связывание формы с конкретным пользователем
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.succes(
                request,
                'Ваш профиль успешно обновлен!'
            )
            return redirect('shop:profile')
        else:
            messages.error(
                request,
                'Исправьте ошибки в форме'
            )
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'shop/profile_edit.html',{
        'form': form,
        'title': "Редактирование профиля",
        'page_type': 'profile'
    })

#============================================
# Смена профиля
#============================================
@login_required
def password_change_view(request):
    if request.method =='POST':
        form = CustomPasswordChangeForm(user = request.user, data = request.POST)
        if form.is_valid():
            user = form.save()
            # Важно- обновление хэш сессии
            # если не обновит хэш- пользователя выбросит из системы
            update_session_auth_hash(request,user)
            messages.success(
                request,
                'Пароль успешно обновлен'
            )
            return redirect('shop:profile')
        else:
            messages.error(
                request,
                'Исправьте ошибки в профиле'
            )
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'shop/password_change.html', {
        'form':form,
        'title':'Смена пароля',
        'page_type': 'profile'
    })

class CustomLoginView(LoginView):
    """
    Кастомизированная страница входа
    LoginView уже умеет:
    - Показывать форму
    - Аутентифицировать пользователя
    - Создавать сессию
    - Перенаправлять после входа
    """

    # Форма входа
    authentication_form = UserLoginForm
    # шаблон
    template_name = 'shop/login.html'
    # Куда перенаправлять после входа
    next_page = reverse_lazy('shop:home')
    # Если пользователь уже авторизован - перенаправляем
    redirect_authenticated_user = True
    
    def get_success_url(self):
        '''
        Определяет URL для перенаправления после входа
        '''
        # Проверяем, есть ли параметр 'next' (?next=) в запросе
        url = self.request.GET.get('next')

        if url:
            # Безопасная проверка URL (защита от скрытых редиректов)
            from django.utils.http import url_has_allowed_host_and_scheme
            if url_has_allowed_host_and_scheme(url,allowed_hosts={self.request.get_host()}):
                return url
            
        # Если next в запросе не обнаружен - используем next_page
        return self.next_page
    
    def form_valid(self, form):
        '''Обработка успешного входа'''

        response = super().form_valid(form)
        #Получаем пользователя
        user = form.get_user()
        # Добавляем сообщение
        from django.contrib import messages
        messages.success(
            self.request,
            f'С возвращением {user.first_name or user.username}!'
        )
        # Логируем вход
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'User {user.username} logged in from IP {self.request.META.get("REMOTE_ADDR")}')
        return response
