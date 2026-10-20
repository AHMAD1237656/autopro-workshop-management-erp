from django.urls import path
from .views import part_list_view, part_create_view

urlpatterns = [
    path('parts/', part_list_view, name='part_list'),
    path('parts/add/', part_create_view, name='part_create'),
]