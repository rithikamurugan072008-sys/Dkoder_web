from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from core.views import index_view

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/', include('core.urls')),
    re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'assets'}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'assets'}),
    path('', index_view, name='home'),
]
