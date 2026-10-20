from django.urls import path
from .views import vehicle_list_view, vehicle_create_view

urlpatterns = [
    path('', vehicle_list_view, name='vehicle_list'),
    path('add/', vehicle_create_view, name='vehicle_create'),
]