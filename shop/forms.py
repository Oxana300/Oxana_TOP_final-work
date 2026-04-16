"""
Формы для приложения магазина
"""
from django import forms
from .models import Product, Category, Tag, ProductReview, SupportTicket, SupportTicketAttachment, UserProfile, Preorder
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from datetime import date

import re


class ProductReviewForm(forms.ModelForm):
    """Форма для добавления отзыва"""
    
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} ★') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Напишите ваш отзыв...'
                }
            ),
        }
        labels = {
            'rating': 'Ваша оценка',
            'comment': 'Комментарий',
        }

class ProductSearchForm(forms.Form):
    """Форма поиска товаров"""
    
    search = forms.CharField(
        required=False,
        label='Поиск',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Поиск товаров...'
            }
        )
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Категория',
        empty_label='Все категории',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    min_price = forms.DecimalField(
        required=False,
        label='Цена от',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'От'})
    )
    
    max_price = forms.DecimalField(
        required=False,
        label='Цена до',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'До'})
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('', 'Сортировать по'),
            ('price_asc', 'Цена: по возрастанию'),
            ('price_desc', 'Цена: по убыванию'),
            ('name', 'Название'),
            ('rating', 'Рейтинг'),
            ('newest', 'Новинки'),
        ],
        required=False,
        label='Сортировка',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class ProductCreateForm(forms.ModelForm):
    """Форма создания товара"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'price', 'discount_price',
            'category', 'tags', 'is_featured', 'stock_quantity'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
    def clean_price(self):
        """
            Валидация поля 'price'
        """
        price = self.cleaned_data.get('price')
            
        if price is not None:
                # Проверка 1 - Цена не может быть отрицательной
            if price < 0:
                raise ValidationError("Цена не может быть отрицательной")
            
                # Проверка 2 - Цена не может быть слишком высокой
            if price > 1000000:
                raise ValidationError("Цена слишком высокая (максимум 1,000,000)")
            
                # Проверка 3 - Цена должна быть кратной 0.01
            if price * 100 % 1 != 0:
                raise ValidationError("Цена должна быть с точностью до копеек (2 знака после запятой)")

        return price

    def clean_discount_price(self):
        """
        Расширенная валидация поля 'discount_price' (Цена со скидкой)
        """
        discount_price = self.cleaned_data.get('discount_price')
        price = self.cleaned_data.get('price') if 'price' in self.cleaned_data else None
        
        # Если поле пустое - это нормально (скидки нет)
        if discount_price is None or discount_price == '':
            return None
        
        # Проверка 1: Скидка должна быть положительным числом
        if discount_price < 0:
            raise ValidationError("Цена со скидкой не может быть отрицательной")
        
        # Проверка 2: Скидка должна быть меньше обычной цены
        if price is not None and discount_price >= price:
            raise ValidationError("Цена со скидкой должна быть меньше обычной цены")
        
        # Проверка 3: Скидка должна быть кратной 0.01
        if discount_price * 100 % 1 != 0:
            raise ValidationError("Цена должна быть с точностью до копеек (2 знака после запятой)")
        
        # Проверка 4: Минимальная сумма скидки (если цена > 100)
        if price is not None and price > 100 and discount_price > price - 10:
            raise ValidationError(
                f"Слишком маленькая скидка. Минимальная сумма скидки для товаров дороже 100 руб. - 10 руб. "
                f"(текущая скидка: {price - discount_price} руб.)"
            )
        
        # Проверка 5: Максимальная скидка (не более 90%)
        if price is not None and price > 0:
            discount_percent = (1 - discount_price / price) * 100
            if discount_percent > 90:
                raise ValidationError(
                    f"Слишком большая скидка ({discount_percent:.1f}%). "
                    f"Максимальная скидка не может превышать 90%"
                )
        
        # Проверка 6: Скидка не может быть слишком маленькой (менее 1 руб.)
        if price is not None and price - discount_price < 1 and price > 10:
            raise ValidationError(
                f"Слишком маленькая скидка ({(price - discount_price):.2f} руб.). "
                f"Минимальная скидка должна быть не менее 1 руб."
            )
        
        return discount_price
    
    def clean_name(self):
        """Валидация поля 'Название товара'"""
        name = self.cleaned_data.get('name')
        
        if name:
            if len(name) < 3:
                raise ValidationError("Название должно содержать минимум 3 символа")
            
            if len(name) > 200:
                raise ValidationError("Название слишком длинное (максимум 200 символов)")
            
            forbidden_words = ['тест', 'спам', 'заглушка', 'ошибка', 'test', 'spam']
            if any(word in name.lower() for word in forbidden_words):
                raise ValidationError("Название содержит запрещенные слова!")
        
        return name
    
    def clean(self):
        """
        Кросс-валидация всех полей
        """
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')
        stock_quantity = cleaned_data.get('stock_quantity')
        is_featured = cleaned_data.get('is_featured')
        
        # Если имеется скидка, то должна быть указана и цена
        if discount_price is not None and price is None:
            self.add_error('price', "Укажите обычную цену при наличии скидки")
        
        # Товар с количеством 0 не может быть рекомендуемым
        if is_featured and stock_quantity == 0:
            self.add_error('stock_quantity', "Рекомендуемый товар должен быть в наличии!")
        
        # Если товар в архиве, он не может быть рекомендуемым
        status = cleaned_data.get('status')
        if status == 'archived' and is_featured:
            self.add_error('is_featured', "Архивный товар не может быть рекомендуемым!")
        
        return cleaned_data
            
class ProductFilterForm(forms.Form):
    """Форма фильтрации товаров"""
    
    STATUS_CHOICES = [
        ('', 'Все статусы'),
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('archived', 'В архиве'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Статус',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    in_stock = forms.BooleanField(
        required=False,
        label='Только в наличии',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    has_discount = forms.BooleanField(
        required=False,
        label='Только со скидкой',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
class SupportTicketForm(forms.ModelForm):
    """Форма создания нового обращения"""
   
    # Дополнительное поле для потверждения email
    email_confirm = forms.EmailField(
        label="Подтвердите email",
        widget=forms.EmailInput(attrs={
                                'class':'form-control',
                                'placeholder': 'Повторите ваш email'}),
        help_text= "Введите тот же email для подтверждения"
    ) 
    
    # Согласие на обработку данных
    agree_to_terms = forms.BooleanField(
        label='Я согласен на обработку персональных данных',
        required= True,
        error_messages={ 'required': "Необходимо согласие на обработку данных"}
    )
   
    class Meta:
        model = SupportTicket
        fields = ['email', 'subject', 'category', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={
                                        'class': 'form-control',
                                        'placeholder': 'your@mail.com',
                                        'id':'id_email' # для AJAX 
                                        }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Краткая тема обращения',
                'maxlength': '200'
            }),
            'category': forms.Select(attrs={
                'class':'form-select'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Подробно опишите вашу проблему...',
                'maxlength': '5000'
            }),
            }
       
        labels = {
           'email': 'Ваш email',
           'subject': 'Тема',
           'category': 'Категория',
           'message': 'Сообщение',
       }
       
    def clean_email_confirm(self):
        """Проверка совпадения email"""
        email = self.cleaned_data.get('email')
        email_confirm = self.cleaned_data.get('email_confirm')
            
        if email and email_confirm and email != email_confirm:
            raise ValidationError("Email адреса не совпадают!")
        return email_confirm
        
    def clean_subject(self):
        """Валидация темы обращения"""
        subject = self.cleaned_data.get('subject')

        if not subject:
            raise ValidationError("Укажите тему обращения")
            
        # минимальная длина
        if len(subject) < 5:
            raise ValidationError("Тема должна содержать минимум 5 символов")
            
        # Максимальная длина
        if len(subject) > 200:
            raise ValidationError("Тема слишком длинная (максимум 200 символов)")
        
        # Проверка на запрещенные слова
        forbidden_words = ['спам', 'тест', 'фигня', 'бред', 'test', 'spam']
        if any(word in subject.lower() for word in forbidden_words):
            raise ValidationError("Тема содержит недопусчтимые слова!")
                   
        # Проверка на повторяющиеся символы
        if len(set(subject)) < len(subject) * 0.3:
            raise ValidationError("Тема содержит слишком много повторяющихся символов")

        return subject

    def clean_message(self):
        """Валидация сообщения"""
        message = self.cleaned_data.get('message')
        
        if not message:
            raise ValidationError("Напишите сообщение")
        
        # Минимальная длина
        if len(message) < 20:
            raise ValidationError("Сообщение должно содержать минимум 20 символов")
        
        # Максимальная длина
        if len(message) > 5000:
            raise ValidationError("Сообщение слишком длинное (максимум 5000 символов)")
        
        # Проверка на повторяющиеся символы (защита от спама)
        if len(set(message)) < len(message) * 0.2:
            raise ValidationError("Сообщение содержит слишком много повторяющихся символов")
        
        # Проверка на URL (защита от спама)
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        if url_pattern.search(message):
            raise ValidationError("Сообщение не должно содержать ссылки")
        
        return message
        
    def clean_email(self):
        """Проверка email на существование в базе"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError("Укажите email для связи")
        
        # Проверка формата email
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            raise ValidationError("Введите корректный email адрес")
        
        # Проверка на временные email-домены
        temp_domains = ['tempmail.com', '10minute.com', 'throwaway.com']
        domain = email.split('@')[1].lower()
        if domain in temp_domains:
            raise ValidationError("Временные email адреса не разрешены")
        
        return email

class SupportTicketAttachmentForm(forms.ModelForm):
    class Meta:
        model = SupportTicketAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={
                'class':'form-control',
                'placeholder': 'Описание файла(необязательно)'
            }),
        }       
    
    def clean_file(self):
        """Проверка размера и типа файлов"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Проверка наличия файла, только потом начинаем проверку
            # Максимальный размер не более 5 Мб
            
            if file.size > 5 * 1024 * 1024:
                raise ValidationError("Размер файла должен быть не более 5 Мб!")
            
            # Разрешенные расширения
            allowed_extencions = ['.jpg', '.png', '.jpeg', '.gif', '.doc', '.docx']
            ext = file.name.split('.')[-1].lower()
            if f'.{ext}' not in allowed_extencions:
                raise ValidationError(f'Недопустимый формат файла. Разрешены: {', '.join(allowed_extencions)}')
        
        return file
    
class SupportTicketUpdateForm(forms.ModelForm):
    """Форма редактирования обращения (для владельца)"""
    
    class Meta:
        model = SupportTicket
        fields = ['subject', 'message']
        widgets ={
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.TextInput(attrs={'class': 'form-control', 'rows': 6}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Нельзя редактировать, если обращение уже решено
        if self.instance and self.instance.is_resolved:
            for field in self.fields:
                self.fields[field].disabled = True
                self.fields[field].help_text = "Редактирование невозможно, так как обращение решено"
    
    def clean(self):
        cleaned_data = super().clean()
        if self.instance and self.instance.is_resolved:
            raise ValidationError("Нельзя редактировать решенное обращение")
        return cleaned_data
                
class SupportResponseForm(forms.ModelForm):
    """Форма ответа администрации"""
    
    send_notification = forms.BooleanField(
        label = 'Отправить уведомление на email',
        required=False,
        initial=True,
        help_text='Пользователь получит письмо с ответом'
    )
    
    class Meta:
        model = SupportTicket
        fields = ['status', 'priority', 'response', 'is_resolved', 'is_public']
        widgets = {
            'status': forms.Select(attrs={'class':'form-select'}), 
            'priority': forms.Select(attrs={'class':'form-select'}), 
            'response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Напишите ваш ответ...'}), 
            'is_resolved': forms.CheckboxInput(attrs={'class':'form-check-input'}), 
            'is_public': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }
    
    def clean_response(self):
        response = self.cleaned_data.get('response')
        
        if not response:
            raise ValidationError("Напишите ответ на обращение")
        
        if len(response) < 10:
            raise ValidationError("Ответ должен содержать минимум 10 символов")
        
        return response
        
class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя с расширенной валидацией"""
    
    email = forms.EmailField(
        required=True,
        label='Электронная почта',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше имя'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вашу фамилию'
        })
    )

    # Заменяем поле age на birth_date для более точной валидации
    birth_date = forms.DateField(
        required=True,
        label='Дата рождения',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': date.today().isoformat()
        })
    )

    phone = forms.CharField(
        max_length=15,
        required=False,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 999-99-99'
        })
    )
    
    age = forms.IntegerField(
        required=True,
        label='Возраст',
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '18'
        })
    )
    
    agree_to_terms = forms.BooleanField(
        required=True,
        label='Я согласен на обработку персональных данных',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'birth_date', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
         # Настройка полей username и паролей
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Придумайте имя пользователя'
        })
        self.fields['username'].help_text = 'Обязательно. Не более 150 символов. Только буквы, цифры и @/./+/-/_'
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Придумайте пароль'
        })
        self.fields['password1'].help_text = '''
            Пароль должен содержать минимум 8 символов,
            не быть слишком простым и не состоять только из цифр
        '''
        
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    
    def clean_username(self):
        """Валидация имени пользователя"""
        username = self.cleaned_data.get('username')
        
        # Проверка на длину
        if len(username) < 3:
            raise ValidationError("Имя пользователя должно содержать минимум 3 символа")
        
        # Проверка на запрещенные символы
        if not re.match(r'^[a-zA-Z0-9_@+-]+$', username):
            raise ValidationError(
                "Имя пользователя может содержать только буквы, цифры и символы: @/./+/-/_"
            )
        
        # Проверка на существование
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Пользователь с таким именем уже существует")
        
        return username

    def clean_first_name(self):
        """Валидация имени - только буквы"""
        first_name = self.cleaned_data.get('first_name')
        
        if first_name:
            # Проверка, что поле не пустое
            if len(first_name.strip()) == 0:
                raise ValidationError("Имя не может быть пустым")
            
            # Проверка на минимальную длину
            if len(first_name) < 2:
                raise ValidationError("Имя должно содержать минимум 2 символа")
            
            # Проверка на наличие цифр
            if any(char.isdigit() for char in first_name):
                raise ValidationError("Имя не должно содержать цифры")
            
            # Проверка на спецсимволы
            if not first_name.replace('-', '').replace(' ', '').isalpha():
                raise ValidationError("Имя может содержать только буквы, пробелы и дефисы")
            
            # Приводим к правильному формату
            first_name = first_name.strip()
            first_name = ' '.join(word.capitalize() for word in first_name.split())
            
        return first_name
    
    def clean_last_name(self):
        """Валидация фамилии - только буквы"""
        last_name = self.cleaned_data.get('last_name')
        
        if last_name:
            # Проверка, что поле не пустое
            if len(last_name.strip()) == 0:
                raise ValidationError("Фамилия не может быть пустой")
            
            # Проверка на минимальную длину
            if len(last_name) < 2:
                raise ValidationError("Фамилия должна содержать минимум 2 символа")
            
            # Проверка на наличие цифр
            if any(char.isdigit() for char in last_name):
                raise ValidationError("Фамилия не должна содержать цифры")
            
            # Проверка на спецсимволы
            if not last_name.replace('-', '').replace(' ', '').isalpha():
                raise ValidationError("Фамилия может содержать только буквы, пробелы и дефисы")
            
            # Приводим к правильному формату
            last_name = last_name.strip()
            last_name = ' '.join(word.capitalize() for word in last_name.split())
            
        return last_name

    def clean_email(self):
        """Валидация email"""
        email = self.cleaned_data.get('email')
        
        # Проверка на существование
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован")
        
        # Проверка домена email
        allowed_domains = ['mail.ru', 'gmail.com', 'yandex.ru', 'bk.ru', 'list.ru']
        domain = email.split('@')[-1].lower()
        
        if domain not in allowed_domains:
            raise ValidationError(
                f"Домен {domain} не разрешен. Разрешены: {', '.join(allowed_domains)}"
            )
        
        return email
    
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Очищаем номер от лишних символов
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            
            # Проверка формата
            if not re.match(r'^\+?\d{10,15}$', cleaned_phone):
                raise ValidationError(
                    "Введите корректный номер телефона (10-15 цифр, может начинаться с +)"
                )
            
            return cleaned_phone
        return phone
    
    def clean_birth_date(self):
        """Валидация даты рождения при регистрации"""
        birth_date = self.cleaned_data.get('birth_date')
        
        if birth_date:
            today = date.today()
            
            # Проверка на будущую дату
            if birth_date > today:
                raise ValidationError("Дата рождения не может быть в будущем")
            
            # Расчет возраста
            age = today.year - birth_date.year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
            
            # Проверка на совершеннолетие
            if age < 18:
                raise ValidationError(
                    f"Регистрация разрешена только пользователям старше 18 лет. "
                    f"Ваш возраст: {age} лет."
                )
            
            # Проверка на слишком старый возраст
            if age > 120:
                raise ValidationError("Указан некорректный возраст")
            
        return birth_date
    
    def clean_password1(self):
        """Валидация пароля"""
        password = self.cleaned_data.get('password1')
        
        # Проверка на простые пароли
        common_passwords = ['12345678', 'qwerty123', 'password123', '11111111']
        if password in common_passwords:
            raise ValidationError("Пароль слишком простой")
        
        # Проверка на наличие цифр и букв
        if not any(char.isdigit() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру")
        
        if not any(char.isalpha() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну букву")
        
        return password
    
    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Проверка совпадения паролей
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Пароли не совпадают")
        
        # Проверка, что пароль не содержит username
        username = cleaned_data.get('username')
        if username and password1 and username.lower() in password1.lower():
            self.add_error('password1', "Пароль не должен содержать имя пользователя")
        
        return cleaned_data
    

class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'birth_date', 'default_address', 'bio', 'email_notifications']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().isoformat()  # Максимальная дата - сегодня
            }),
            'default_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите ваш адрес'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'phone': 'Телефон',
            'birth_date': 'Дата рождения',
            'default_address': 'Адрес доставки',
            'bio': 'О себе',
            'email_notifications': 'Получать уведомления на email',
        }
    
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Очищаем номер от лишних символов
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            
            # Проверка формата
            if not re.match(r'^\+?\d{10,15}$', cleaned_phone):
                raise ValidationError(
                    "Введите корректный номер телефона (10-15 цифр, может начинаться с +)"
                )
            
            return cleaned_phone
        return phone
    def clean_birth_date(self):
        """Валидация даты рождения"""
        birth_date = self.cleaned_data.get('birth_date')
        
        if birth_date:
            today = date.today()
            
            # Проверка 1: Дата рождения не может быть в будущем
            if birth_date > today:
                raise ValidationError("Дата рождения не может быть в будущем")
            
            # Проверка 2: Дата рождения не может быть слишком старой (например, > 120 лет)
            max_age = 120
            min_birth_date = date(today.year - max_age, today.month, today.day)
            if birth_date < min_birth_date:
                raise ValidationError(f"Указана слишком старая дата (максимальный возраст: {max_age} лет)")
            
            # Проверка 3: Проверка на совершеннолетие (18 лет)
            age = today.year - birth_date.year
            # Корректировка возраста, если день рождения еще не наступил в этом году
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
            
            if age < 18:
                raise ValidationError(
                    f"Вам должно быть не менее 18 лет. Ваш возраст: {age} лет. "
                    f"Регистрация разрешена только совершеннолетним пользователям."
                )
            
            # Проверка 4: Дата рождения должна быть реалистичной (не сегодня и не вчера для взрослых)
            if age == 18 and birth_date > date(today.year - 18, today.month, today.day):
                # Проверка, что действительно исполнилось 18 лет
                birthday_18 = date(birth_date.year + 18, birth_date.month, birth_date.day)
                if birthday_18 > today:
                    raise ValidationError("Вам еще нет 18 лет. Регистрация доступна с 18 лет.")
            
            # Проверка 5: Нельзя установить дату рождения на 1 января 1970 года (часто значение по умолчанию)
            if birth_date == date(1970, 1, 1):
                raise ValidationError("Пожалуйста, укажите реальную дату рождения")
            
        return birth_date

class UserAvatarForm(forms.ModelForm):
    """Форма для загрузки аватара"""
    
    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/gif'
            })
        }
        labels = {
            'avatar': 'Фотография профиля'
        }
    
    def clean_avatar(self):
        """Валидация загружаемого изображения"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Проверка размера файла (макс 2 МБ)
            if avatar.size > 2 * 1024 * 1024:
                raise ValidationError("Размер файла не должен превышать 2 МБ")
            
            # Проверка типа файла
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if avatar.content_type not in allowed_types:
                raise ValidationError("Допустимые форматы: JPG, PNG, GIF")
        
        return avatar


class UserInfoForm(forms.ModelForm):
    """Форма редактирования основной информации пользователя"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@mail.com'
            }),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }
    
    def clean_first_name(self):
        """Валидация имени - только буквы"""
        first_name = self.cleaned_data.get('first_name')
        
        if first_name:
            # Проверка, что поле не пустое
            if len(first_name.strip()) == 0:
                raise ValidationError("Имя не может быть пустым")
            
            # Проверка на минимальную длину
            if len(first_name) < 2:
                raise ValidationError("Имя должно содержать минимум 2 символа")
            
            # Проверка на максимальную длину
            if len(first_name) > 30:
                raise ValidationError("Имя слишком длинное (максимум 30 символов)")
            
            # Проверка, что имя содержит только буквы
            if not first_name.replace('-', '').replace(' ', '').isalpha():
                raise ValidationError("Имя может содержать только буквы, пробелы и дефисы")
            
            # Проверка на наличие цифр
            if any(char.isdigit() for char in first_name):
                raise ValidationError("Имя не должно содержать цифры")
            
            # Проверка на спецсимволы (кроме дефиса)
            allowed_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ- ')
            if not all(char in allowed_chars for char in first_name):
                raise ValidationError("Имя содержит недопустимые символы")
            
            # Приводим к правильному формату (первая буква заглавная, остальные строчные)
            first_name = first_name.strip()
            first_name = ' '.join(word.capitalize() for word in first_name.split())
            
        return first_name
    
    def clean_last_name(self):
        """Валидация фамилии - только буквы"""
        last_name = self.cleaned_data.get('last_name')
        
        if last_name:
            # Проверка, что поле не пустое
            if len(last_name.strip()) == 0:
                raise ValidationError("Фамилия не может быть пустой")
            
            # Проверка на минимальную длину
            if len(last_name) < 2:
                raise ValidationError("Фамилия должна содержать минимум 2 символа")
            
            # Проверка на максимальную длину
            if len(last_name) > 50:
                raise ValidationError("Фамилия слишком длинная (максимум 50 символов)")
            
            # Проверка, что фамилия содержит только буквы
            if not last_name.replace('-', '').replace(' ', '').isalpha():
                raise ValidationError("Фамилия может содержать только буквы, пробелы и дефисы")
            
            # Проверка на наличие цифр
            if any(char.isdigit() for char in last_name):
                raise ValidationError("Фамилия не должна содержать цифры")
            
            # Проверка на спецсимволы (кроме дефиса)
            allowed_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ- ')
            if not all(char in allowed_chars for char in last_name):
                raise ValidationError("Фамилия содержит недопустимые символы")
            
            # Приводим к правильному формату (первая буква заглавная, остальные строчные)
            last_name = last_name.strip()
            last_name = ' '.join(word.capitalize() for word in last_name.split())
            
        return last_name
    
    def clean_email(self):
        """Валидация email"""
        email = self.cleaned_data.get('email')
        
        # Проверка, не занят ли email другим пользователем
        if email and self.instance.email != email:
            if User.objects.filter(email=email).exists():
                raise ValidationError("Этот email уже используется другим пользователем")
        
        return email
    
# Предзаказ с указанием дней до исполнения
class PreorderForm(forms.ModelForm):
    class Meta:
        model = Preorder
        fields = ['customer_name', 'email', 'phone', 'quantity', 'days_to_delivery', 'comment']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваше имя'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'days_to_delivery': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Дополнительные пожелания'}),
        }