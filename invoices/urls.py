from django.urls import path
from .views import invoice_detail_view, invoice_settings_view

urlpatterns = [
    path('settings/', invoice_settings_view, name='invoice_settings'),
    path('view/<str:invoice_no>/', invoice_detail_view, name='invoice_detail'),
]