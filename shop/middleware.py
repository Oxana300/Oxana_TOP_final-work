import logging
import time
from django.utils.deprecation import MiddlewareMixin
# создаем логер
logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware для логирования всех запросов

    Записывать в лог:
    - Метод запроса (POST, GET...)
    - URL
    - Время выполнения
    - IP адрес пользователя
    - Статус ответа
    """
    def process_request(self,request):
        """
        Вызывается до view

        Вход - запрос HttpRequest объект
        Выход - None или HttpResponse
        """
        request._start_time = time.time()
        
        logger.info(
            f'"RQUEST": {request.method} {request.path}'
            f'"From IP: {self.get_client_ip(request)}'
        )
        # Возвращаем None - обработка продолжается
        return None
    
    def process_response(self, request, response):
        """
        Вызывается После view
        """
        # Вычисляем время выполнения
        if hasattr(request,'_start_time'):
            elapsed = time.time() - request._start_time
        else:
            elapsed = 0

        # логируем информацию об ответе
        logger.info(
            f'RESPONSE: {response.status_code}'
            f'in {elapsed:.3f}s'
            f'for {request.method} {request.path}'
        )

        # Добавляем заголовок со временем (для отладки)
        response['X-Response-Time'] = f'{elapsed:.3f}s'
        return response
    
    def process_ecxeption(self,request,exception):
        """
        Вызывается, если view выбросил исключение
        """
        logger.error(
            f'EXCEPTION in {request.method}, {request.path}: {exception}',
            exc_info= True # Включает traceback в лог
        )
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Первый IP в списке - оригинальный клиент
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        return ip