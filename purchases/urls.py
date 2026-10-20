from django.urls import path
from .views import purchase_order_list_view, purchase_order_create_view

urlpatterns = [
    path('', purchase_order_list_view, name='purchase_list'),
    path('create/', purchase_order_create_view, name='purchase_create'),
]