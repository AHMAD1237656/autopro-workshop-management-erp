"""
URL configuration for autopro_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from users_app.views import user_login_view, user_logout_view
from roles.views import role_matrix_view
from dashboard.views import dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', user_login_view, name='login'),
    path('logout/', user_logout_view, name='logout'),
    path('', dashboard_view, name='dashboard_home'),
    path('dashboard/', include('dashboard.urls')),
    path('roles/matrix/', role_matrix_view, name='role_matrix'),
    path('inventory/', include('inventory.urls')),
    path('workshop/', include('workshop.urls')),
    path('sales/', include('sales.urls')),
    path('invoices/', include('invoices.urls')),
    path('showroom/', include('showroom.urls')),
    path('purchases/', include('purchases.urls')),
    path('ledger/', include('ledger.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports_app.urls')),
    path('audit-log/', include('audit_log.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
