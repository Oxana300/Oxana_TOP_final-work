"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
#from . import views

from django.contrib.auth.models import User
from django.http import HttpResponse

def create_admin(request):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        return HttpResponse("✅ Admin created! Login: admin, Password: admin123")
    return HttpResponse("Admin already exists")



#=============все удалить сверху после создания суперпользователя=====

urlpatterns = [
    path('create-admin/', create_admin),  # ВРЕМЕННО!УДАЛИТЬ
    path('admin/', admin.site.urls),
    #path('products/', views.product_list, name='product_list'),
    path('', include('shop.urls', namespace='shop')),
    path('accounts/', include('django.contrib.auth.urls')),
]

# ОКСАНА Добавляем обработку медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
