"""
URL configuration for sales_distribution project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from dashboard.views import LowStockLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
    path('accounts/login/', LowStockLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('dashboard.urls')),
    path('customers/', include('customers.urls')),
    path('orders/', include('orders.urls')),
    path('returns/', include('returns.urls', namespace='returns')),
    path('products/', include('core.urls')),
    path('reports/', include('reports.urls')),
    path('purchasing/', include('purchasing.urls')),
    path('accounting/', include('accounting.urls')),
    path('crm/', include('crm.urls')),
    path('settings/', include('master_data.urls')),
    
    # API
    path('api/master/', include('master_data.api_urls')),
    path('api/', include('core.api_urls')),
    path('api/', include('customers.api_urls')),
    path('api/', include('orders.api_urls')),
    path('api/', include('crm.api_urls')),
    path('api/', include('purchasing.api_urls')),
    path('api/', include('returns.api_urls')),
    path('api/', include('accounting.api_urls')),
    path('api/common/', include('common.api_urls')),
    path('system/', include('common.urls')),
    path('api/reports/', include('reports.api_urls')),
    path('api-auth/', include('rest_framework.urls')),
    
    # Swagger / OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

