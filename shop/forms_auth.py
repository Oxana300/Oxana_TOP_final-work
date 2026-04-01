"""
Формы для систем аутентификации пользователей

-Регистрация нового пользователя
-Вход в аккаунт
-Реддактирование профиля
-Смена пароля
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

#===================================
# ФОРМА РЕГИСТРАЦИИ
#===================================

class UserRegistrationForm(UserCreationForm):
    """
    Форма регистрации нового пользователя

    Наследуется от UserCreation- стандартная форма django
    стандартно содержит поля username, password1, password2
    """
    email = forms.EmailField(
        required=True,
        label='Email адрес',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com',
            'autocomplete': 'email' # автозаполнение браузером
        }),
        help_text= 'На этот email придут уведомления о заказах'
    )

    # поле имени
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иван',
            'autocomplete': 'given-name'
        })
    )

    # поле фамилии
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label= 'Фамилия',
        widget = forms.TextInput(attrs={
            'class':'form-control',
            'placeholder': 'Иванов',
            'autocomplete': 'family-name'
        })
    )

    class Meta:
        model = User
        fields =[
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Логин (латиницей, без пробелов и спец символов)',
                'autocomplete': 'username',
                'pattern': '[a-zA-Z0-9_]+', # Только латиница, цифры и подчеркивание
                'title': 'Только латинские буквы, цифры и подчеркивание'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Придумайте пароль',
                'autocomplete': 'new-password',
                'minlength': '8'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Подтвердите пароль',
                'autocomplete': 'new-password'
            }),
        }

    def clean_email(self):
        '''
        Валидация поля email
        Проверяет уникальность email в БД

        Returns:
            str: Очищенное значение email
        
        Raises:
            ValidationError: Если email уже зарегистрирован
        '''

        email = self.cleaned_data.get('email') # email из формы

        # Проверяем есть ли пользователь с таким email в БД
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "Этот email уже зарегистрирован!"
                "Попробуйте войти или используйте другой email."
            )
        return email
    
    def clean_username(self):
        """
        Валидация поля username
        Проверяет уникальность username пользователя
        """
        username = self.changed_data.get('username')

        if User.objects.filter(username=username).exists():
            raise ValidationError(
                "Это имя пользователя уже занято!"
                "Попробуйте другое."
            )
        return username
    
    def clean_password2(self):
        """
        Валидация подтверждения пароля
        Проверка совпадения паролей
        """
        password1= self.cleaned_data.get('password1')
        password2= self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")
        
        return password2
    
#=================================================
# ФОРМА ВХОДА
#=================================================

class UserLoginForm(AuthenticationForm):
    """
    Форма входа пользователя
    """
    # Переопределение виджета для поля username
    username = forms.CharField(
        label='Логин или Email',
        widget= forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите логин или email',
            'autocomplete': 'username',
            'autofocus': True
        })
    )

    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль',
            'autocomplete': 'current-password'
        })
    )

    def clean_username(self):
        '''
        Позволяет входить как по email так и по username
        '''
        username = self.cleaned_data.get('username')

        # Если введенное значение содержит '@' - это может быть email
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username
    
#=========================================
# ФОРМА ПРОФИЛЯ
#=========================================

class UserProfileForm(forms.ModelForm):
    '''
    Форма редактирования профиля
    Позволяет менять основные данные БЕЗ смены пароля
    '''

    email = forms.EmailField(
        label = 'Email',
        widget=forms.EmailInput(attrs={
            'class':'form-control',
            'placeholder': 'your@email.com'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class':'form-control',
                'placeholder':'Имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder':'фамилия'
            }),
        }
    
    def clean_email(self):
        """
        Проверяет уникальность email при редактировании

        Эта валидация не возвращает ошибку, если email принадлежит текущему пользователю
        """
        email = self.cleaned_data.get('email')

        current_user = self.instance

        if User.objects.filter(email=email).exclude(pk=current_user.pk).exists():
            raise ValidationError("Этот email уже используется другим пользователем!")
        
        return email
    

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Кастомизированная форма смены пароля
    """
    old_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder':'Введите текущий пароль',
            'autocomplete':'current-password'
        })
    )

    new_password1= forms.CharField(
        label = 'Новый пароль',
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder': 'Введите новый пароль',
            'autocomplete': 'new-password'
        })
    )

    new_password2 = forms.CharField(
        label = 'Подтверждение нового пароля',
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder': 'Подтвердите новый пароль',
            'autocomplete': 'new-password'
        })
    )