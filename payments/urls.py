from django.urls import path
from .views import payment_list_view, payment_create_view

urlpatterns = [
    path('', payment_list_view, name='payment_list'),
    path('record/', payment_create_view, name='payment_create'),
]