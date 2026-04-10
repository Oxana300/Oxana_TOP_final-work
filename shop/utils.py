# shop/utils.py
import re
from django.utils.html import strip_tags, escape

def sanitize_text(text, max_length=1000, allow_html=False):
    """
    Очищает текст от опасных символов и XSS-атак
    
    Args:
        text: Входной текст
        max_length: Максимальная длина текста
        allow_html: Разрешить ли HTML (по умолчанию False)
    
    Returns:
        Очищенный безопасный текст
    """
    if not text:
        return ""
    
    # Если HTML запрещен, удаляем теги
    if not allow_html:
        text = strip_tags(text)
    
    # Всегда экранируем специальные символы
    text = escape(text)
    
    # Дополнительная очистка от потенциально опасных символов
    # Оставляем буквы, цифры, пробелы и базовую пунктуацию
    text = re.sub(r'[^\w\s\-\.,!?@\(\)\[\]\{\}\"\'`]', '', text)
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length] + '...'
    
    return text.strip()

def sanitize_email_content(subject, message):
    """
    Очищает тему и сообщение email от XSS-атак
    """
    return {
        'subject': sanitize_text(subject, 200),
        'message': sanitize_text(message, 2000)
    }
